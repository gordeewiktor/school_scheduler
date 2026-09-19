from collections.abc import Iterable
from dataclasses import dataclass

from app.application.ports.repositories import LessonRepository, ScheduledLesson
from app.application.services.conflicts import ConflictService
from app.domain.exceptions import (
    CrossSchoolLessonError,
    InvalidLessonPlacementError,
    ScheduleConflictError,
    SchoolAuthorizationError,
)
from app.domain.models import Day, Lesson, Period, PeriodKind, Teacher
from app.domain.policies import LessonRequest


@dataclass(frozen=True, slots=True)
class TimetableCell:
    period: Period
    kind: str
    lesson: ScheduledLesson | None = None


@dataclass(frozen=True, slots=True)
class TimetableRow:
    day: Day
    cells: list[TimetableCell]


@dataclass(frozen=True, slots=True)
class StaffScheduleAssignment:
    teacher_id: int
    teacher_name: str
    subject_name: str
    student_group_name: str
    room_name: str
    regular_teacher_name: str = ""
    has_substitution_conflict: bool = False


@dataclass(frozen=True, slots=True)
class StaffScheduleSlot:
    day: Day
    period: Period
    teaching: tuple[StaffScheduleAssignment, ...]
    substitutions: tuple[StaffScheduleAssignment, ...]
    free_teachers: tuple[Teacher, ...]
    unassigned_substitutions: tuple[StaffScheduleAssignment, ...]

    @property
    def is_break(self) -> bool:
        return self.period.kind == PeriodKind.BREAK


@dataclass(frozen=True, slots=True)
class StaffScheduleRow:
    day: Day
    slots: tuple[StaffScheduleSlot, ...]


@dataclass(frozen=True, slots=True)
class StaffSchedule:
    periods: tuple[Period, ...]
    rows: tuple[StaffScheduleRow, ...]


class ScheduleService:
    DAY_ORDER = list(Day)

    def __init__(
        self,
        lesson_repository: LessonRepository,
        conflict_service: ConflictService,
    ) -> None:
        self.lesson_repository = lesson_repository
        self.conflict_service = conflict_service

    def create_lesson(self, lesson: Lesson, school_id: int | None = None) -> Lesson:
        request = self._request_for(lesson, school_id=school_id)
        self._raise_for_conflicts(request)
        return self.lesson_repository.create_lesson(lesson)

    def update_lesson(self, lesson: Lesson, school_id: int | None = None) -> Lesson:
        if lesson.id is None:
            raise ValueError("Lesson id is required for updates.")
        request = self._request_for(lesson, school_id=school_id)
        self._raise_for_conflicts(request)
        return self.lesson_repository.update_lesson(lesson)

    def _request_for(self, lesson: Lesson, school_id: int | None = None) -> LessonRequest:
        period = self.lesson_repository.get_period(lesson.start_period_id)
        if period is None:
            raise InvalidLessonPlacementError("Choose a configured period.")
        if not period.accepts_lessons:
            raise InvalidLessonPlacementError("Lessons cannot occupy break periods.")
        self._ensure_same_school(lesson, period, school_id=school_id)
        return LessonRequest(
            teacher_id=lesson.teacher_id,
            room_id=lesson.room_id,
            student_group_id=lesson.student_group_id,
            day=lesson.day,
            academic_year_id=period.academic_year_id,
            period_id=period.id,
            planned_substitute_id=lesson.planned_substitute_id,
            lesson_id=lesson.id,
        )

    def _ensure_same_school(
        self, lesson: Lesson, period: Period, school_id: int | None = None
    ) -> None:
        school_ids = self.lesson_repository.get_resource_school_ids(
            teacher_id=lesson.teacher_id,
            room_id=lesson.room_id,
            subject_id=lesson.subject_id,
            student_group_id=lesson.student_group_id,
            period_id=period.id,
            planned_substitute_id=lesson.planned_substitute_id,
        )
        distinct_schools = {
            school_ids.teacher_school_id,
            school_ids.room_school_id,
            school_ids.subject_school_id,
            school_ids.student_group_school_id,
            school_ids.period_school_id,
        }
        if school_ids.planned_substitute_school_id is not None:
            distinct_schools.add(school_ids.planned_substitute_school_id)
        if len(distinct_schools) > 1:
            raise CrossSchoolLessonError(
                "Teacher, room, subject, student group, and planned substitute "
                "must all belong to the same school as the lesson's academic year."
            )
        if school_id is not None and school_ids.period_school_id != school_id:
            raise SchoolAuthorizationError(
                "This lesson does not belong to the given school."
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
        for day in self.DAY_ORDER:
            lanes: list[list[ScheduledLesson]] = []
            occupied_by_lane: list[set[int]] = []
            for lesson in schedule.get(day, []):
                occupied = {lesson.start_period.id}
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
                    )
                )
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

    def staff_schedule(self, academic_year_id: int) -> StaffSchedule:
        periods = self.periods(academic_year_id)
        school_id = self.lesson_repository.get_academic_year_school_id(academic_year_id)
        teachers = sorted(
            self.lesson_repository.list_teachers(school_id),
            key=lambda teacher: (teacher.name.casefold(), teacher.id),
        )
        lessons_by_slot: dict[tuple[Day, int], list[ScheduledLesson]] = {}
        for lesson in self.lesson_repository.list_lessons(academic_year_id):
            lessons_by_slot.setdefault((lesson.day, lesson.start_period.id), []).append(
                lesson
            )

        return StaffSchedule(
            periods=tuple(periods),
            rows=tuple(
                StaffScheduleRow(
                    day=day,
                    slots=tuple(
                        self._staff_schedule_slot(
                            day,
                            period,
                            lessons_by_slot.get((day, period.id), []),
                            teachers,
                        )
                        for period in periods
                    ),
                )
                for day in self.DAY_ORDER
            ),
        )

    @staticmethod
    def _staff_schedule_slot(
        day: Day,
        period: Period,
        lessons: list[ScheduledLesson],
        teachers: list[Teacher],
    ) -> StaffScheduleSlot:
        teaching_teacher_ids = {lesson.teacher_id for lesson in lessons}
        substitution_teacher_ids = [
            lesson.planned_substitute_id
            for lesson in lessons
            if lesson.planned_substitute_id is not None
        ]
        substitution_counts = {
            teacher_id: substitution_teacher_ids.count(teacher_id)
            for teacher_id in substitution_teacher_ids
        }
        teaching = tuple(
            sorted(
                (
                    StaffScheduleAssignment(
                        teacher_id=lesson.teacher_id,
                        teacher_name=lesson.teacher_name,
                        subject_name=lesson.subject_name,
                        student_group_name=lesson.student_group_name,
                        room_name=lesson.room_name,
                    )
                    for lesson in lessons
                ),
                key=lambda assignment: (assignment.teacher_name.casefold(), assignment.teacher_id),
            )
        )
        substitutions = tuple(
            sorted(
                (
                    StaffScheduleAssignment(
                        teacher_id=lesson.planned_substitute_id,
                        teacher_name=lesson.planned_substitute_name,
                        subject_name=lesson.subject_name,
                        student_group_name=lesson.student_group_name,
                        room_name=lesson.room_name,
                        regular_teacher_name=lesson.teacher_name,
                        has_substitution_conflict=(
                            substitution_counts[lesson.planned_substitute_id] > 1
                        ),
                    )
                    for lesson in lessons
                    if lesson.planned_substitute_id is not None
                ),
                key=lambda assignment: (assignment.teacher_name.casefold(), assignment.teacher_id),
            )
        )
        unassigned_substitutions = tuple(
            sorted(
                (
                    StaffScheduleAssignment(
                        teacher_id=lesson.teacher_id,
                        teacher_name=lesson.teacher_name,
                        subject_name=lesson.subject_name,
                        student_group_name=lesson.student_group_name,
                        room_name=lesson.room_name,
                    )
                    for lesson in lessons
                    if lesson.planned_substitute_id is None
                ),
                key=lambda assignment: (assignment.teacher_name.casefold(), assignment.teacher_id),
            )
        )
        occupied_teacher_ids = teaching_teacher_ids | set(substitution_teacher_ids)
        free_teachers = tuple(
            teacher for teacher in teachers if teacher.id not in occupied_teacher_ids
        )
        return StaffScheduleSlot(
            day=day,
            period=period,
            teaching=teaching,
            substitutions=substitutions,
            free_teachers=free_teachers,
            unassigned_substitutions=unassigned_substitutions,
        )
