from dataclasses import dataclass
from typing import Any

from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import ProtectedError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from app.application.services.conflicts import ConflictService
from app.application.services.schedules import ScheduleService
from app.domain.exceptions import InvalidLessonPlacementError, ScheduleConflictError
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
from app.infrastructure.repositories.django_lessons import DjangoLessonRepository
from app.presentation.web.forms import (
    LessonForm,
    RoomForm,
    StudentGroupForm,
    SubjectForm,
    TeacherForm,
    AcademicYearForm,
    PeriodForm,
)
from app.presentation.web.schedule_renderers import WholeSchoolTimetableRenderer


class AdministratorRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if request.user.is_authenticated and not request.user.is_staff:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


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


class SchedulerListView(AdministratorRequiredMixin, ListView):
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


class SchedulerCreateView(AdministratorRequiredMixin, SuccessMessageMixin, CreateView):
    template_name = "scheduler/object_form.html"
    success_message = "Created successfully."
    title = ""
    list_url_name = ""

    def get_success_url(self) -> str:
        return reverse_lazy(self.list_url_name)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update({"title": self.title, "list_url_name": self.list_url_name})
        return context


class SchedulerUpdateView(AdministratorRequiredMixin, SuccessMessageMixin, UpdateView):
    template_name = "scheduler/object_form.html"
    success_message = "Updated successfully."
    title = ""
    list_url_name = ""

    def get_success_url(self) -> str:
        return reverse_lazy(self.list_url_name)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update({"title": self.title, "list_url_name": self.list_url_name})
        return context


class SchedulerDeleteView(AdministratorRequiredMixin, ProtectedDeleteMixin, DeleteView):
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
    columns = [("name", "Name"), ("email", "Email")]


class TeacherCreateView(SchedulerCreateView):
    model = Teacher
    form_class = TeacherForm
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
    columns = [("name", "Name"), ("capacity", "Capacity")]


class RoomCreateView(SchedulerCreateView):
    model = Room
    form_class = RoomForm
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
    columns = [("name", "Name"), ("code", "Code")]


class SubjectCreateView(SchedulerCreateView):
    model = Subject
    form_class = SubjectForm
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
    columns = [("name", "Name"), ("size", "Size")]


class StudentGroupCreateView(SchedulerCreateView):
    model = StudentGroup
    form_class = StudentGroupForm
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
    columns = [("name", "Name")]


class AcademicYearCreateView(SchedulerCreateView):
    model = AcademicYear
    form_class = AcademicYearForm
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
    title = "Edit Period"
    list_url_name = "period-list"


class PeriodDeleteView(SchedulerDeleteView):
    model = Period
    title = "Delete Period"
    list_url_name = "period-list"


class LessonListView(SchedulerListView):
    model = Lesson
    queryset = Lesson.objects.select_related(
        "teacher", "subject", "room", "student_group", "start_period"
    )
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
        ("duration", "Duration"),
    ]


class LessonWriteMixin:
    is_update = False

    def form_valid(self, form):
        cleaned = form.cleaned_data
        repository = DjangoLessonRepository()
        service = ScheduleService(repository, ConflictService(repository))
        try:
            lesson = DomainLesson(
                id=self.object.pk if self.is_update else None,
                teacher_id=cleaned["teacher"].pk,
                subject_id=cleaned["subject"].pk,
                room_id=cleaned["room"].pk,
                student_group_id=cleaned["student_group"].pk,
                day=Day(cleaned["day"]),
                start_period_id=cleaned["start_period"].pk,
                duration=cleaned["duration"],
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
        return redirect(self.get_success_url())


class LessonCreateView(LessonWriteMixin, SchedulerCreateView):
    model = Lesson
    form_class = LessonForm
    title = "New Lesson"
    list_url_name = "lesson-list"


class LessonUpdateView(LessonWriteMixin, SchedulerUpdateView):
    model = Lesson
    form_class = LessonForm
    title = "Edit Lesson"
    list_url_name = "lesson-list"
    is_update = True


class LessonDeleteView(SchedulerDeleteView):
    model = Lesson
    title = "Delete Lesson"
    list_url_name = "lesson-list"


@dataclass(frozen=True)
class ScheduleViewChoice:
    value: str
    label: str
    description: str


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


class ScheduleView(LoginRequiredMixin, TemplateView):
    template_name = "scheduler/schedule.html"

    VIEW_CHOICES = (
        ScheduleViewChoice("teacher", "Teacher", "View one teacher's week"),
        ScheduleViewChoice(
            "student_group", "Student Group", "View one student group's week"
        ),
        ScheduleViewChoice("room", "Room", "View one room's week"),
        ScheduleViewChoice(
            "whole_school", "Whole School", "View the complete master timetable"
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
            request.user.is_authenticated
            and request.GET.get("view") == "whole_school"
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

    def _academic_year(self, academic_years: Any) -> AcademicYear | None:
        academic_year_id = self.request.GET.get("academic_year", "")
        if academic_year_id.isdigit():
            academic_year = academic_years.filter(pk=int(academic_year_id)).first()
            if academic_year is not None:
                return academic_year
        return academic_years.first()

    def _selector(self, current_view: str) -> ScheduleSelector | None:
        configuration = self.ENTITY_VIEWS.get(current_view)
        if configuration is None:
            return None

        selected = self.request.GET.get(current_view, "")
        model = configuration["model"]
        if not selected.isdigit() or not model.objects.filter(pk=int(selected)).exists():
            selected = ""
        return ScheduleSelector(
            name=current_view,
            label=configuration["label"],
            placeholder=configuration["placeholder"],
            options=model.objects.all(),
            selected=selected,
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        repository = DjangoLessonRepository()
        service = ScheduleService(repository, ConflictService(repository))

        academic_years = AcademicYear.objects.all()
        academic_year = self._academic_year(academic_years)
        requested_view = self.request.GET.get("view", "")
        view_choices = self._view_choices()
        valid_views = {choice.value for choice in view_choices}
        current_view = requested_view if requested_view in valid_views else ""
        selector = self._selector(current_view)

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
        )
        focused_rows = []
        whole_school_timetable = None
        if show_timetable and current_view == "whole_school":
            whole_school_timetable = WholeSchoolTimetableRenderer().render(
                grouped_schedule, periods
            )
        elif show_timetable:
            focused_rows = service.timetable_rows(grouped_schedule, periods)

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


class TeacherSubstitutionView(LoginRequiredMixin, TemplateView):
    template_name = "scheduler/teacher_substitution.html"
