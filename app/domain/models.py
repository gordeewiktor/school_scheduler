from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from enum import StrEnum

from app.domain.exceptions import InvalidLessonPlacementError, InvalidPeriodError


class Day(StrEnum):
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"


class PeriodKind(StrEnum):
    LESSON = "LESSON"
    BREAK = "BREAK"


@dataclass(frozen=True, slots=True)
class Period:
    id: int
    academic_year_id: int
    name: str
    order: int
    start_time: time
    end_time: time
    kind: PeriodKind

    def __post_init__(self) -> None:
        if self.start_time >= self.end_time:
            raise InvalidPeriodError("Start time must be before end time.")
        if self.order < 1:
            raise InvalidPeriodError("Period order must be at least 1.")

    @property
    def accepts_lessons(self) -> bool:
        return self.kind == PeriodKind.LESSON


@dataclass(frozen=True, slots=True)
class Lesson:
    teacher_id: int
    subject_id: int
    room_id: int
    student_group_id: int
    day: Day
    start_period_id: int
    duration: int = 1
    notes: str = ""
    id: int | None = None

    def __post_init__(self) -> None:
        if self.duration < 1:
            raise InvalidLessonPlacementError("Duration must be at least 1.")
