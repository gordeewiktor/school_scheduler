from dataclasses import dataclass

from app.application.ports.repositories import ScheduledLesson
from app.domain.models import Day, Period, PeriodKind


@dataclass(frozen=True, slots=True)
class WholeSchoolPeriodCell:
    period: Period
    column: int
    is_break: bool


@dataclass(frozen=True, slots=True)
class WholeSchoolLessonCard:
    lesson_id: int
    subject: str
    teacher: str
    student_group: str
    column: int
    lane: int


@dataclass(frozen=True, slots=True)
class WholeSchoolDayRow:
    day: Day
    period_cells: tuple[WholeSchoolPeriodCell, ...]
    cards: tuple[WholeSchoolLessonCard, ...]
    lane_count: int


@dataclass(frozen=True, slots=True)
class WholeSchoolTimetable:
    periods: tuple[Period, ...]
    rows: tuple[WholeSchoolDayRow, ...]


class WholeSchoolTimetableRenderer:
    """Builds the compact, card-based presentation model for the master timetable."""

    SUBJECT_ALIASES = {
        "mathematics": "Math",
        "physical education": "PE",
        "information and communication technology": "ICT",
        "information technology": "IT",
        "english language": "English",
    }
    TEACHER_PREFIXES = (
        "teacher ",
        "mr. ",
        "mr ",
        "mrs. ",
        "mrs ",
        "ms. ",
        "ms ",
        "miss ",
        "dr. ",
        "dr ",
    )

    def render(
        self,
        schedule: dict[Day, list[ScheduledLesson]],
        periods: list[Period],
    ) -> WholeSchoolTimetable:
        period_indexes = {period.id: index for index, period in enumerate(periods)}
        period_cells = tuple(
            WholeSchoolPeriodCell(
                period=period,
                column=index + 2,
                is_break=period.kind == PeriodKind.BREAK,
            )
            for index, period in enumerate(periods)
        )
        rows = tuple(
            self._day_row(day, schedule.get(day, []), periods, period_indexes, period_cells)
            for day in Day
        )
        return WholeSchoolTimetable(periods=tuple(periods), rows=rows)

    def _day_row(
        self,
        day: Day,
        lessons: list[ScheduledLesson],
        periods: list[Period],
        period_indexes: dict[int, int],
        period_cells: tuple[WholeSchoolPeriodCell, ...],
    ) -> WholeSchoolDayRow:
        occupied_by_lane: list[set[int]] = []
        cards: list[WholeSchoolLessonCard] = []

        for lesson in lessons:
            start_index = period_indexes[lesson.start_period.id]
            occupied = {lesson.start_period.id}
            lane = self._available_lane(occupied, occupied_by_lane)
            cards.append(
                WholeSchoolLessonCard(
                    lesson_id=lesson.id,
                    subject=self.short_subject(lesson.subject_name),
                    teacher=self.short_teacher(lesson.teacher_name),
                    student_group=lesson.student_group_name,
                    column=start_index + 2,
                    lane=lane + 1,
                )
            )

        return WholeSchoolDayRow(
            day=day,
            period_cells=period_cells,
            cards=tuple(cards),
            lane_count=max(1, len(occupied_by_lane)),
        )

    @staticmethod
    def _available_lane(occupied: set[int], occupied_by_lane: list[set[int]]) -> int:
        for index, lane_occupied in enumerate(occupied_by_lane):
            if not occupied & lane_occupied:
                lane_occupied.update(occupied)
                return index
        occupied_by_lane.append(set(occupied))
        return len(occupied_by_lane) - 1

    @classmethod
    def short_subject(cls, name: str) -> str:
        return cls.SUBJECT_ALIASES.get(name.strip().casefold(), name.strip())

    @classmethod
    def short_teacher(cls, name: str) -> str:
        display_name = name.strip()
        lowered_name = display_name.casefold()
        for prefix in cls.TEACHER_PREFIXES:
            if lowered_name.startswith(prefix):
                shortened = display_name[len(prefix) :].strip()
                return shortened or display_name
        return display_name
