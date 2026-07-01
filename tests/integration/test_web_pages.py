from datetime import time

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from app.infrastructure.database.models import (
    AcademicYear,
    Lesson,
    Period,
    Room,
    StudentGroup,
    Subject,
    Teacher,
)


@pytest.fixture
def authenticated_client(client):
    user = get_user_model().objects.create_user(username="scheduler", password="test-password")
    client.force_login(user)
    return client


@pytest.fixture
def lesson_form_data(db):
    year = AcademicYear.objects.create(name="2026")
    first = Period.objects.create(
        academic_year=year, name="Period 1", order=1,
        start_time=time(8), end_time=time(9)
    )
    second = Period.objects.create(
        academic_year=year, name="Period 2", order=2,
        start_time=time(9), end_time=time(10)
    )
    return {
        "teacher": Teacher.objects.create(name="Ada"),
        "subject": Subject.objects.create(name="Math"),
        "room": Room.objects.create(name="A101"),
        "student_group": StudentGroup.objects.create(name="Grade 1"),
        "day": "MONDAY",
        "start_period": first,
        "second_period": second,
        "duration": 1,
        "notes": "",
    }


def post_data(values):
    return {
        key: value.pk if hasattr(value, "pk") else value
        for key, value in values.items()
        if key != "second_period"
    }


@pytest.mark.django_db
def test_login_page_renders(client):
    response = client.get(reverse("login"))
    assert response.status_code == 200
    assert b"Login" in response.content


@pytest.mark.django_db
def test_dashboard_requires_login(client):
    response = client.get(reverse("dashboard"))
    assert response.status_code == 302
    assert reverse("login") in response["Location"]


@pytest.mark.django_db
def test_create_period_from_time_input(authenticated_client):
    year = AcademicYear.objects.create(name="2026")
    response = authenticated_client.post(
        reverse("period-create"),
        {
            "academic_year": year.pk,
            "name": "Period 1",
            "order": 1,
            "start_time": "12:00",
            "end_time": "13:00",
            "kind": "LESSON",
        },
    )
    assert response.status_code == 302
    assert Period.objects.filter(academic_year=year, order=1).exists()


@pytest.mark.django_db
def test_invalid_period_time_returns_form_errors(authenticated_client):
    year = AcademicYear.objects.create(name="2026")
    response = authenticated_client.post(
        reverse("period-create"),
        {
            "academic_year": year.pk,
            "name": "Period 1",
            "order": 1,
            "start_time": "invalid",
            "end_time": "invalid",
            "kind": "LESSON",
        },
    )
    assert response.status_code == 200
    assert response.context["form"].errors["start_time"] == ["Enter a valid time."]
    assert response.context["form"].errors["end_time"] == ["Enter a valid time."]


@pytest.mark.django_db
def test_schedule_uses_period_columns_and_breaks(authenticated_client):
    year = AcademicYear.objects.create(name="2026")
    Period.objects.create(
        academic_year=year, name="Morning Break", order=1,
        start_time=time(10), end_time=time(10, 30), kind=Period.Kind.BREAK
    )
    response = authenticated_client.get(
        reverse("schedule"), {"view": "whole_school", "academic_year": year.pk}
    )
    assert response.status_code == 200
    assert b"Morning Break" in response.content
    assert len(response.context["periods"]) == 1


@pytest.mark.django_db
def test_lesson_form_writes_through_service(authenticated_client, lesson_form_data):
    response = authenticated_client.post(reverse("lesson-create"), post_data(lesson_form_data))
    assert response.status_code == 302
    lesson = Lesson.objects.get()
    assert lesson.day == "MONDAY"
    assert lesson.start_period == lesson_form_data["start_period"]


@pytest.mark.django_db
def test_lesson_form_returns_conflict_on_same_teacher(authenticated_client, lesson_form_data):
    authenticated_client.post(reverse("lesson-create"), post_data(lesson_form_data))
    response = authenticated_client.post(reverse("lesson-create"), post_data(lesson_form_data))
    assert response.status_code == 200
    assert "Teacher is already teaching then." in response.context["form"].errors["teacher"]
    assert Lesson.objects.count() == 1


@pytest.mark.django_db
def test_multi_period_lesson_renders_with_colspan(authenticated_client, lesson_form_data):
    lesson_form_data["duration"] = 2
    authenticated_client.post(reverse("lesson-create"), post_data(lesson_form_data))
    year = lesson_form_data["start_period"].academic_year
    response = authenticated_client.get(
        reverse("schedule"), {"view": "whole_school", "academic_year": year.pk}
    )
    assert response.status_code == 200
    assert b'colspan="2"' in response.content


@pytest.mark.django_db
def test_schedule_starts_with_view_choices_and_no_timetable(authenticated_client):
    AcademicYear.objects.create(name="2026")

    response = authenticated_client.get(reverse("schedule"))

    assert response.status_code == 200
    assert response.context["page"].waiting_for_view is True
    assert response.context["page"].show_timetable is False
    assert response.context["rows"] == []
    assert b"Choose what you want to view" in response.content
    assert b"<table" not in response.content


@pytest.mark.django_db
def test_teacher_view_only_exposes_teacher_selector(authenticated_client):
    AcademicYear.objects.create(name="2026")
    Teacher.objects.create(name="Ada")
    Room.objects.create(name="A101")
    StudentGroup.objects.create(name="Grade 1")

    response = authenticated_client.get(reverse("schedule"), {"view": "teacher"})

    selector = response.context["page"].selector
    assert selector.name == "teacher"
    assert response.context["page"].waiting_for_selection is True
    assert b'name="teacher"' in response.content
    assert b'name="room"' not in response.content
    assert b'name="student_group"' not in response.content
