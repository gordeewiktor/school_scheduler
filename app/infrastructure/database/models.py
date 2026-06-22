from django.core.exceptions import ValidationError
from django.db import models

from app.application.services.conflicts import ConflictService
from app.domain.exceptions import InvalidTimeSlotError
from app.domain.models import Lesson as DomainLesson
from app.domain.models import TimeSlot as DomainTimeSlot
from app.domain.policies import LessonRequest


DAYS_OF_WEEK = [
    ("Monday", "Monday"),
    ("Tuesday", "Tuesday"),
    ("Wednesday", "Wednesday"),
    ("Thursday", "Thursday"),
    ("Friday", "Friday"),
    ("Saturday", "Saturday"),
    ("Sunday", "Sunday"),
]


class Teacher(models.Model):
    name = models.CharField(max_length=120, unique=True)
    email = models.EmailField(blank=True)

    class Meta:
        app_label = "app"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Room(models.Model):
    name = models.CharField(max_length=80, unique=True)
    capacity = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        app_label = "app"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Subject(models.Model):
    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=30, blank=True)

    class Meta:
        app_label = "app"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class StudentGroup(models.Model):
    name = models.CharField(max_length=120, unique=True)
    size = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        app_label = "app"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class TimeSlot(models.Model):
    day = models.CharField(max_length=12, choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        app_label = "app"
        ordering = ["day", "start_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["day", "start_time", "end_time"],
                name="unique_time_slot",
            )
        ]

    def __str__(self) -> str:
        return f"{self.day} {self.start_time:%H:%M}-{self.end_time:%H:%M}"

    def to_domain(self) -> DomainTimeSlot:
        return DomainTimeSlot(
            day=self.day,
            start_time=self.start_time,
            end_time=self.end_time,
        )

    def clean(self) -> None:
        super().clean()
        # ModelForm calls model.clean() even when field parsing has failed. In
        # that case the invalid fields remain None and their field-level errors
        # should be returned instead of constructing a domain object with None.
        if self.start_time is None or self.end_time is None:
            return
        try:
            self.to_domain()
        except InvalidTimeSlotError as exc:
            raise ValidationError({"end_time": str(exc)}) from exc


class Lesson(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.PROTECT, related_name="lessons")
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="lessons")
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name="lessons")
    student_group = models.ForeignKey(
        StudentGroup,
        on_delete=models.PROTECT,
        related_name="lessons",
    )
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.PROTECT, related_name="lessons")
    notes = models.TextField(blank=True)

    class Meta:
        app_label = "app"
        ordering = [
            "time_slot__day",
            "time_slot__start_time",
            "student_group__name",
            "subject__name",
        ]

    def __str__(self) -> str:
        return f"{self.subject} with {self.teacher} ({self.student_group})"

    def to_domain(self) -> DomainLesson:
        return DomainLesson(
            id=self.pk,
            teacher_id=self.teacher_id,
            subject_id=self.subject_id,
            room_id=self.room_id,
            student_group_id=self.student_group_id,
            time_slot_id=self.time_slot_id,
        )

    def to_lesson_request(self) -> LessonRequest:
        return LessonRequest(
            teacher_id=self.teacher_id,
            room_id=self.room_id,
            student_group_id=self.student_group_id,
            time_slot=self.time_slot.to_domain(),
            lesson_id=self.pk,
        )

    def clean(self) -> None:
        super().clean()
        if not all([self.teacher_id, self.room_id, self.student_group_id, self.time_slot_id]):
            return

        from app.infrastructure.repositories.django_lessons import DjangoLessonRepository

        conflict_service = ConflictService(DjangoLessonRepository())
        conflicts = conflict_service.find_conflicts(self.to_lesson_request())
        if conflicts:
            errors: dict[str, list[str]] = {}
            field_map = {"teacher": "teacher", "room": "room", "student_group": "student_group"}
            for conflict in conflicts:
                errors.setdefault(field_map[conflict.field], []).append(conflict.message)
            raise ValidationError(errors)

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)
