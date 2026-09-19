import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from app.infrastructure.database.models import School, SchoolMembership

VALID_PASSWORD = "xQ7!vB29zRk4"


def _registration_data(**overrides):
    data = {
        "username": "ada",
        "password1": VALID_PASSWORD,
        "password2": VALID_PASSWORD,
        "school_name": "Riverside School",
    }
    data.update(overrides)
    return data


@pytest.mark.django_db
def test_anonymous_get_registration_page_returns_200(client):
    response = client.get(reverse("register"))

    assert response.status_code == 200
    assert b"school_name" in response.content


@pytest.mark.django_db
def test_valid_post_creates_account_school_membership_and_logs_in(client):
    response = client.post(reverse("register"), _registration_data())

    assert response.status_code == 302
    assert response.url == reverse("schedule")

    assert get_user_model().objects.count() == 1
    assert School.objects.count() == 1
    assert SchoolMembership.objects.count() == 1

    user = get_user_model().objects.get(username="ada")
    membership = SchoolMembership.objects.get()
    assert membership.user_id == user.id
    assert membership.role == SchoolMembership.Role.PRINCIPAL

    # The response's session now belongs to the newly-created user.
    assert int(client.session["_auth_user_id"]) == user.id


@pytest.mark.django_db
def test_new_principal_can_access_their_school_scoped_application(client):
    client.post(reverse("register"), _registration_data())
    school = School.objects.get()

    response = client.get(reverse("schedule"))

    assert response.status_code == 200
    assert response.context["current_school"] == school

    lesson_list_response = client.get(reverse("lesson-list"))
    assert lesson_list_response.status_code == 200


@pytest.mark.django_db
def test_authenticated_user_visiting_registration_is_redirected_to_schedule(
    make_principal_client,
):
    client = make_principal_client("alice", "School A")

    response = client.get(reverse("register"))

    assert response.status_code == 302
    assert response.url == reverse("schedule")


@pytest.mark.django_db
def test_authenticated_user_posting_registration_creates_nothing(make_principal_client):
    client = make_principal_client("alice", "School A")
    assert get_user_model().objects.count() == 1
    assert School.objects.count() == 1

    response = client.post(
        reverse("register"),
        _registration_data(username="mallory", school_name="Mallory's School"),
    )

    assert response.status_code == 302
    assert response.url == reverse("schedule")
    assert get_user_model().objects.count() == 1
    assert School.objects.count() == 1
    assert SchoolMembership.objects.count() == 1
    assert not get_user_model().objects.filter(username="mallory").exists()


@pytest.mark.django_db
def test_invalid_form_data_creates_nothing_and_returns_form_errors(client):
    response = client.post(
        reverse("register"),
        _registration_data(password2="a-completely-different-password"),
    )

    assert response.status_code == 200
    assert response.context["form"].errors
    assert get_user_model().objects.count() == 0
    assert School.objects.count() == 0
    assert SchoolMembership.objects.count() == 0


@pytest.mark.django_db
def test_blank_school_name_creates_nothing_and_returns_form_error(client):
    response = client.post(reverse("register"), _registration_data(school_name="   "))

    assert response.status_code == 200
    assert "school_name" in response.context["form"].errors
    assert get_user_model().objects.count() == 0
    assert School.objects.count() == 0


@pytest.mark.django_db
def test_duplicate_username_returns_clean_form_error_and_creates_no_extra_rows(client):
    client.post(reverse("register"), _registration_data())
    client.post(reverse("logout"))

    response = client.post(
        reverse("register"),
        _registration_data(school_name="Someone Else's School"),
    )

    assert response.status_code == 200
    assert response.context["form"].errors
    assert get_user_model().objects.count() == 1
    assert School.objects.count() == 1
    assert SchoolMembership.objects.count() == 1


@pytest.mark.django_db
def test_two_anonymous_registrations_with_the_same_school_name_stay_isolated(client):
    other_client = client.__class__()

    client.post(
        reverse("register"),
        _registration_data(username="alice", school_name="Riverside School"),
    )
    other_client.post(
        reverse("register"),
        _registration_data(username="bob", school_name="Riverside School"),
    )

    schools = list(School.objects.filter(name="Riverside School"))
    assert len(schools) == 2
    school_alice, school_bob = schools

    alice = get_user_model().objects.get(username="alice")
    bob = get_user_model().objects.get(username="bob")
    membership_alice = SchoolMembership.objects.get(user=alice)
    membership_bob = SchoolMembership.objects.get(user=bob)
    assert membership_alice.school_id != membership_bob.school_id

    response_alice = client.get(reverse("schedule"))
    response_bob = other_client.get(reverse("schedule"))
    assert response_alice.context["current_school"] == membership_alice.school
    assert response_bob.context["current_school"] == membership_bob.school
    assert response_alice.context["current_school"] != response_bob.context["current_school"]
