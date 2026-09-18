import pytest
from django.contrib.auth import get_user_model

from app.infrastructure.database.models import School, SchoolMembership


@pytest.fixture
def make_user(db):
    def _make_user(username="user", *, is_staff=False, is_superuser=False, password="test-password"):
        return get_user_model().objects.create_user(
            username=username,
            password=password,
            is_staff=is_staff,
            is_superuser=is_superuser,
        )

    return _make_user


@pytest.fixture
def make_school(db):
    def _make_school(name="School"):
        return School.objects.create(name=name)

    return _make_school


@pytest.fixture
def make_membership(db):
    def _make_membership(user, school, role=SchoolMembership.Role.PRINCIPAL):
        return SchoolMembership.objects.create(user=user, school=school, role=role)

    return _make_membership
