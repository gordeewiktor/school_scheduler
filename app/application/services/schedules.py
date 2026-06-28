from collections.abc import Iterable
from dataclasses import dataclass

from app.application.ports.repositories import LessonRepository, ScheduledLesson
from app.application.services.conflicts import ConflictService
from app.domain.exceptions import InvalidLessonPlacementError, ScheduleConflictError
from app.domain.models import Day, Lesson, Period, PeriodKind
from app.domain.policies import LessonRequest


@dataclass(frozen=True, slots=True)
class TimetableCell:
    period: Period
    kind: str
    lesson: ScheduledLesson | None = None
    colspan: int = 1


@dataclass(frozen=True, slots=True)
class TimetableRow:
    day: Day
    cells: list[TimetableCell]


class ScheduleService:
    DAY_ORDER = list(Day)

    def __init__(
        self,
        lesson_repository: LessonRepository,
        conflict_service: ConflictService,
    ) -> None:
        self.lesson_repository = lesson_repository
        self.conflict_service = conflict_service

    def create_lesson(self, lesson: Lesson) -> Lesson:
        request = self._request_for(lesson)
        self._raise_for_conflicts(request)
        return self.lesson_repository.create_lesson(lesson)

    def update_lesson(self, lesson: Lesson) -> Lesson:
        if lesson.id is None:
            raise ValueError("Lesson id is required for updates.")
        request = self._request_for(lesson)
        self._raise_for_conflicts(request)
        return self.lesson_repository.update_lesson(lesson)

    def _request_for(self, lesson: Lesson) -> LessonRequest:
        periods = self.lesson_repository.periods_for_placement(
            lesson.start_period_id, lesson.duration
        )
        if len(periods) != lesson.duration:
            raise InvalidLessonPlacementError(
                "The lesson extends beyond the configured periods."
            )
        if any(not period.accepts_lessons for period in periods):
            raise InvalidLessonPlacementError("Lessons cannot occupy break periods.")
        return LessonRequest(
            teacher_id=lesson.teacher_id,
            room_id=lesson.room_id,
            student_group_id=lesson.student_group_id,
            day=lesson.day,
            academic_year_id=periods[0].academic_year_id,
            occupied_period_ids=frozenset(period.id for period in periods),
            lesson_id=lesson.id,
        )

    def _raise_for_conflicts(self, request: LessonRequest) -> None:
        conflicts = self.conflict_service.find_conflicts(request)
        if conflicts:
            raise ScheduleConflictError(conflicts)

    def weekly_schedule(
        self, lessons: Iterable[ScheduledLesson]
    ) -> dict[Day, list[ScheduledLesson]]:
        grouped: dict[Day, list[ScheduledLesson]] = {}
        for lesson in lessons:
            grouped.setdefault(lesson.day, []).append(lesson)
        return {
            day: sorted(day_lessons, key=lambda lesson: lesson.start_period.order)
            for day, day_lessons in sorted(
                grouped.items(), key=lambda item: self.DAY_ORDER.index(item[0])
            )
        }

    def periods(self, academic_year_id: int) -> list[Period]:
        return self.lesson_repository.list_periods(academic_year_id)

    def timetable_rows(
        self,
        schedule: dict[Day, list[ScheduledLesson]],
        periods: list[Period],
    ) -> list[TimetableRow]:
        rows: list[TimetableRow] = []
        period_index = {period.id: index for index, period in enumerate(periods)}
        for day in self.DAY_ORDER:
            lanes: list[list[ScheduledLesson]] = []
            occupied_by_lane: list[set[int]] = []
            for lesson in schedule.get(day, []):
                start_index = period_index[lesson.start_period.id]
                occupied = {
                    period.id for period in periods[start_index : start_index + lesson.duration]
                }
                for index, lane_occupied in enumerate(occupied_by_lane):
                    if not occupied & lane_occupied:
                        lanes[index].append(lesson)
                        lane_occupied.update(occupied)
                        break
                else:
                    lanes.append([lesson])
                    occupied_by_lane.append(occupied)
            for lane in lanes or [[]]:
                rows.append(TimetableRow(day=day, cells=self._cells_for_lane(lane, periods)))
        return rows

    @staticmethod
    def _cells_for_lane(
        lessons: list[ScheduledLesson], periods: list[Period]
    ) -> list[TimetableCell]:
        lessons_by_order = {lesson.start_period.order: lesson for lesson in lessons}
        cells: list[TimetableCell] = []
        index = 0
        while index < len(periods):
            period = periods[index]
            lesson = lessons_by_order.get(period.order)
            if lesson is not None:
                cells.append(
                    TimetableCell(
                        period=period,
                        kind="lesson",
                        lesson=lesson,
                        colspan=lesson.duration,
                    )
                )
                index += lesson.duration
            else:
                cells.append(
                    TimetableCell(
                        period=period,
                        kind="break" if period.kind == PeriodKind.BREAK else "empty",
                    )
                )
                index += 1
        return cells

    def schedule(self, academic_year_id: int) -> dict[Day, list[ScheduledLesson]]:
        return self.weekly_schedule(self.lesson_repository.list_lessons(academic_year_id))

    def schedule_for_teacher(
        self, teacher_id: int, academic_year_id: int
    ) -> dict[Day, list[ScheduledLesson]]:
        return self.weekly_schedule(
            self.lesson_repository.list_lessons_for_teacher(teacher_id, academic_year_id)
        )

    def schedule_for_room(
        self, room_id: int, academic_year_id: int
    ) -> dict[Day, list[ScheduledLesson]]:
        return self.weekly_schedule(
            self.lesson_repository.list_lessons_for_room(room_id, academic_year_id)
        )

    def schedule_for_student_group(
        self, student_group_id: int, academic_year_id: int
    ) -> dict[Day, list[ScheduledLesson]]:
        return self.weekly_schedule(
            self.lesson_repository.list_lessons_for_student_group(
                student_group_id, academic_year_id
            )
        )
