import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from app.infrastructure.database.models import AcademicYear, Period, School


@pytest.fixture
def academic_year(db):
    school = School.objects.create(name="Riverside School")
    return AcademicYear.objects.create(school=school, name="2026")


@pytest.mark.django_db
def test_duplicate_order_within_academic_year_is_rejected(academic_year):
    Period.objects.create(
        academic_year=academic_year, name="Period 1", order=1,
        start_time="08:00", end_time="08:50",
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Period.objects.create(
                academic_year=academic_year, name="Period 1 (again)", order=1,
                start_time="09:00", end_time="09:50",
            )


@pytest.mark.django_db
def test_duplicate_name_within_academic_year_is_rejected(academic_year):
    Period.objects.create(
        academic_year=academic_year, name="Period 1", order=1,
        start_time="08:00", end_time="08:50",
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Period.objects.create(
                academic_year=academic_year, name="Period 1", order=2,
                start_time="09:00", end_time="09:50",
            )


@pytest.mark.django_db
def test_same_order_and_name_are_allowed_across_different_academic_years():
    school = School.objects.create(name="Riverside School")
    year_a = AcademicYear.objects.create(school=school, name="2026")
    year_b = AcademicYear.objects.create(school=school, name="2027")

    period_a = Period.objects.create(
        academic_year=year_a, name="Period 1", order=1,
        start_time="08:00", end_time="08:50",
    )
    period_b = Period.objects.create(
        academic_year=year_b, name="Period 1", order=1,
        start_time="08:00", end_time="08:50",
    )

    assert period_a.academic_year != period_b.academic_year


@pytest.mark.django_db
def test_full_clean_rejects_start_time_equal_to_end_time(academic_year):
    period = Period(
        academic_year=academic_year, name="Period 1", order=1,
        start_time="09:00", end_time="09:00",
    )

    with pytest.raises(ValidationError):
        period.full_clean()


@pytest.mark.django_db
def test_full_clean_rejects_start_time_after_end_time(academic_year):
    period = Period(
        academic_year=academic_year, name="Period 1", order=1,
        start_time="10:00", end_time="09:00",
    )

    with pytest.raises(ValidationError):
        period.full_clean()


@pytest.mark.django_db
def test_full_clean_accepts_a_valid_period(academic_year):
    period = Period(
        academic_year=academic_year, name="Period 1", order=1,
        start_time="09:00", end_time="09:50", kind=Period.Kind.LESSON,
    )

    period.full_clean()


@pytest.mark.django_db
def test_break_kind_is_persisted_and_does_not_accept_lessons(academic_year):
    period = Period.objects.create(
        academic_year=academic_year, name="Lunch", order=1,
        start_time="12:00", end_time="12:30", kind=Period.Kind.BREAK,
    )

    assert period.kind == Period.Kind.BREAK
    assert not period.to_domain().accepts_lessons


@pytest.mark.django_db
def test_lesson_kind_is_the_default(academic_year):
    period = Period.objects.create(
        academic_year=academic_year, name="Period 1", order=1,
        start_time="08:00", end_time="08:50",
    )

    assert period.kind == Period.Kind.LESSON
    assert period.to_domain().accepts_lessons
