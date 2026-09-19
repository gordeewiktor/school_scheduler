from datetime import time

import pytest

from app.application.services.conflicts import ConflictService
from app.application.services.schedules import ScheduleService
from app.domain.exceptions import CrossSchoolLessonError
from app.domain.models import Day, Lesson as DomainLesson
from app.infrastructure.database.models import (
    AcademicYear,
    Period,
    Room,
    School,
    StudentGroup,
    Subject,
    Teacher,
)
from app.infrastructure.repositories.django_lessons import DjangoLessonRepository


@pytest.fixture
def two_school_data(db):
    school = School.objects.create(name="Home School")
    other_school = School.objects.create(name="Other School")
    year = AcademicYear.objects.create(school=school, name="2026")
    period = Period.objects.create(
        academic_year=year, name="Period 1", order=1, start_time=time(8), end_time=time(9)
    )
    return {
        "period": period,
        "teacher": Teacher.objects.create(school=school, name="Ada"),
        "room": Room.objects.create(school=school, name="A101"),
        "subject": Subject.objects.create(school=school, name="Math"),
        "group": StudentGroup.objects.create(school=school, name="Grade 1"),
        "foreign_teacher": Teacher.objects.create(school=other_school, name="Foreign Teacher"),
        "foreign_room": Room.objects.create(school=other_school, name="Foreign Room"),
        "foreign_subject": Subject.objects.create(school=other_school, name="Foreign Subject"),
        "foreign_group": StudentGroup.objects.create(school=other_school, name="Foreign Group"),
    }


def service():
    repository = DjangoLessonRepository()
    return ScheduleService(repository, ConflictService(repository))


def command(data, **overrides):
    values = dict(
        teacher_id=data["teacher"].pk,
        subject_id=data["subject"].pk,
        room_id=data["room"].pk,
        student_group_id=data["group"].pk,
        day=Day.MONDAY,
        start_period_id=data["period"].pk,
    )
    values.update(overrides)
    return DomainLesson(**values)


@pytest.mark.django_db
def test_service_allows_lesson_when_all_resources_share_the_period_school(two_school_data):
    saved = service().create_lesson(command(two_school_data))
    assert saved.id is not None


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("field", "foreign_key"),
    [
        ("teacher_id", "foreign_teacher"),
        ("room_id", "foreign_room"),
        ("subject_id", "foreign_subject"),
        ("student_group_id", "foreign_group"),
    ],
)
def test_service_rejects_lesson_mixing_resources_from_another_school(
    two_school_data, field, foreign_key
):
    overrides = {field: two_school_data[foreign_key].pk}
    with pytest.raises(CrossSchoolLessonError):
        service().create_lesson(command(two_school_data, **overrides))


@pytest.mark.django_db
def test_service_update_rejects_lesson_mixing_resources_from_another_school(two_school_data):
    saved = service().create_lesson(command(two_school_data))

    with pytest.raises(CrossSchoolLessonError):
        service().update_lesson(
            command(two_school_data, id=saved.id, room_id=two_school_data["foreign_room"].pk)
        )


@pytest.mark.django_db
def test_service_rejects_lesson_with_cross_school_planned_substitute(two_school_data):
    with pytest.raises(CrossSchoolLessonError):
        service().create_lesson(
            command(
                two_school_data,
                planned_substitute_id=two_school_data["foreign_teacher"].pk,
            )
        )


@pytest.mark.django_db
def test_service_update_rejects_lesson_with_cross_school_planned_substitute(two_school_data):
    saved = service().create_lesson(command(two_school_data))

    with pytest.raises(CrossSchoolLessonError):
        service().update_lesson(
            command(
                two_school_data,
                id=saved.id,
                planned_substitute_id=two_school_data["foreign_teacher"].pk,
            )
        )


@pytest.mark.django_db
def test_service_accepts_lesson_with_same_school_planned_substitute(two_school_data):
    substitute = Teacher.objects.create(
        school=two_school_data["teacher"].school, name="Substitute"
    )

    saved = service().create_lesson(
        command(two_school_data, planned_substitute_id=substitute.pk)
    )

    assert saved.planned_substitute_id == substitute.pk


@pytest.mark.django_db
def test_service_accepts_lesson_with_no_planned_substitute(two_school_data):
    saved = service().create_lesson(command(two_school_data, planned_substitute_id=None))

    assert saved.planned_substitute_id is None
