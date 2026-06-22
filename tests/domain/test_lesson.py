from app.domain.models import Lesson


def test_lesson_stores_assignment_ids():
    lesson = Lesson(
        teacher_id=1,
        subject_id=2,
        room_id=3,
        student_group_id=4,
        time_slot_id=5,
    )

    assert lesson.teacher_id == 1
    assert lesson.subject_id == 2
    assert lesson.room_id == 3
    assert lesson.student_group_id == 4
    assert lesson.time_slot_id == 5


def test_lesson_id_is_optional_for_new_lessons():
    lesson = Lesson(1, 2, 3, 4, 5)

    assert lesson.id is None


def test_lesson_can_represent_existing_lesson():
    lesson = Lesson(1, 2, 3, 4, 5, id=99)

    assert lesson.id == 99
