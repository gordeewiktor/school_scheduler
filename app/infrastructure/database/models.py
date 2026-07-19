from django.core.exceptions import ValidationError
from django.db import models

from app.domain.exceptions import InvalidPeriodError
from app.domain.models import Day as DomainDay
from app.domain.models import Lesson as DomainLesson
from app.domain.models import Period as DomainPeriod
from app.domain.models import PeriodKind as DomainPeriodKind


class AcademicYear(models.Model):
    name = models.CharField(max_length=40, unique=True)
    default_period_duration = models.PositiveIntegerField(default=45)

    class Meta:
        app_label = "app"
        ordering = ["-name"]

    def __str__(self) -> str:
        return self.name


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


class Period(models.Model):
    class Kind(models.TextChoices):
        LESSON = "LESSON", "Lesson"
        BREAK = "BREAK", "Break"

    academic_year = models.ForeignKey(
        AcademicYear, on_delete=models.CASCADE, related_name="periods"
    )
    name = models.CharField(max_length=80)
    order = models.PositiveIntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.LESSON)

    class Meta:
        app_label = "app"
        ordering = ["academic_year", "order"]
        constraints = [
            models.UniqueConstraint(
                fields=["academic_year", "order"], name="unique_period_order_per_year"
            ),
            models.UniqueConstraint(
                fields=["academic_year", "name"], name="unique_period_name_per_year"
            ),
        ]

    def __str__(self) -> str:
        return (
            f"{self.academic_year} – {self.name} "
            f"({self.start_time:%H:%M}-{self.end_time:%H:%M})"
        )

    def to_domain(self) -> DomainPeriod:
        return DomainPeriod(
            id=self.pk,
            academic_year_id=self.academic_year_id,
            name=self.name,
            order=self.order,
            start_time=self.start_time,
            end_time=self.end_time,
            kind=DomainPeriodKind(self.kind),
        )

    def clean(self) -> None:
        super().clean()
        if self.start_time is None or self.end_time is None or self.order is None:
            return
        try:
            self.to_domain()
        except InvalidPeriodError as exc:
            raise ValidationError({"end_time": str(exc)}) from exc


class Lesson(models.Model):
    class Day(models.TextChoices):
        MONDAY = "MONDAY", "Monday"
        TUESDAY = "TUESDAY", "Tuesday"
        WEDNESDAY = "WEDNESDAY", "Wednesday"
        THURSDAY = "THURSDAY", "Thursday"
        FRIDAY = "FRIDAY", "Friday"

    teacher = models.ForeignKey(Teacher, on_delete=models.PROTECT, related_name="lessons")
    planned_substitute = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="planned_substitutions",
        related_query_name="planned_substitution",
    )
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="lessons")
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name="lessons")
    student_group = models.ForeignKey(
        StudentGroup, on_delete=models.PROTECT, related_name="lessons"
    )
    day = models.CharField(max_length=9, choices=Day.choices)
    start_period = models.ForeignKey(
        Period, on_delete=models.PROTECT, related_name="starting_lessons"
    )
    notes = models.TextField(blank=True)

    class Meta:
        app_label = "app"
        ordering = ["day", "start_period__order", "student_group__name", "subject__name"]

    def __str__(self) -> str:
        return f"{self.subject} with {self.teacher} ({self.student_group})"

    def to_domain(self) -> DomainLesson:
        return DomainLesson(
            id=self.pk,
            teacher_id=self.teacher_id,
            planned_substitute_id=self.planned_substitute_id,
            subject_id=self.subject_id,
            room_id=self.room_id,
            student_group_id=self.student_group_id,
            day=DomainDay(self.day),
            start_period_id=self.start_period_id,
            notes=self.notes,
        )
