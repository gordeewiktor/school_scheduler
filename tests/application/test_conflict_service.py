from app.application.services.conflicts import ConflictService
from app.domain.models import TimeSlot
from app.domain.policies import ExistingLesson, LessonRequest


class FakeLessonRepository:
    def __init__(self, lessons):
        self.lessons = lessons

    def list_potential_conflicts(self, request):
        return self.lessons


def lesson(
    lesson_id=1,
    teacher_id=1,
    room_id=1,
    student_group_id=1,
    time_slot=None,
):
    return ExistingLesson(
        id=lesson_id,
        teacher_id=teacher_id,
        room_id=room_id,
        student_group_id=student_group_id,
        time_slot=time_slot or TimeSlot("Monday", 9, 10),
    )


def request(
    teacher_id=2,
    room_id=2,
    student_group_id=2,
    time_slot=None,
    lesson_id=None,
):
    return LessonRequest(
        teacher_id=teacher_id,
        room_id=room_id,
        student_group_id=student_group_id,
        time_slot=time_slot or TimeSlot("Monday", 9, 10),
        lesson_id=lesson_id,
    )


def test_conflict_service_detects_teacher_conflict():
    service = ConflictService(FakeLessonRepository([lesson(teacher_id=7)]))

    conflicts = service.find_conflicts(request(teacher_id=7))

    assert [conflict.field for conflict in conflicts] == ["teacher"]


def test_conflict_service_detects_room_conflict():
    service = ConflictService(FakeLessonRepository([lesson(room_id=7)]))

    conflicts = service.find_conflicts(request(room_id=7))

    assert [conflict.field for conflict in conflicts] == ["room"]


def test_conflict_service_detects_student_group_conflict():
    service = ConflictService(FakeLessonRepository([lesson(student_group_id=7)]))

    conflicts = service.find_conflicts(request(student_group_id=7))

    assert [conflict.field for conflict in conflicts] == ["student_group"]


def test_conflict_service_detects_multiple_conflicts():
    service = ConflictService(
        FakeLessonRepository([lesson(teacher_id=7, room_id=8, student_group_id=9)])
    )

    conflicts = service.find_conflicts(request(teacher_id=7, room_id=8, student_group_id=9))

    assert {conflict.field for conflict in conflicts} == {"teacher", "room", "student_group"}


def test_conflict_service_ignores_non_overlapping_time_slot():
    service = ConflictService(FakeLessonRepository([lesson(teacher_id=7)]))

    conflicts = service.find_conflicts(request(teacher_id=7, time_slot=TimeSlot("Monday", 10, 11)))

    assert conflicts == []


def test_conflict_service_ignores_different_day():
    service = ConflictService(FakeLessonRepository([lesson(teacher_id=7)]))

    conflicts = service.find_conflicts(request(teacher_id=7, time_slot=TimeSlot("Tuesday", 9, 10)))

    assert conflicts == []


def test_conflict_service_ignores_same_lesson_when_updating():
    service = ConflictService(FakeLessonRepository([lesson(lesson_id=12, teacher_id=7)]))

    conflicts = service.find_conflicts(request(teacher_id=7, lesson_id=12))

    assert conflicts == []


def test_conflict_service_reports_has_conflicts():
    service = ConflictService(FakeLessonRepository([lesson(teacher_id=7)]))

    assert service.has_conflicts(request(teacher_id=7))
