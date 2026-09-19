from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from typing import Protocol

from app.domain.models import Day, Lesson, Period, PeriodKind, Teacher
from app.domain.policies import ExistingLesson, LessonRequest


@dataclass(frozen=True, slots=True)
class PeriodSpec:
    """A not-yet-persisted period, computed by PeriodGenerationService.

    Distinct from the domain `Period` dataclass, which requires a real
    `id` and therefore only represents already-persisted periods.
    """

    order: int
    name: str
    start_time: time
    end_time: time
    kind: PeriodKind


@dataclass(frozen=True, slots=True)
class ResourceSchoolIds:
    teacher_school_id: int | None
    room_school_id: int | None
    subject_school_id: int | None
    student_group_school_id: int | None
    period_school_id: int | None
    planned_substitute_school_id: int | None = None


@dataclass(frozen=True, slots=True)
class ScheduledLesson:
    id: int
    teacher_id: int
    teacher_name: str
    subject_name: str
    room_id: int
    room_name: str
    student_group_id: int
    student_group_name: str
    day: Day
    start_period: Period
    planned_substitute_id: int | None = None
    planned_substitute_name: str = ""
    notes: str = ""


class LessonRepository(Protocol):
    def list_teachers(self, school_id: int) -> list[Teacher]: ...

    def get_academic_year_school_id(self, academic_year_id: int) -> int | None: ...

    def get_resource_school_ids(
        self,
        *,
        teacher_id: int,
        room_id: int,
        subject_id: int,
        student_group_id: int,
        period_id: int,
        planned_substitute_id: int | None = None,
    ) -> ResourceSchoolIds: ...

    def get_period(self, period_id: int) -> Period | None: ...

    def list_periods(self, academic_year_id: int) -> list[Period]: ...

    def create_periods(
        self, academic_year_id: int, specs: list[PeriodSpec]
    ) -> list[Period]: ...

    def list_potential_conflicts(self, request: LessonRequest) -> list[ExistingLesson]: ...

    def create_lesson(self, lesson: Lesson) -> Lesson: ...

    def update_lesson(self, lesson: Lesson) -> Lesson: ...

    def set_planned_substitute(
        self,
        lesson_id: int,
        teacher_id: int | None,
    ) -> None: ...

    def list_lessons(self, academic_year_id: int) -> list[ScheduledLesson]: ...

    def list_lessons_starting_at(
        self, academic_year_id: int, day: Day, period_id: int
    ) -> list[ScheduledLesson]: ...

    def list_lessons_for_teacher(
        self, teacher_id: int, academic_year_id: int
    ) -> list[ScheduledLesson]: ...

    def list_lessons_for_room(
        self, room_id: int, academic_year_id: int
    ) -> list[ScheduledLesson]: ...

    def list_lessons_for_student_group(
        self, student_group_id: int, academic_year_id: int
    ) -> list[ScheduledLesson]: ...
   
    def list_lessons_for_substitute(
        self,
        teacher_id: int,
        academic_year_id: int,
    ) -> list[ScheduledLesson]: ...
