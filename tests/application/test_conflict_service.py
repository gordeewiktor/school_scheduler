from app.application.services.conflicts import ConflictService
from app.domain.models import Day
from app.domain.policies import ExistingLesson, LessonRequest


class FakeLessonRepository:
    def __init__(self, lessons):
        self.lessons = lessons

    def list_potential_conflicts(self, request):
        return self.lessons


def lesson(lesson_id=1, teacher_id=1, room_id=1, student_group_id=1, period_id=1):
    return ExistingLesson(
        id=lesson_id,
        teacher_id=teacher_id,
        room_id=room_id,
        student_group_id=student_group_id,
        day=Day.MONDAY,
        academic_year_id=1,
        period_id=period_id,
    )


def request(teacher_id=2, room_id=2, student_group_id=2, period_id=1, lesson_id=None):
    return LessonRequest(
        teacher_id=teacher_id,
        room_id=room_id,
        student_group_id=student_group_id,
        day=Day.MONDAY,
        academic_year_id=1,
        period_id=period_id,
        lesson_id=lesson_id,
    )


def test_conflict_service_detects_teacher_room_and_group_conflicts():
    service = ConflictService(
        FakeLessonRepository([lesson(teacher_id=7, room_id=8, student_group_id=9)])
    )
    conflicts = service.find_conflicts(request(teacher_id=7, room_id=8, student_group_id=9))
    assert {conflict.field for conflict in conflicts} == {"teacher", "room", "student_group"}


def test_conflict_service_ignores_consecutive_periods():
    service = ConflictService(FakeLessonRepository([lesson(teacher_id=7, period_id=1)]))
    assert service.find_conflicts(request(teacher_id=7, period_id=2)) == []


def test_conflict_service_ignores_different_day_or_year():
    different_day = ExistingLesson(1, 7, 1, 1, Day.TUESDAY, 1, 1)
    different_year = ExistingLesson(2, 7, 1, 1, Day.MONDAY, 2, 1)
    service = ConflictService(FakeLessonRepository([different_day, different_year]))
    assert service.find_conflicts(request(teacher_id=7)) == []


def test_conflict_service_ignores_same_lesson_when_updating():
    service = ConflictService(FakeLessonRepository([lesson(lesson_id=12, teacher_id=7)]))
    assert service.find_conflicts(request(teacher_id=7, lesson_id=12)) == []


def test_conflict_service_reports_has_conflicts():
    service = ConflictService(FakeLessonRepository([lesson(teacher_id=7)]))
    assert service.has_conflicts(request(teacher_id=7))
