from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from django.db import transaction

from app.application.ports.repositories import LessonRepository, PeriodSpec
from app.domain.exceptions import InvalidPeriodError, PeriodsAlreadyExistError, SchoolAuthorizationError
from app.domain.models import Period, PeriodKind


@dataclass(frozen=True, slots=True)
class BreakAfter:
    """A break inserted after the given 1-based lesson-period number."""

    after_period: int
    duration_minutes: int


class PeriodGenerationService:
    def __init__(self, lesson_repository: LessonRepository) -> None:
        self.lesson_repository = lesson_repository

    def generate(
        self,
        *,
        academic_year_id: int,
        school_id: int,
        lesson_count: int,
        first_start_time: time,
        lesson_duration_minutes: int,
        breaks: list[BreakAfter] = (),
    ) -> list[Period]:
        actual_school_id = self.lesson_repository.get_academic_year_school_id(academic_year_id)
        if actual_school_id != school_id:
            raise SchoolAuthorizationError(
                "This academic year does not belong to the given school."
            )

        self._validate_inputs(lesson_count, lesson_duration_minutes, breaks)
        specs = self._build_specs(lesson_count, first_start_time, lesson_duration_minutes, breaks)

        with transaction.atomic():
            if self.lesson_repository.list_periods(academic_year_id):
                raise PeriodsAlreadyExistError(
                    "This academic year already has periods. Generation is only "
                    "available for an academic year with no periods yet."
                )
            return self.lesson_repository.create_periods(academic_year_id, specs)

    @staticmethod
    def _validate_inputs(
        lesson_count: int,
        lesson_duration_minutes: int,
        breaks: list[BreakAfter],
    ) -> None:
        if lesson_count < 1:
            raise InvalidPeriodError("Number of lesson periods must be at least 1.")
        if lesson_duration_minutes < 1:
            raise InvalidPeriodError("Lesson duration must be at least 1 minute.")

        seen_positions: set[int] = set()
        for br in breaks:
            if br.duration_minutes < 1:
                raise InvalidPeriodError("Break duration must be at least 1 minute.")
            if not (1 <= br.after_period <= lesson_count):
                raise InvalidPeriodError(
                    f"A break after lesson period {br.after_period} is not valid for "
                    f"{lesson_count} lesson period(s)."
                )
            if br.after_period in seen_positions:
                raise InvalidPeriodError(
                    f"Only one break may be placed after lesson period {br.after_period}."
                )
            seen_positions.add(br.after_period)

    @staticmethod
    def _build_specs(
        lesson_count: int,
        first_start_time: time,
        lesson_duration_minutes: int,
        breaks: list[BreakAfter],
    ) -> list[PeriodSpec]:
        breaks_by_period = {br.after_period: br.duration_minutes for br in breaks}
        anchor_day = date(2000, 1, 1)
        specs: list[PeriodSpec] = []
        order = 1
        cursor = datetime.combine(anchor_day, first_start_time)

        for lesson_number in range(1, lesson_count + 1):
            cursor = PeriodGenerationService._append_spec(
                specs,
                order=order,
                name=f"Period {lesson_number}",
                start=cursor,
                duration_minutes=lesson_duration_minutes,
                kind=PeriodKind.LESSON,
                anchor_day=anchor_day,
            )
            order += 1

            duration_minutes = breaks_by_period.get(lesson_number)
            if duration_minutes is not None:
                cursor = PeriodGenerationService._append_spec(
                    specs,
                    order=order,
                    name=f"Break after Period {lesson_number}",
                    start=cursor,
                    duration_minutes=duration_minutes,
                    kind=PeriodKind.BREAK,
                    anchor_day=anchor_day,
                )
                order += 1

        return specs

    @staticmethod
    def _append_spec(
        specs: list[PeriodSpec],
        *,
        order: int,
        name: str,
        start: datetime,
        duration_minutes: int,
        kind: PeriodKind,
        anchor_day: date,
    ) -> datetime:
        end = start + timedelta(minutes=duration_minutes)
        if end.date() != anchor_day:
            raise InvalidPeriodError(
                "The generated schedule runs past midnight. Reduce the lesson "
                "count, duration, or break lengths."
            )
        specs.append(
            PeriodSpec(
                order=order,
                name=name,
                start_time=start.time(),
                end_time=end.time(),
                kind=kind,
            )
        )
        return end
