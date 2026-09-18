import pytest
from django.urls import reverse

from app.presentation.web.school_access import CURRENT_SCHOOL_SESSION_KEY

PROTECTED_URL = "staff-schedule"


@pytest.mark.django_db
def test_single_membership_becomes_current_school(client, make_user, make_school, make_membership):
    user = make_user("ada")
    school = make_school("Riverside School")
    make_membership(user, school)
    client.force_login(user)

    response = client.get(reverse(PROTECTED_URL))

    assert response.status_code == 200
    assert client.session[CURRENT_SCHOOL_SESSION_KEY] == school.id


@pytest.mark.django_db
def test_multiple_memberships_without_selection_redirects_to_choose_school(
    client, make_user, make_school, make_membership
):
    user = make_user("ada")
    school_a = make_school("School A")
    school_b = make_school("School B")
    make_membership(user, school_a)
    make_membership(user, school_b)
    client.force_login(user)

    response = client.get(reverse(PROTECTED_URL))

    assert response.status_code == 302
    assert response.url == reverse("choose-school")


@pytest.mark.django_db
def test_user_can_select_a_school_they_belong_to(
    client, make_user, make_school, make_membership
):
    user = make_user("ada")
    school_a = make_school("School A")
    school_b = make_school("School B")
    make_membership(user, school_a)
    make_membership(user, school_b)
    client.force_login(user)

    response = client.post(reverse("choose-school"), {"school_id": school_a.id})

    assert response.status_code == 302
    assert response.url == reverse("schedule")


@pytest.mark.django_db
def test_selecting_a_school_stores_it_in_the_session(
    client, make_user, make_school, make_membership
):
    user = make_user("ada")
    school_a = make_school("School A")
    school_b = make_school("School B")
    make_membership(user, school_a)
    make_membership(user, school_b)
    client.force_login(user)

    client.post(reverse("choose-school"), {"school_id": school_a.id})

    assert client.session[CURRENT_SCHOOL_SESSION_KEY] == school_a.id


@pytest.mark.django_db
def test_cannot_select_a_school_not_a_member_of(
    client, make_user, make_school, make_membership
):
    user = make_user("ada")
    school_a = make_school("School A")
    school_b = make_school("School B")
    make_membership(user, school_a)
    client.force_login(user)

    response = client.post(reverse("choose-school"), {"school_id": school_b.id})

    assert response.status_code == 400
    assert CURRENT_SCHOOL_SESSION_KEY not in client.session


@pytest.mark.django_db
def test_cannot_select_a_nonexistent_school_id(client, make_user, make_school, make_membership):
    user = make_user("ada")
    school = make_school("School A")
    make_membership(user, school)
    client.force_login(user)

    response = client.post(reverse("choose-school"), {"school_id": 999999})

    assert response.status_code == 400
    assert CURRENT_SCHOOL_SESSION_KEY not in client.session


@pytest.mark.django_db
def test_removed_membership_loses_access_on_next_request(
    client, make_user, make_school, make_membership
):
    user = make_user("ada")
    school = make_school("Riverside School")
    membership = make_membership(user, school)
    client.force_login(user)

    first_response = client.get(reverse(PROTECTED_URL))
    assert first_response.status_code == 200

    membership.delete()

    second_response = client.get(reverse(PROTECTED_URL))
    assert second_response.status_code == 403


@pytest.mark.django_db
def test_zero_memberships_receives_no_school_access_response(client, make_user):
    user = make_user("ada")
    client.force_login(user)

    response = client.get(reverse(PROTECTED_URL))

    assert response.status_code == 403
    assert b"No school access" in response.content


@pytest.mark.django_db
def test_is_staff_without_membership_cannot_access(client, make_user):
    user = make_user("ada", is_staff=True)
    client.force_login(user)

    response = client.get(reverse(PROTECTED_URL))

    assert response.status_code == 403


@pytest.mark.django_db
def test_non_staff_with_principal_membership_can_access(
    client, make_user, make_school, make_membership
):
    user = make_user("ada", is_staff=False)
    school = make_school("Riverside School")
    make_membership(user, school)
    client.force_login(user)

    response = client.get(reverse(PROTECTED_URL))

    assert response.status_code == 200


@pytest.mark.django_db
def test_superuser_without_membership_cannot_access(client, make_user):
    user = make_user("ada", is_staff=True, is_superuser=True)
    client.force_login(user)

    response = client.get(reverse(PROTECTED_URL))

    assert response.status_code == 403


@pytest.mark.django_db
def test_superuser_with_membership_can_access(client, make_user, make_school, make_membership):
    user = make_user("ada", is_staff=True, is_superuser=True)
    school = make_school("Riverside School")
    make_membership(user, school)
    client.force_login(user)

    response = client.get(reverse(PROTECTED_URL))

    assert response.status_code == 200


@pytest.mark.django_db
def test_current_school_is_revalidated_against_the_database_not_the_session(
    client, make_user, make_school, make_membership
):
    """A session value is only ever a workspace hint. Even if it points
    at a real School the user does NOT belong to, resolution must fall
    back on live SchoolMembership rows rather than trusting it."""
    user = make_user("ada")
    school = make_school("Riverside School")
    other_school = make_school("Other School")
    make_membership(user, school)
    client.force_login(user)

    session = client.session
    session[CURRENT_SCHOOL_SESSION_KEY] = other_school.id
    session.save()

    response = client.get(reverse(PROTECTED_URL))

    assert response.status_code == 200
    assert client.session[CURRENT_SCHOOL_SESSION_KEY] == school.id
