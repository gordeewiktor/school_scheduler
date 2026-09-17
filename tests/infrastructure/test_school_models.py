import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

from app.infrastructure.database.models import School, SchoolMembership


@pytest.mark.django_db
def test_school_name_is_not_globally_unique():
    School.objects.create(name="Riverside School")
    School.objects.create(name="Riverside School")

    assert School.objects.filter(name="Riverside School").count() == 2


@pytest.mark.django_db
def test_school_membership_links_user_and_school_with_principal_role():
    user = get_user_model().objects.create_user(username="ada", password="test-password")
    school = School.objects.create(name="Riverside School")

    membership = SchoolMembership.objects.create(user=user, school=school)

    assert membership.role == SchoolMembership.Role.PRINCIPAL
    assert user.school_memberships.get() == membership
    assert school.memberships.get() == membership


@pytest.mark.django_db
def test_school_membership_is_unique_per_user_and_school():
    user = get_user_model().objects.create_user(username="ada", password="test-password")
    school = School.objects.create(name="Riverside School")
    SchoolMembership.objects.create(user=user, school=school)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            SchoolMembership.objects.create(user=user, school=school)


@pytest.mark.django_db
def test_same_user_can_belong_to_multiple_schools():
    user = get_user_model().objects.create_user(username="ada", password="test-password")
    school_a = School.objects.create(name="School A")
    school_b = School.objects.create(name="School B")

    SchoolMembership.objects.create(user=user, school=school_a)
    SchoolMembership.objects.create(user=user, school=school_b)

    assert user.school_memberships.count() == 2


@pytest.mark.django_db
def test_deleting_school_cascades_to_memberships():
    user = get_user_model().objects.create_user(username="ada", password="test-password")
    school = School.objects.create(name="Riverside School")
    SchoolMembership.objects.create(user=user, school=school)

    school.delete()

    assert SchoolMembership.objects.count() == 0
