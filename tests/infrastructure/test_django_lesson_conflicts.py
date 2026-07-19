from datetime import time

import pytest

from app.infrastructure.database.models import (
    AcademicYear,
    Lesson,
    Period,
    Room,
    StudentGroup,
    Subject,
    Teacher,
)
from app.infrastructure.repositories.django_lessons import DjangoLessonRepository


@pytest.mark.django_db
def test_list_lessons_for_substitute_returns_only_assigned_lessons():
    academic_year = AcademicYear.objects.create(name="2026/2027")

    period = Period.objects.create(
        academic_year=academic_year,
        name="P1",
        order=1,
        start_time=time(8, 0),
        end_time=time(8, 45),
    )

    teacher = Teacher.objects.create(name="Alice")
    substitute = Teacher.objects.create(name="Bob")
    other_teacher = Teacher.objects.create(name="Charlie")

    subject = Subject.objects.create(name="Math")
    room = Room.objects.create(name="101")
    group = StudentGroup.objects.create(name="7A")

    lesson_with_substitute = Lesson.objects.create(
        teacher=teacher,
        planned_substitute=substitute,
        subject=subject,
        room=room,
        student_group=group,
        day=Lesson.Day.MONDAY,
        start_period=period,
    )

    Lesson.objects.create(
        teacher=other_teacher,
        planned_substitute=other_teacher,
        subject=subject,
        room=room,
        student_group=group,
        day=Lesson.Day.MONDAY,
        start_period=period,
    )

    repository = DjangoLessonRepository()

    lessons = repository.list_lessons_for_substitute(
        substitute.id,
        academic_year.id,
    )

    assert len(lessons) == 1
    assert lessons[0].id == lesson_with_substitute.id
    assert lessons[0].teacher_name == "Alice"