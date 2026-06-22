import pytest

from app.application.services.conflicts import ConflictService
from app.application.services.schedules import ScheduleService
from app.domain.exceptions import ScheduleConflictError
from app.domain.models import Lesson, TimeSlot
from app.domain.policies import ExistingLesson, LessonRequest


class FakeLessonRepository:
    def __init__(self, existing=None):
        self.existing = existing or []
        self.created = []
        self.updated = []

    def list_potential_conflicts(self, request):
        return self.existing

    def create_lesson(self, lesson):
        saved = Lesson(
            lesson.teacher_id,
            lesson.subject_id,
            lesson.room_id,
            lesson.student_group_id,
            lesson.time_slot_id,
            id=1,
        )
        self.created.append(saved)
        return saved

    def update_lesson(self, lesson):
        self.updated.append(lesson)
        return lesson

    def list_lessons_for_teacher(self, teacher_id):
        return [lesson for lesson in self.existing if lesson.teacher_id == teacher_id]

    def list_lessons_for_room(self, room_id):
        return [lesson for lesson in self.existing if lesson.room_id == room_id]

    def list_lessons_for_student_group(self, student_group_id):
        return [lesson for lesson in self.existing if lesson.student_group_id == student_group_id]


def existing_lesson(lesson_id, day, start, end, teacher_id=1, room_id=1, student_group_id=1):
    return ExistingLesson(
        id=lesson_id,
        teacher_id=teacher_id,
        room_id=room_id,
        student_group_id=student_group_id,
        time_slot=TimeSlot(day, start, end),
    )


def build_service(repository):
    return ScheduleService(repository, ConflictService(repository))


def test_schedule_service_creates_lesson_when_no_conflict():
    repository = FakeLessonRepository()
    service = build_service(repository)
    lesson = Lesson(teacher_id=1, subject_id=1, room_id=1, student_group_id=1, time_slot_id=1)
    request = LessonRequest(1, 1, 1, TimeSlot("Monday", 9, 10))

    saved = service.create_lesson(lesson, request)

    assert saved.id == 1
    assert len(repository.created) == 1


def test_schedule_service_rejects_conflicting_lesson():
    repository = FakeLessonRepository([existing_lesson(1, "Monday", 9, 10, teacher_id=5)])
    service = build_service(repository)

    with pytest.raises(ScheduleConflictError):
        service.create_lesson(
            Lesson(5, 1, 2, 3, 4),
            LessonRequest(5, 2, 3, TimeSlot("Monday", 9, 10)),
        )

    assert repository.created == []


def test_schedule_service_updates_lesson_when_no_conflict():
    repository = FakeLessonRepository()
    service = build_service(repository)
    lesson = Lesson(teacher_id=1, subject_id=1, room_id=1, student_group_id=1, time_slot_id=1, id=2)
    request = LessonRequest(1, 1, 1, TimeSlot("Monday", 9, 10), lesson_id=2)

    updated = service.update_lesson(lesson, request)

    assert updated.id == 2
    assert repository.updated == [lesson]


def test_weekly_schedule_groups_lessons_by_day_and_sorts_by_start_time():
    repository = FakeLessonRepository()
    service = build_service(repository)
    late = existing_lesson(1, "Monday", 11, 12)
    early = existing_lesson(2, "Monday", 9, 10)
    tuesday = existing_lesson(3, "Tuesday", 9, 10)

    schedule = service.weekly_schedule([late, tuesday, early])

    assert schedule["Monday"] == [early, late]
    assert schedule["Tuesday"] == [tuesday]


def test_weekly_schedule_uses_weekday_order():
    repository = FakeLessonRepository()
    service = build_service(repository)
    friday = existing_lesson(1, "Friday", 9, 10)
    monday = existing_lesson(2, "Monday", 9, 10)
    wednesday = existing_lesson(3, "Wednesday", 9, 10)

    schedule = service.weekly_schedule([friday, monday, wednesday])

    assert list(schedule) == ["Monday", "Wednesday", "Friday"]


def test_schedule_service_filters_by_teacher():
    repository = FakeLessonRepository(
        [
            existing_lesson(1, "Monday", 9, 10, teacher_id=4),
            existing_lesson(2, "Monday", 10, 11, teacher_id=5),
        ]
    )
    service = build_service(repository)

    schedule = service.schedule_for_teacher(4)

    assert [lesson.id for lesson in schedule["Monday"]] == [1]


def test_schedule_service_filters_by_room():
    repository = FakeLessonRepository(
        [
            existing_lesson(1, "Monday", 9, 10, room_id=4),
            existing_lesson(2, "Monday", 10, 11, room_id=5),
        ]
    )
    service = build_service(repository)

    schedule = service.schedule_for_room(4)

    assert [lesson.id for lesson in schedule["Monday"]] == [1]


def test_schedule_service_filters_by_student_group():
    repository = FakeLessonRepository(
        [
            existing_lesson(1, "Monday", 9, 10, student_group_id=4),
            existing_lesson(2, "Monday", 10, 11, student_group_id=5),
        ]
    )
    service = build_service(repository)

    schedule = service.schedule_for_student_group(4)

    assert [lesson.id for lesson in schedule["Monday"]] == [1]
