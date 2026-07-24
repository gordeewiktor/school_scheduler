from dataclasses import dataclass

from django.urls import reverse

from app.application.ports.repositories import ScheduledLesson
from app.application.services.schedules import TimetableRow
from app.domain.models import Day, Period, PeriodKind


SUBJECT_PALETTE_SIZE = 10


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
    planned_substitute: str
    edit_url: str
    color_class: str
    detail_title: str
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


class LessonDisplayMixin:
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

    @staticmethod
    def subject_color_class(subject_name: str) -> str:
        normalized_name = subject_name.strip().casefold()
        color_index = sum(ord(character) for character in normalized_name)
        return f"subject-color-{color_index % SUBJECT_PALETTE_SIZE}"

    @staticmethod
    def detail_title(lesson: ScheduledLesson, *, include_room: bool = True) -> str:
        details = [
            lesson.subject_name,
            f"Teacher: {lesson.teacher_name}",
            f"Group: {lesson.student_group_name}",
        ]
        if include_room:
            details.append(f"Room: {lesson.room_name}")
        if lesson.planned_substitute_name:
            details.append(f"Substitute: {lesson.planned_substitute_name}")
        if lesson.notes:
            details.append(f"Notes: {lesson.notes}")
        return "\n".join(details)


class WholeSchoolTimetableRenderer(LessonDisplayMixin):
    """Builds the compact, card-based presentation model for the master timetable."""

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
                    planned_substitute=self.short_teacher(
                        lesson.planned_substitute_name
                    ),
                    edit_url=reverse("lesson-update", args=[lesson.id]),
                    color_class=self.subject_color_class(lesson.subject_name),
                    detail_title=self.detail_title(lesson, include_room=False),
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


@dataclass(frozen=True, slots=True)
class FocusedLessonDetail:
    label: str
    value: str


@dataclass(frozen=True, slots=True)
class FocusedLessonCard:
    lesson_id: int
    subject: str
    details: tuple[FocusedLessonDetail, ...]
    planned_substitute: str
    edit_url: str
    color_class: str
    detail_title: str


@dataclass(frozen=True, slots=True)
class FocusedTimetableCell:
    period: Period
    kind: str
    card: FocusedLessonCard | None = None


@dataclass(frozen=True, slots=True)
class FocusedTimetableRow:
    day: Day
    cells: tuple[FocusedTimetableCell, ...]


class FocusedTimetableRenderer(LessonDisplayMixin):
    """Adapts lesson cards to the currently selected timetable context."""

    DETAIL_LABELS_BY_VIEW = {
        "student_group": (("Teacher", "teacher_name"), ("Room", "room_name")),
        "teacher": (("Group", "student_group_name"), ("Room", "room_name")),
        "room": (("Teacher", "teacher_name"), ("Group", "student_group_name")),
    }

    def render(
        self,
        rows: list[TimetableRow],
        current_view: str,
    ) -> tuple[FocusedTimetableRow, ...]:
        return tuple(
            FocusedTimetableRow(
                day=row.day,
                cells=tuple(
                    FocusedTimetableCell(
                        period=cell.period,
                        kind=cell.kind,
                        card=(
                            self._card(cell.lesson, current_view)
                            if cell.lesson is not None
                            else None
                        ),
                    )
                    for cell in row.cells
                ),
            )
            for row in rows
        )

    def _card(
        self,
        lesson: ScheduledLesson,
        current_view: str,
    ) -> FocusedLessonCard:
        return FocusedLessonCard(
            lesson_id=lesson.id,
            subject=self.short_subject(lesson.subject_name),
            details=self._details(lesson, current_view),
            planned_substitute=self.short_teacher(lesson.planned_substitute_name),
            edit_url=reverse("lesson-update", args=[lesson.id]),
            color_class=self.subject_color_class(lesson.subject_name),
            detail_title=self.detail_title(lesson),
        )

    def _details(
        self,
        lesson: ScheduledLesson,
        current_view: str,
    ) -> tuple[FocusedLessonDetail, ...]:
        return tuple(
            FocusedLessonDetail(label=label, value=getattr(lesson, attribute))
            for label, attribute in self.DETAIL_LABELS_BY_VIEW.get(current_view, ())
        )
