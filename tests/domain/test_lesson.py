import pytest

from app.domain.exceptions import InvalidLessonPlacementError
from app.domain.models import Day, Lesson


def test_lesson_stores_manual_placement():
    lesson = Lesson(1, 2, 3, 4, Day.MONDAY, 5, duration=2, notes="Lab")

    assert lesson.teacher_id == 1
    assert lesson.subject_id == 2
    assert lesson.room_id == 3
    assert lesson.student_group_id == 4
    assert lesson.day == Day.MONDAY
    assert lesson.start_period_id == 5
    assert lesson.duration == 2
    assert lesson.notes == "Lab"
    assert lesson.id is None


def test_lesson_can_represent_existing_lesson():
    lesson = Lesson(1, 2, 3, 4, Day.FRIDAY, 5, id=99)
    assert lesson.id == 99


def test_lesson_requires_positive_duration():
    with pytest.raises(InvalidLessonPlacementError):
        Lesson(1, 2, 3, 4, Day.MONDAY, 5, duration=0)
