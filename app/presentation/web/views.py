from dataclasses import dataclass
from typing import Any
from app.presentation.web.dependencies import build_schedule_service, build_substitution_service

from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import ProtectedError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView, View

from app.domain.exceptions import (
    CrossSchoolLessonError,
    InvalidLessonPlacementError,
    ScheduleConflictError,
    SchoolAuthorizationError,
)
from app.domain.models import Day, Lesson as DomainLesson
from app.infrastructure.database.models import (
    AcademicYear,
    Lesson,
    Period,
    Room,
    StudentGroup,
    Subject,
    Teacher,
)
from app.presentation.web.forms import (
    LessonForm,
    RoomForm,
    StudentGroupForm,
    SubjectForm,
    TeacherForm,
    AcademicYearForm,
    PeriodForm,
    TeacherSubstitutionForm,
)
from app.presentation.web.schedule_renderers import (
    FocusedTimetableRenderer,
    WholeSchoolTimetableRenderer,
)
from app.presentation.web.school_access import (
    CurrentSchoolService,
    SchoolAccessRequiredMixin,
)


class SchoolScopedQuerysetMixin:
    """Restricts a generic view's queryset to rows belonging to
    `self.current_school` (set by SchoolAccessRequiredMixin).

    Used by SchedulerListView (so list pages only show the current
    school's rows) and by SchedulerUpdateView/SchedulerDeleteView,
    where it doubles as IDOR protection: Django's SingleObjectMixin
    builds get_object() from get_queryset(), so a pk belonging to
    another school simply isn't in the queryset and 404s instead of
    being returned or edited.

    `school_filter_lookup` is the ORM lookup path from the model to
    School — "school" for models with a direct FK, or a dotted lookup
    such as "academic_year__school" for models that own a School only
    indirectly.
    """

    school_filter_lookup: str = "school"

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(**{self.school_filter_lookup: self.current_school})


class ProtectedDeleteMixin:
    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except ProtectedError:
            form.add_error(None, "This item is used by a lesson and cannot be deleted.")
            return self.form_invalid(form)

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        try:
            return super().post(request, *args, **kwargs)
        except ProtectedError:
            return redirect(self.get_success_url())


class SchedulerListView(SchoolScopedQuerysetMixin, SchoolAccessRequiredMixin, ListView):
    template_name = "scheduler/object_list.html"
    context_object_name = "objects"

    title = ""
    create_url_name = ""
    edit_url_name = ""
    delete_url_name = ""
    columns: list[tuple[str, str]] = []

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": self.title,
                "create_url_name": self.create_url_name,
                "edit_url_name": self.edit_url_name,
                "delete_url_name": self.delete_url_name,
                "columns": self.columns,
            }
        )
        return context


class SchedulerCreateView(SchoolAccessRequiredMixin, SuccessMessageMixin, CreateView):
    template_name = "scheduler/object_form.html"
    success_message = "Created successfully."
    title = ""
    list_url_name = ""

    # Set to True on subclasses whose model has a direct `school` FK.
    # `school` is never a form field for these models (it must not be
    # client-choosable) — the view assigns it instead.
    assign_current_school = False

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        # Forms that accept a `school` kwarg (Period, Lesson) use it to
        # scope their ModelChoiceFields to the current school; forms
        # that don't need it (Teacher, Room, ...) simply ignore it.
        kwargs["school"] = self.current_school
        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.assign_current_school:
            # Assigned in get_form() rather than form_valid(): the
            # per-school UniqueConstraint(school, name) is checked by
            # ModelForm.validate_unique() during form.is_valid(), which
            # runs before form_valid() — school must already be set on
            # the instance by then, or the uniqueness check silently
            # validates against school=None instead of the real school.
            form.instance.school = self.current_school
        return form

    def get_success_url(self) -> str:
        return self._safe_next_url() or reverse_lazy(self.list_url_name)

    def _safe_next_url(self) -> str:
        next_url = self.request.POST.get("next") or self.request.GET.get("next", "")
        if url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return ""

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": self.title,
                "list_url_name": self.list_url_name,
                "return_url": self._safe_next_url(),
            }
        )
        return context


class SchedulerUpdateView(SchoolScopedQuerysetMixin, SchoolAccessRequiredMixin, SuccessMessageMixin, UpdateView):
    template_name = "scheduler/object_form.html"
    success_message = "Updated successfully."
    title = ""
    list_url_name = ""

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()
        kwargs["school"] = self.current_school
        return kwargs

    def get_success_url(self) -> str:
        return self._safe_next_url() or reverse_lazy(self.list_url_name)

    def _safe_next_url(self) -> str:
        next_url = self.request.POST.get("next") or self.request.GET.get("next", "")
        if url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return ""

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "title": self.title,
                "list_url_name": self.list_url_name,
                "return_url": self._safe_next_url(),
            }
        )
        return context


class SchedulerDeleteView(SchoolScopedQuerysetMixin, SchoolAccessRequiredMixin, ProtectedDeleteMixin, DeleteView):
    template_name = "scheduler/object_confirm_delete.html"
    title = ""
    list_url_name = ""

    def get_success_url(self) -> str:
        return reverse_lazy(self.list_url_name)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update({"title": self.title, "list_url_name": self.list_url_name})
        return context


class TeacherListView(SchedulerListView):
    model = Teacher
    title = "Teachers"
    create_url_name = "teacher-create"
    edit_url_name = "teacher-update"
    delete_url_name = "teacher-delete"
    columns = [("name", "Name"), ("email", "Email"), ("school", "School")]


class TeacherCreateView(SchedulerCreateView):
    model = Teacher
    form_class = TeacherForm
    assign_current_school = True
    title = "New Teacher"
    list_url_name = "teacher-list"


class TeacherUpdateView(SchedulerUpdateView):
    model = Teacher
    form_class = TeacherForm
    title = "Edit Teacher"
    list_url_name = "teacher-list"


class TeacherDeleteView(SchedulerDeleteView):
    model = Teacher
    title = "Delete Teacher"
    list_url_name = "teacher-list"


class RoomListView(SchedulerListView):
    model = Room
    title = "Rooms"
    create_url_name = "room-create"
    edit_url_name = "room-update"
    delete_url_name = "room-delete"
    columns = [("name", "Name"), ("capacity", "Capacity"), ("school", "School")]


class RoomCreateView(SchedulerCreateView):
    model = Room
    form_class = RoomForm
    assign_current_school = True
    title = "New Room"
    list_url_name = "room-list"


class RoomUpdateView(SchedulerUpdateView):
    model = Room
    form_class = RoomForm
    title = "Edit Room"
    list_url_name = "room-list"


class RoomDeleteView(SchedulerDeleteView):
    model = Room
    title = "Delete Room"
    list_url_name = "room-list"


class SubjectListView(SchedulerListView):
    model = Subject
    title = "Subjects"
    create_url_name = "subject-create"
    edit_url_name = "subject-update"
    delete_url_name = "subject-delete"
    columns = [("name", "Name"), ("code", "Code"), ("school", "School")]


class SubjectCreateView(SchedulerCreateView):
    model = Subject
    form_class = SubjectForm
    assign_current_school = True
    title = "New Subject"
    list_url_name = "subject-list"


class SubjectUpdateView(SchedulerUpdateView):
    model = Subject
    form_class = SubjectForm
    title = "Edit Subject"
    list_url_name = "subject-list"


class SubjectDeleteView(SchedulerDeleteView):
    model = Subject
    title = "Delete Subject"
    list_url_name = "subject-list"


class StudentGroupListView(SchedulerListView):
    model = StudentGroup
    title = "Student Groups"
    create_url_name = "student-group-create"
    edit_url_name = "student-group-update"
    delete_url_name = "student-group-delete"
    columns = [("name", "Name"), ("size", "Size"), ("school", "School")]


class StudentGroupCreateView(SchedulerCreateView):
    model = StudentGroup
    form_class = StudentGroupForm
    assign_current_school = True
    title = "New Student Group"
    list_url_name = "student-group-list"


class StudentGroupUpdateView(SchedulerUpdateView):
    model = StudentGroup
    form_class = StudentGroupForm
    title = "Edit Student Group"
    list_url_name = "student-group-list"


class StudentGroupDeleteView(SchedulerDeleteView):
    model = StudentGroup
    title = "Delete Student Group"
    list_url_name = "student-group-list"


class AcademicYearListView(SchedulerListView):
    model = AcademicYear
    title = "Academic Years"
    create_url_name = "academic-year-create"
    edit_url_name = "academic-year-update"
    delete_url_name = "academic-year-delete"
    columns = [("name", "Name"), ("school", "School")]


class AcademicYearCreateView(SchedulerCreateView):
    model = AcademicYear
    form_class = AcademicYearForm
    assign_current_school = True
    title = "New Academic Year"
    list_url_name = "academic-year-list"


class AcademicYearUpdateView(SchedulerUpdateView):
    model = AcademicYear
    form_class = AcademicYearForm
    title = "Edit Academic Year"
    list_url_name = "academic-year-list"


class AcademicYearDeleteView(SchedulerDeleteView):
    model = AcademicYear
    title = "Delete Academic Year"
    list_url_name = "academic-year-list"


class PeriodListView(SchedulerListView):
    model = Period
    queryset = Period.objects.select_related("academic_year")
    school_filter_lookup = "academic_year__school"
    title = "Periods"
    create_url_name = "period-create"
    edit_url_name = "period-update"
    delete_url_name = "period-delete"
    columns = [
        ("academic_year", "Academic Year"),
        ("order", "Order"),
        ("name", "Name"),
        ("start_time", "Start"),
        ("end_time", "End"),
        ("kind", "Kind"),
    ]


class PeriodCreateView(SchedulerCreateView):
    model = Period
    form_class = PeriodForm
    title = "New Period"
    list_url_name = "period-list"


class PeriodUpdateView(SchedulerUpdateView):
    model = Period
    form_class = PeriodForm
    school_filter_lookup = "academic_year__school"
    title = "Edit Period"
    list_url_name = "period-list"


class PeriodDeleteView(SchedulerDeleteView):
    model = Period
    school_filter_lookup = "academic_year__school"
    title = "Delete Period"
    list_url_name = "period-list"


class LessonListView(SchedulerListView):
    model = Lesson
    queryset = Lesson.objects.select_related(
        "teacher", "subject", "room", "student_group", "start_period"
    )
    school_filter_lookup = "start_period__academic_year__school"
    title = "Lessons"
    create_url_name = "lesson-create"
    edit_url_name = "lesson-update"
    delete_url_name = "lesson-delete"
    columns = [
        ("subject", "Subject"),
        ("teacher", "Teacher"),
        ("room", "Room"),
        ("student_group", "Student Group"),
        ("day", "Day"),
        ("start_period", "Start Period"),
    ]


class LessonWriteMixin:
    is_update = False

    def form_valid(self, form):
        cleaned = form.cleaned_data
        service = build_schedule_service()
        try:
            lesson = DomainLesson(
                id=self.object.pk if self.is_update else None,
                teacher_id=cleaned["teacher"].pk,
                subject_id=cleaned["subject"].pk,
                room_id=cleaned["room"].pk,
                student_group_id=cleaned["student_group"].pk,
                day=Day(cleaned["day"]),
                start_period_id=cleaned["start_period"].pk,
                planned_substitute_id=(
                    cleaned["planned_substitute"].pk
                    if cleaned["planned_substitute"] is not None
                    else None
                ),
                notes=cleaned["notes"],
            )
            if self.is_update:
                service.update_lesson(lesson)
                messages.success(self.request, "Updated successfully.")
            else:
                service.create_lesson(lesson)
                messages.success(self.request, "Created successfully.")
        except ScheduleConflictError as exc:
            for conflict in exc.conflicts:
                form.add_error(conflict.field, conflict.message)
            return self.form_invalid(form)
        except InvalidLessonPlacementError as exc:
            form.add_error("start_period", str(exc))
            return self.form_invalid(form)
        except CrossSchoolLessonError as exc:
            form.add_error(None, str(exc))
            return self.form_invalid(form)
        return redirect(self.get_success_url())


class LessonCreateView(LessonWriteMixin, SchedulerCreateView):
    model = Lesson
    form_class = LessonForm
    title = "New Lesson"
    list_url_name = "lesson-list"


class LessonUpdateView(LessonWriteMixin, SchedulerUpdateView):
    model = Lesson
    form_class = LessonForm
    school_filter_lookup = "start_period__academic_year__school"
    title = "Edit Lesson"
    list_url_name = "lesson-list"
    is_update = True


class LessonDeleteView(SchedulerDeleteView):
    model = Lesson
    school_filter_lookup = "start_period__academic_year__school"
    title = "Delete Lesson"
    list_url_name = "lesson-list"


class ChooseSchoolView(LoginRequiredMixin, View):
    """Lets a user who belongs to more than one School pick which one
    they're currently working in. Only ever offers the schools the
    user actually has a PRINCIPAL SchoolMembership for."""

    template_name = "scheduler/choose_school.html"

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        memberships = CurrentSchoolService.memberships_for(request.user)
        if not memberships:
            return render(request, "scheduler/no_school_access.html", status=403)
        if len(memberships) == 1:
            CurrentSchoolService.set_current(request, memberships[0].school_id)
            return redirect("schedule")
        return render(request, self.template_name, {"memberships": memberships})

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        school = CurrentSchoolService.set_current(request, request.POST.get("school_id"))
        if school is None:
            memberships = CurrentSchoolService.memberships_for(request.user)
            messages.error(request, "Choose one of the schools you belong to.")
            return render(
                request, self.template_name, {"memberships": memberships}, status=400
            )
        return redirect("schedule")


@dataclass(frozen=True)
class ScheduleViewChoice:
    value: str
    label: str
    description: str
    is_primary: bool = True


@dataclass(frozen=True)
class ScheduleSelector:
    name: str
    label: str
    placeholder: str
    options: Any
    selected: str


@dataclass(frozen=True)
class SchedulePageState:
    current_view: str
    current_view_label: str
    view_choices: tuple[ScheduleViewChoice, ...]
    selector: ScheduleSelector | None
    waiting_for_view: bool
    waiting_for_selection: bool
    show_timetable: bool
    missing_academic_year: bool
    selected_academic_year_name: str


class ScheduleView(TemplateView):
    template_name = "scheduler/schedule.html"

    VIEW_CHOICES = (
        ScheduleViewChoice("teacher", "Teacher", "View one teacher's week"),
        ScheduleViewChoice(
            "student_group", "Student Group", "View one student group's week"
        ),
        ScheduleViewChoice(
            "whole_school",
            "Whole School",
            "View the complete master timetable",
            is_primary=False,
        ),
        ScheduleViewChoice(
            "room",
            "Room",
            "View one room's week",
            is_primary=False,
        ),
    )
    ENTITY_VIEWS = {
        "teacher": {
            "label": "Teacher",
            "placeholder": "Choose a teacher",
            "model": Teacher,
            "service_method": "schedule_for_teacher",
        },
        "student_group": {
            "label": "Student Group",
            "placeholder": "Choose a student group",
            "model": StudentGroup,
            "service_method": "schedule_for_student_group",
        },
        "room": {
            "label": "Room",
            "placeholder": "Choose a room",
            "model": Room,
            "service_method": "schedule_for_room",
        },
    }

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if (
            request.GET.get("view") == "whole_school"
            and not request.user.is_staff
        ):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def _view_choices(self) -> tuple[ScheduleViewChoice, ...]:
        if self.request.user.is_staff:
            return self.VIEW_CHOICES
        return tuple(
            choice for choice in self.VIEW_CHOICES if choice.value != "whole_school"
        )

    def _academic_years(self, current_school: Any) -> Any:
        # Anonymous visitors and authenticated users with no resolvable
        # current school keep today's public, unscoped behaviour — this
        # view stays intentionally public (see PROJECT_CONTEXT.md).
        # Only an authenticated principal with a current school gets
        # its data restricted to that school.
        if current_school is not None:
            return AcademicYear.objects.filter(school=current_school)
        return AcademicYear.objects.all()

    def _academic_year(self, academic_years: Any) -> AcademicYear | None:
        academic_year_id = self.request.GET.get("academic_year", "")
        if academic_year_id.isdigit():
            academic_year = academic_years.filter(pk=int(academic_year_id)).first()
            if academic_year is not None:
                return academic_year
        # AcademicYear is ordered newest first, so this is the current year until
        # the domain grows explicit academic-year dates.
        return academic_years.first()

    def _selector(self, current_view: str, current_school: Any) -> ScheduleSelector | None:
        configuration = self.ENTITY_VIEWS.get(current_view)
        if configuration is None:
            return None

        selected = self.request.GET.get(current_view, "")
        model = configuration["model"]
        queryset = (
            model.objects.filter(school=current_school)
            if current_school is not None
            else model.objects.all()
        )
        if not selected.isdigit() or not queryset.filter(pk=int(selected)).exists():
            selected = ""
        return ScheduleSelector(
            name=current_view,
            label=configuration["label"],
            placeholder=configuration["placeholder"],
            options=queryset,
            selected=selected,
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        service = build_schedule_service()
        current_school = CurrentSchoolService.resolve(self.request)

        academic_years = self._academic_years(current_school)
        academic_year = self._academic_year(academic_years)
        requested_view = self.request.GET.get("view", "")
        view_choices = self._view_choices()
        valid_views = {choice.value for choice in view_choices}
        current_view = requested_view if requested_view in valid_views else ""
        selector = self._selector(current_view, current_school)

        waiting_for_view = not current_view
        waiting_for_selection = selector is not None and not selector.selected
        show_timetable = bool(academic_year and current_view and not waiting_for_selection)

        grouped_schedule = {}
        periods = []
        if show_timetable:
            periods = service.periods(academic_year.pk)
            if current_view == "whole_school":
                grouped_schedule = service.schedule(academic_year.pk)
            else:
                configuration = self.ENTITY_VIEWS[current_view]
                schedule_method = getattr(service, configuration["service_method"])
                grouped_schedule = schedule_method(int(selector.selected), academic_year.pk)

        current_view_label = next(
            (choice.label for choice in view_choices if choice.value == current_view),
            "",
        )
        page = SchedulePageState(
            current_view=current_view,
            current_view_label=current_view_label,
            view_choices=view_choices,
            selector=selector,
            waiting_for_view=waiting_for_view,
            waiting_for_selection=waiting_for_selection,
            show_timetable=show_timetable,
            missing_academic_year=bool(current_view and academic_year is None),
            selected_academic_year_name=str(academic_year) if academic_year else "",
        )
        focused_rows = []
        whole_school_timetable = None
        if show_timetable and current_view == "whole_school":
            whole_school_timetable = WholeSchoolTimetableRenderer().render(
                grouped_schedule, periods
            )
        elif show_timetable:
            focused_rows = FocusedTimetableRenderer().render(
                service.timetable_rows(grouped_schedule, periods),
                current_view,
            )

        context.update(
            {
                "page": page,
                "schedule": grouped_schedule,
                "rows": focused_rows,
                "whole_school_timetable": whole_school_timetable,
                "periods": periods,
                "academic_years": academic_years,
                "selected_academic_year": str(academic_year.pk) if academic_year else "",
            }
        )
        return context


class GeneratePlannedSubstitutionsView(SchoolAccessRequiredMixin, View):
    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        academic_year_id = request.POST.get("academic_year", "")
        # Never trust a POSTed academic_year id: this mutates every
        # Lesson in that academic year's planned_substitute, so it must
        # belong to the current school, not merely be a valid id. The
        # service-level school_id below is a defense-in-depth backstop,
        # not a substitute for this check.
        if academic_year_id.isdigit() and AcademicYear.objects.filter(
            pk=academic_year_id, school=self.current_school
        ).exists():
            try:
                build_substitution_service().generate_planned_substitutions(
                    int(academic_year_id), school_id=self.current_school.id
                )
            except SchoolAuthorizationError:
                messages.error(request, "Choose an academic year before generating substitutions.")
            else:
                messages.success(request, "Planned substitutions generated.")
        else:
            messages.error(request, "Choose an academic year before generating substitutions.")

        next_url = request.POST.get("next", "")
        if not url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            next_url = reverse("schedule")
        return redirect(next_url)


class StaffScheduleView(SchoolAccessRequiredMixin, TemplateView):
    template_name = "scheduler/staff_schedule.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        academic_years = AcademicYear.objects.filter(school=self.current_school)
        academic_year_id = self.request.GET.get("academic_year", "")
        academic_year = (
            academic_years.filter(pk=int(academic_year_id)).first()
            if academic_year_id.isdigit()
            else academic_years.first()
        )
        staff_schedule = None
        selected_slot = None
        if academic_year is not None:
            staff_schedule = build_schedule_service().staff_schedule(academic_year.pk)
            selected_day = self.request.GET.get("day", "")
            selected_period_id = self.request.GET.get("period", "")
            if selected_period_id.isdigit():
                selected_slot = next(
                    (
                        slot
                        for row in staff_schedule.rows
                        if row.day.value == selected_day
                        for slot in row.slots
                        if slot.period.id == int(selected_period_id) and not slot.is_break
                    ),
                    None,
                )

        context.update(
            {
                "academic_years": academic_years,
                "selected_academic_year": str(academic_year.pk) if academic_year else "",
                "staff_schedule": staff_schedule,
                "selected_slot": selected_slot,
            }
        )
        return context


class TeacherSubstitutionView(SchoolAccessRequiredMixin, TemplateView):
    template_name = "scheduler/teacher_substitution.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        form = TeacherSubstitutionForm(self.request.GET or None, school=self.current_school)
        available_teachers = None

        if form.is_bound and form.is_valid():
            substitution_service = build_substitution_service()
            available_teachers = substitution_service.available_teachers(
                academic_year_id=form.cleaned_data["academic_year"].pk,
                day=Day(form.cleaned_data["day"]),
                period_id=form.cleaned_data["period"].pk,
            )

        context.update(
            {
                "form": form,
                "available_teachers": available_teachers,
            }
        )
        return context
