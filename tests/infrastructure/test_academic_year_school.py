import pytest
from django.db import IntegrityError, transaction

from app.infrastructure.database.models import AcademicYear, School


@pytest.mark.django_db
def test_academic_year_requires_a_school():
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            AcademicYear.objects.create(name="2026")


@pytest.mark.django_db
def test_same_school_cannot_have_duplicate_academic_year_names():
    school = School.objects.create(name="Riverside School")
    AcademicYear.objects.create(school=school, name="2026")

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            AcademicYear.objects.create(school=school, name="2026")


@pytest.mark.django_db
def test_different_schools_can_share_an_academic_year_name():
    school_a = School.objects.create(name="School A")
    school_b = School.objects.create(name="School B")

    year_a = AcademicYear.objects.create(school=school_a, name="2026")
    year_b = AcademicYear.objects.create(school=school_b, name="2026")

    assert year_a.name == year_b.name
    assert year_a.school != year_b.school


@pytest.mark.django_db
def test_deleting_school_cascades_to_academic_years():
    school = School.objects.create(name="Riverside School")
    AcademicYear.objects.create(school=school, name="2026")

    school.delete()

    assert AcademicYear.objects.count() == 0


@pytest.mark.django_db
def test_academic_year_str_includes_school():
    school = School.objects.create(name="Riverside School")
    year = AcademicYear.objects.create(school=school, name="2026")

    assert str(year) == "2026 (Riverside School)"
