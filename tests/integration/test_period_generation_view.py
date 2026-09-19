import pytest
from django.urls import reverse

from app.infrastructure.database.models import AcademicYear, Period


def _generate_form_data(academic_year, **overrides):
    data = {
        "academic_year": academic_year.pk,
        "lesson_count": 3,
        "first_start_time": "08:00",
        "lesson_duration_minutes": 45,
        "breaks": "2:10",
    }
    data.update(overrides)
    return data


@pytest.mark.django_db
def test_get_only_offers_academic_years_without_existing_periods(make_principal_client):
    client = make_principal_client("alice", "School A")
    empty_year = AcademicYear.objects.create(school=client.school, name="2026")
    populated_year = AcademicYear.objects.create(school=client.school, name="2025")
    Period.objects.create(
        academic_year=populated_year, name="Period 1", order=1,
        start_time="08:00", end_time="08:45",
    )

    response = client.get(reverse("period-generate"))

    offered_ids = {
        year.pk for year in response.context["form"].fields["academic_year"].queryset
    }
    assert offered_ids == {empty_year.pk}


@pytest.mark.django_db
def test_post_creates_the_expected_period_sequence(make_principal_client):
    client = make_principal_client("alice", "School A")
    year = AcademicYear.objects.create(school=client.school, name="2026")

    response = client.post(
        reverse("period-generate"), _generate_form_data(year)
    )

    assert response.status_code == 302
    assert response.url == reverse("period-list")
    periods = list(Period.objects.filter(academic_year=year).order_by("order"))
    assert [(p.order, p.name, str(p.start_time)[:5], str(p.end_time)[:5], p.kind) for p in periods] == [
        (1, "Period 1", "08:00", "08:45", Period.Kind.LESSON),
        (2, "Period 2", "08:45", "09:30", Period.Kind.LESSON),
        (3, "Break after Period 2", "09:30", "09:40", Period.Kind.BREAK),
        (4, "Period 3", "09:40", "10:25", Period.Kind.LESSON),
    ]


@pytest.mark.django_db
def test_post_for_a_year_that_already_has_periods_creates_nothing(make_principal_client):
    client = make_principal_client("alice", "School A")
    year = AcademicYear.objects.create(school=client.school, name="2026")
    Period.objects.create(
        academic_year=year, name="Existing Period", order=1,
        start_time="08:00", end_time="08:45",
    )

    # The academic_year field's queryset already excludes years with
    # periods, so posting one directly is rejected as an invalid
    # choice before the service's own PeriodsAlreadyExistError guard
    # (exercised directly in test_period_generation_service.py) is
    # even reached. Both layers refusing independently is the point.
    response = client.post(
        reverse("period-generate"),
        _generate_form_data(year, breaks=""),
    )

    assert response.status_code == 200
    assert response.context["form"].errors["academic_year"]
    assert Period.objects.filter(academic_year=year).count() == 1


@pytest.mark.django_db
def test_post_rejects_another_schools_academic_year(make_principal_client):
    client_a = make_principal_client("alice", "School A")
    client_b = make_principal_client("bob", "School B")
    year_b = AcademicYear.objects.create(school=client_b.school, name="2026")

    response = client_a.post(
        reverse("period-generate"),
        _generate_form_data(year_b, breaks=""),
    )

    assert response.status_code == 200
    assert not response.context["form"].is_valid()
    assert Period.objects.filter(academic_year=year_b).count() == 0


@pytest.mark.django_db
def test_post_rejects_a_malformed_breaks_field(make_principal_client):
    client = make_principal_client("alice", "School A")
    year = AcademicYear.objects.create(school=client.school, name="2026")

    response = client.post(
        reverse("period-generate"),
        _generate_form_data(year, breaks="not-a-valid-entry"),
    )

    assert response.status_code == 200
    assert response.context["form"].errors["breaks"]
    assert Period.objects.filter(academic_year=year).count() == 0


@pytest.mark.django_db
def test_post_rejects_a_schedule_that_crosses_midnight(make_principal_client):
    client = make_principal_client("alice", "School A")
    year = AcademicYear.objects.create(school=client.school, name="2026")

    response = client.post(
        reverse("period-generate"),
        _generate_form_data(
            year,
            lesson_count=1,
            first_start_time="23:30",
            lesson_duration_minutes=50,
            breaks="",
        ),
    )

    assert response.status_code == 200
    assert response.context["form"].non_field_errors()
    assert Period.objects.filter(academic_year=year).count() == 0
