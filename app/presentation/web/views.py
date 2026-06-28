from typing import Any

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


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "scheduler/dashboard.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["counts"] = {
            "teachers": Teacher.objects.count(),
            "rooms": Room.objects.count(),
            "subjects": Subject.objects.count(),
            "student_groups": StudentGroup.objects.count(),
            "academic_years": AcademicYear.objects.count(),
            "periods": Period.objects.count(),
            "lessons": Lesson.objects.count(),
        }
        return context


class ProtectedDeleteMixin:
    protected_redirect_url: str = "dashboard"

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
            return redirect(self.protected_redirect_url)


class SchedulerListView(LoginRequiredMixin, ListView):
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


class SchedulerCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
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


class SchedulerUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
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


class SchedulerDeleteView(LoginRequiredMixin, ProtectedDeleteMixin, DeleteView):
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


class ScheduleView(LoginRequiredMixin, TemplateView):
    template_name = "scheduler/schedule.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        repository = DjangoLessonRepository()
        service = ScheduleService(repository, ConflictService(repository))

        academic_years = AcademicYear.objects.all()
        academic_year_id = self.request.GET.get("academic_year")
        academic_year = None
        if academic_year_id and academic_year_id.isdigit():
            academic_year = academic_years.filter(pk=int(academic_year_id)).first()
        if academic_year is None:
            academic_year = academic_years.first()

        teacher_id = self.request.GET.get("teacher")
        room_id = self.request.GET.get("room")
        student_group_id = self.request.GET.get("student_group")

        if academic_year is None:
            grouped_schedule = {}
            periods = []
        elif teacher_id and teacher_id.isdigit():
            grouped_schedule = service.schedule_for_teacher(int(teacher_id), academic_year.pk)
            periods = service.periods(academic_year.pk)
        elif room_id and room_id.isdigit():
            grouped_schedule = service.schedule_for_room(int(room_id), academic_year.pk)
            periods = service.periods(academic_year.pk)
        elif student_group_id and student_group_id.isdigit():
            grouped_schedule = service.schedule_for_student_group(
                int(student_group_id), academic_year.pk
            )
            periods = service.periods(academic_year.pk)
        else:
            grouped_schedule = service.schedule(academic_year.pk) if academic_year else {}
            periods = service.periods(academic_year.pk) if academic_year else []

        context.update(
            {
                "schedule": grouped_schedule,
                "rows": service.timetable_rows(grouped_schedule, periods),
                "periods": periods,
                "academic_years": academic_years,
                "teachers": Teacher.objects.all(),
                "rooms": Room.objects.all(),
                "student_groups": StudentGroup.objects.all(),
                "selected_teacher": teacher_id or "",
                "selected_room": room_id or "",
                "selected_student_group": student_group_id or "",
                "selected_academic_year": str(academic_year.pk) if academic_year else "",
            }
        )
        return context
