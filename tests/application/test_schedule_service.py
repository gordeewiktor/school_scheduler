from datetime import time

import pytest

from app.application.ports.repositories import ScheduledLesson
from app.application.services.conflicts import ConflictService
from app.application.services.schedules import ScheduleService
from app.domain.exceptions import InvalidLessonPlacementError, ScheduleConflictError
from app.domain.models import Day, Lesson, Period, PeriodKind, Teacher
from app.domain.policies import ExistingLesson


def make_period(order, kind=PeriodKind.LESSON):
    return Period(order, 1, f"Period {order}", order, time(8 + order), time(9 + order), kind)


def scheduled(lesson_id, day=Day.MONDAY, order=1, duration=1, teacher_id=1, room_id=1, group_id=1):
    return ScheduledLesson(
        id=lesson_id,
        teacher_id=teacher_id,
        teacher_name=f"Teacher {teacher_id}",
        subject_name="Math",
        room_id=room_id,
        room_name=f"Room {room_id}",
        student_group_id=group_id,
        student_group_name=f"Group {group_id}",
        day=day,
        start_period=make_period(order),
        duration=duration,
    )


class FakeLessonRepository:
    def __init__(self, periods=None, conflicts=None, lessons=None, teachers=None):
        self.periods = periods or [make_period(1), make_period(2), make_period(3)]
        self.conflicts = conflicts or []
        self.lessons = lessons or []
        self.teachers = teachers or []
        self.created = []
        self.updated = []

    def list_teachers(self):
        return self.teachers

    def periods_for_placement(self, start_period_id, duration):
        start_index = next(
            (index for index, period in enumerate(self.periods) if period.id == start_period_id),
            None,
        )
        if start_index is None:
            return []
        return self.periods[start_index : start_index + duration]

    def list_periods(self, academic_year_id):
        return [period for period in self.periods if period.academic_year_id == academic_year_id]

    def list_potential_conflicts(self, request):
        return self.conflicts

    def create_lesson(self, lesson):
        saved = Lesson(
            lesson.teacher_id, lesson.subject_id, lesson.room_id, lesson.student_group_id,
            lesson.day, lesson.start_period_id, lesson.duration, lesson.notes, id=1
        )
        self.created.append(saved)
        return saved

    def update_lesson(self, lesson):
        self.updated.append(lesson)
        return lesson

    def list_lessons(self, academic_year_id):
        return self.lessons

    def list_lessons_starting_at(self, academic_year_id, day, period_id):
        return [
            item
            for item in self.lessons
            if item.start_period.academic_year_id == academic_year_id
            and item.day == day
            and item.start_period.id == period_id
        ]

    def list_lessons_for_teacher(self, teacher_id, academic_year_id):
        return [item for item in self.lessons if item.teacher_id == teacher_id]

    def list_lessons_for_room(self, room_id, academic_year_id):
        return [item for item in self.lessons if item.room_id == room_id]

    def list_lessons_for_student_group(self, student_group_id, academic_year_id):
        return [item for item in self.lessons if item.student_group_id == student_group_id]


def build_service(repository):
    return ScheduleService(repository, ConflictService(repository))


def command(**overrides):
    values = dict(
        teacher_id=1, subject_id=1, room_id=1, student_group_id=1,
        day=Day.MONDAY, start_period_id=1, duration=1
    )
    values.update(overrides)
    return Lesson(**values)


def test_service_creates_multi_period_lesson_when_valid():
    repository = FakeLessonRepository()
    saved = build_service(repository).create_lesson(command(duration=2, notes="Double"))
    assert saved.id == 1
    assert saved.duration == 2
    assert saved.notes == "Double"


def test_service_rejects_break_in_occupied_periods():
    repository = FakeLessonRepository([make_period(1), make_period(2, PeriodKind.BREAK)])
    with pytest.raises(InvalidLessonPlacementError, match="break"):
        build_service(repository).create_lesson(command(duration=2))
    assert repository.created == []


def test_service_rejects_lesson_past_last_period():
    repository = FakeLessonRepository([make_period(1)])
    with pytest.raises(InvalidLessonPlacementError, match="beyond"):
        build_service(repository).create_lesson(command(duration=2))


def test_duration_uses_period_sequence_not_numeric_order_values():
    first = make_period(1)
    second = make_period(2)
    first = Period(first.id, 1, first.name, 10, first.start_time, first.end_time, first.kind)
    second = Period(second.id, 1, second.name, 20, second.start_time, second.end_time, second.kind)
    repository = FakeLessonRepository([first, second])
    saved = build_service(repository).create_lesson(command(duration=2))
    assert saved.duration == 2


def test_service_rejects_conflicting_lesson():
    existing = ExistingLesson(1, 5, 2, 3, Day.MONDAY, 1, frozenset({1, 2}))
    repository = FakeLessonRepository(conflicts=[existing])
    with pytest.raises(ScheduleConflictError):
        build_service(repository).create_lesson(command(teacher_id=5, duration=2))
    assert repository.created == []


def test_service_updates_lesson_and_excludes_it_from_conflicts():
    existing = ExistingLesson(7, 1, 1, 1, Day.MONDAY, 1, frozenset({1}))
    repository = FakeLessonRepository(conflicts=[existing])
    lesson = command(id=7)
    assert build_service(repository).update_lesson(lesson) == lesson
    assert repository.updated == [lesson]


def test_weekly_schedule_orders_days_and_start_periods():
    lessons = [
        scheduled(1, Day.FRIDAY, 1),
        scheduled(2, Day.MONDAY, 2),
        scheduled(3, Day.MONDAY, 1),
    ]
    schedule = build_service(FakeLessonRepository()).weekly_schedule(lessons)
    assert list(schedule) == [Day.MONDAY, Day.FRIDAY]
    assert [item.id for item in schedule[Day.MONDAY]] == [3, 2]


@pytest.mark.parametrize(
    ("method", "identifier", "expected"),
    [
        ("schedule_for_teacher", 4, 1),
        ("schedule_for_room", 5, 2),
        ("schedule_for_student_group", 6, 3),
    ],
)
def test_schedule_projections_filter_same_lesson_data(method, identifier, expected):
    lessons = [
        scheduled(1, teacher_id=4),
        scheduled(2, room_id=5),
        scheduled(3, group_id=6),
    ]
    service = build_service(FakeLessonRepository(lessons=lessons))
    result = getattr(service, method)(identifier, 1)
    assert [item.id for item in result[Day.MONDAY]] == [expected]


def test_timetable_rows_include_breaks_and_multi_period_colspan():
    periods = [make_period(1), make_period(2), make_period(3, PeriodKind.BREAK)]
    lesson = scheduled(1, duration=2)
    service = build_service(FakeLessonRepository(periods=periods))
    rows = service.timetable_rows({Day.MONDAY: [lesson]}, periods)
    monday = rows[0]
    assert monday.cells[0].kind == "lesson"
    assert monday.cells[0].colspan == 2
    assert monday.cells[1].kind == "break"


def test_available_teachers_excludes_teachers_with_lesson_starting_in_selected_period():
    teachers = [
        Teacher(id=1, name="Ada"),
        Teacher(id=2, name="Grace"),
        Teacher(id=3, name="Katherine"),
    ]
    lessons = [
        scheduled(1, teacher_id=1, day=Day.MONDAY, order=1),
        scheduled(2, teacher_id=2, day=Day.MONDAY, order=2),
        scheduled(3, teacher_id=3, day=Day.TUESDAY, order=1),
    ]
    service = build_service(FakeLessonRepository(lessons=lessons, teachers=teachers))

    result = service.available_teachers(1, Day.MONDAY, 1)

    assert [teacher.name for teacher in result] == ["Grace", "Katherine"]


def test_available_teachers_returns_all_teachers_when_schedule_is_empty():
    teachers = [Teacher(id=1, name="Ada"), Teacher(id=2, name="Grace")]
    service = build_service(FakeLessonRepository(teachers=teachers))

    result = service.available_teachers(1, Day.MONDAY, 1)

    assert result == teachers
