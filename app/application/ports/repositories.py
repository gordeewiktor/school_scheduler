from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.domain.models import Day, Lesson, Period, Teacher
from app.domain.policies import ExistingLesson, LessonRequest


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
    duration: int
    notes: str = ""


class LessonRepository(Protocol):
    def list_teachers(self) -> list[Teacher]: ...

    def periods_for_placement(self, start_period_id: int, duration: int) -> list[Period]: ...

    def list_periods(self, academic_year_id: int) -> list[Period]: ...

    def list_potential_conflicts(self, request: LessonRequest) -> list[ExistingLesson]: ...

    def create_lesson(self, lesson: Lesson) -> Lesson: ...

    def update_lesson(self, lesson: Lesson) -> Lesson: ...

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
