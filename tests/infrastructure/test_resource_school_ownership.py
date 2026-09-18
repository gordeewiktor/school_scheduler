import pytest
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from app.infrastructure.database.models import (
    AcademicYear,
    Lesson,
    Period,
    Room,
    School,
    StudentGroup,
    Subject,
    Teacher,
)

MODELS = [Teacher, Room, Subject, StudentGroup]


@pytest.mark.django_db
@pytest.mark.parametrize("model", MODELS)
def test_resource_requires_a_school(model):
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            model.objects.create(name="Resource")


@pytest.mark.django_db
@pytest.mark.parametrize("model", MODELS)
def test_same_school_cannot_have_duplicate_resource_names(model):
    school = School.objects.create(name="Riverside School")
    model.objects.create(school=school, name="Shared Name")

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            model.objects.create(school=school, name="Shared Name")


@pytest.mark.django_db
@pytest.mark.parametrize("model", MODELS)
def test_different_schools_can_share_a_resource_name(model):
    school_a = School.objects.create(name="School A")
    school_b = School.objects.create(name="School B")

    resource_a = model.objects.create(school=school_a, name="Shared Name")
    resource_b = model.objects.create(school=school_b, name="Shared Name")

    assert resource_a.name == resource_b.name
    assert resource_a.school != resource_b.school


@pytest.mark.django_db
@pytest.mark.parametrize("model", MODELS)
def test_deleting_school_cascades_to_resource_without_lessons(model):
    school = School.objects.create(name="Riverside School")
    model.objects.create(school=school, name="Resource")

    school.delete()

    assert model.objects.count() == 0


@pytest.mark.django_db
def test_deleting_school_with_referenced_lessons_is_protected():
    school = School.objects.create(name="Riverside School")
    year = AcademicYear.objects.create(school=school, name="2026")
    period = Period.objects.create(
        academic_year=year,
        name="Period 1",
        order=1,
        start_time="08:00",
        end_time="09:00",
    )
    teacher = Teacher.objects.create(school=school, name="Ada")
    room = Room.objects.create(school=school, name="A101")
    subject = Subject.objects.create(school=school, name="Math")
    group = StudentGroup.objects.create(school=school, name="Grade 1")
    Lesson.objects.create(
        teacher=teacher,
        subject=subject,
        room=room,
        student_group=group,
        day=Lesson.Day.MONDAY,
        start_period=period,
    )

    with pytest.raises(ProtectedError):
        school.delete()

    assert School.objects.filter(pk=school.pk).exists()
    assert Teacher.objects.filter(pk=teacher.pk).exists()
