import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from app.application.services.registration import register_principal
from app.infrastructure.database.models import School, SchoolMembership

VALID_PASSWORD = "xQ7!vB29zRk4"


@pytest.mark.django_db
def test_register_principal_creates_user_school_and_membership():
    user, school, membership = register_principal(
        username="ada", password=VALID_PASSWORD, school_name="Riverside School"
    )

    assert get_user_model().objects.count() == 1
    assert School.objects.count() == 1
    assert SchoolMembership.objects.count() == 1

    assert membership.role == SchoolMembership.Role.PRINCIPAL
    assert membership.school_id == school.id
    assert membership.user_id == user.id
    assert school.name == "Riverside School"

    assert user.has_usable_password()
    assert user.check_password(VALID_PASSWORD)
    assert user.is_staff is False
    assert user.is_superuser is False


@pytest.mark.django_db
def test_register_principal_always_creates_a_new_school_even_with_a_duplicate_name():
    School.objects.create(name="Riverside School")

    _, school, _ = register_principal(
        username="ada", password=VALID_PASSWORD, school_name="Riverside School"
    )

    assert School.objects.filter(name="Riverside School").count() == 2
    assert School.objects.filter(name="Riverside School").exclude(pk=school.pk).exists()


@pytest.mark.django_db
def test_register_principal_rejects_duplicate_username_and_creates_no_extra_school():
    register_principal(username="ada", password=VALID_PASSWORD, school_name="First School")

    with pytest.raises(IntegrityError):
        register_principal(
            username="ada", password=VALID_PASSWORD, school_name="Second School"
        )

    assert get_user_model().objects.count() == 1
    assert School.objects.count() == 1
    assert SchoolMembership.objects.count() == 1


@pytest.mark.django_db
def test_register_principal_rejects_a_weak_password_and_creates_nothing():
    with pytest.raises(ValidationError):
        register_principal(username="ada", password="short", school_name="Riverside School")

    assert get_user_model().objects.count() == 0
    assert School.objects.count() == 0
    assert SchoolMembership.objects.count() == 0


@pytest.mark.django_db
def test_two_registrations_produce_independent_users_schools_and_memberships():
    user_a, school_a, membership_a = register_principal(
        username="ada", password=VALID_PASSWORD, school_name="School A"
    )
    user_b, school_b, membership_b = register_principal(
        username="grace", password=VALID_PASSWORD, school_name="School B"
    )

    assert user_a.id != user_b.id
    assert school_a.id != school_b.id
    assert membership_a.id != membership_b.id
    assert membership_a.school_id == school_a.id
    assert membership_b.school_id == school_b.id
    assert SchoolMembership.objects.filter(
        user=user_a, school=school_b
    ).exists() is False
    assert SchoolMembership.objects.filter(
        user=user_b, school=school_a
    ).exists() is False


@pytest.mark.django_db
def test_failure_after_user_creation_rolls_back_the_user_and_school(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("simulated failure creating the membership")

    monkeypatch.setattr(SchoolMembership.objects, "create", boom)

    with pytest.raises(RuntimeError):
        register_principal(
            username="ada", password=VALID_PASSWORD, school_name="Riverside School"
        )

    assert get_user_model().objects.filter(username="ada").exists() is False
    assert School.objects.filter(name="Riverside School").exists() is False
