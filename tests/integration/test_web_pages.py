import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from app.infrastructure.database.models import TimeSlot


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
def test_create_noon_time_slot_from_time_input(client):
    user = get_user_model().objects.create_user(username="scheduler", password="test-password")
    client.force_login(user)

    response = client.post(
        reverse("time-slot-create"),
        {"day": "Monday", "start_time": "12:00", "end_time": "13:00"},
    )

    assert response.status_code == 302
    assert TimeSlot.objects.filter(
        day="Monday", start_time="12:00", end_time="13:00"
    ).exists()


@pytest.mark.django_db
def test_invalid_time_input_returns_form_errors_instead_of_crashing(client):
    user = get_user_model().objects.create_user(username="scheduler", password="test-password")
    client.force_login(user)

    response = client.post(
        reverse("time-slot-create"),
        {"day": "Monday", "start_time": "invalid", "end_time": "invalid"},
    )

    assert response.status_code == 200
    assert response.context["form"].errors["start_time"] == ["Enter a valid time."]
    assert response.context["form"].errors["end_time"] == ["Enter a valid time."]
