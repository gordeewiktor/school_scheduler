from datetime import time

import pytest
from django.core.exceptions import ValidationError

from app.infrastructure.database.models import Lesson, Room, StudentGroup, Subject, Teacher, TimeSlot


@pytest.fixture
def school_data(db):
    return {
        "teacher": Teacher.objects.create(name="Ada Lovelace"),
        "other_teacher": Teacher.objects.create(name="Grace Hopper"),
        "room": Room.objects.create(name="A101"),
        "other_room": Room.objects.create(name="B202"),
        "subject": Subject.objects.create(name="Math"),
        "other_subject": Subject.objects.create(name="Science"),
        "group": StudentGroup.objects.create(name="Grade 1"),
        "other_group": StudentGroup.objects.create(name="Grade 2"),
        "slot": TimeSlot.objects.create(
            day="Monday",
            start_time=time(9, 0),
            end_time=time(10, 0),
        ),
        "overlap_slot": TimeSlot.objects.create(
            day="Monday",
            start_time=time(9, 30),
            end_time=time(10, 30),
        ),
        "later_slot": TimeSlot.objects.create(
            day="Monday",
            start_time=time(10, 0),
            end_time=time(11, 0),
        ),
    }


@pytest.mark.django_db
def test_django_lesson_save_rejects_teacher_conflict(school_data):
    Lesson.objects.create(
        teacher=school_data["teacher"],
        subject=school_data["subject"],
        room=school_data["room"],
        student_group=school_data["group"],
        time_slot=school_data["slot"],
    )

    with pytest.raises(ValidationError):
        Lesson.objects.create(
            teacher=school_data["teacher"],
            subject=school_data["other_subject"],
            room=school_data["other_room"],
            student_group=school_data["other_group"],
            time_slot=school_data["overlap_slot"],
        )


@pytest.mark.django_db
def test_django_lesson_save_allows_adjacent_time_slot(school_data):
    Lesson.objects.create(
        teacher=school_data["teacher"],
        subject=school_data["subject"],
        room=school_data["room"],
        student_group=school_data["group"],
        time_slot=school_data["slot"],
    )

    lesson = Lesson.objects.create(
        teacher=school_data["teacher"],
        subject=school_data["other_subject"],
        room=school_data["other_room"],
        student_group=school_data["other_group"],
        time_slot=school_data["later_slot"],
    )

    assert lesson.pk is not None
