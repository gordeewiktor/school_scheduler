from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import ProtectedError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, TemplateView, UpdateView

from app.application.services.conflicts import ConflictService
from app.application.services.schedules import ScheduleService
from app.infrastructure.database.models import Lesson, Room, StudentGroup, Subject, Teacher, TimeSlot
from app.infrastructure.repositories.django_lessons import DjangoLessonRepository
from app.presentation.web.forms import (
    LessonForm,
    RoomForm,
    StudentGroupForm,
    SubjectForm,
    TeacherForm,
    TimeSlotForm,
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
            "time_slots": TimeSlot.objects.count(),
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


class TimeSlotListView(SchedulerListView):
    model = TimeSlot
    title = "Time Slots"
    create_url_name = "time-slot-create"
    edit_url_name = "time-slot-update"
    delete_url_name = "time-slot-delete"
    columns = [("day", "Day"), ("start_time", "Start"), ("end_time", "End")]


class TimeSlotCreateView(SchedulerCreateView):
    model = TimeSlot
    form_class = TimeSlotForm
    title = "New Time Slot"
    list_url_name = "time-slot-list"


class TimeSlotUpdateView(SchedulerUpdateView):
    model = TimeSlot
    form_class = TimeSlotForm
    title = "Edit Time Slot"
    list_url_name = "time-slot-list"


class TimeSlotDeleteView(SchedulerDeleteView):
    model = TimeSlot
    title = "Delete Time Slot"
    list_url_name = "time-slot-list"


class LessonListView(SchedulerListView):
    model = Lesson
    queryset = Lesson.objects.select_related("teacher", "subject", "room", "student_group", "time_slot")
    title = "Lessons"
    create_url_name = "lesson-create"
    edit_url_name = "lesson-update"
    delete_url_name = "lesson-delete"
    columns = [
        ("subject", "Subject"),
        ("teacher", "Teacher"),
        ("room", "Room"),
        ("student_group", "Student Group"),
        ("time_slot", "Time Slot"),
    ]


class LessonCreateView(SchedulerCreateView):
    model = Lesson
    form_class = LessonForm
    title = "New Lesson"
    list_url_name = "lesson-list"


class LessonUpdateView(SchedulerUpdateView):
    model = Lesson
    form_class = LessonForm
    title = "Edit Lesson"
    list_url_name = "lesson-list"


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

        teacher_id = self.request.GET.get("teacher")
        room_id = self.request.GET.get("room")
        student_group_id = self.request.GET.get("student_group")

        if teacher_id:
            grouped_schedule = service.schedule_for_teacher(int(teacher_id))
        elif room_id:
            grouped_schedule = service.schedule_for_room(int(room_id))
        elif student_group_id:
            grouped_schedule = service.schedule_for_student_group(int(student_group_id))
        else:
            grouped_schedule = service.weekly_schedule(repository.list_lessons())

        context.update(
            {
                "schedule": grouped_schedule,
                "teachers": Teacher.objects.all(),
                "rooms": Room.objects.all(),
                "student_groups": StudentGroup.objects.all(),
                "selected_teacher": teacher_id or "",
                "selected_room": room_id or "",
                "selected_student_group": student_group_id or "",
            }
        )
        return context
