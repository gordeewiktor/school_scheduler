from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command, CommandError

from app.infrastructure.database.models import School, SchoolMembership


@pytest.mark.django_db
def test_create_school_creates_school_and_principal_membership():
    get_user_model().objects.create_user(username="principal", password="test-password")
    output = StringIO()

    call_command("create_school", "Riverside School", "--username=principal", stdout=output)

    school = School.objects.get(name="Riverside School")
    membership = SchoolMembership.objects.get(school=school)
    assert membership.user.username == "principal"
    assert membership.role == SchoolMembership.Role.PRINCIPAL


@pytest.mark.django_db
def test_create_school_is_idempotent_for_same_user_and_school():
    get_user_model().objects.create_user(username="principal", password="test-password")

    call_command("create_school", "Riverside School", "--username=principal", stdout=StringIO())
    call_command("create_school", "Riverside School", "--username=principal", stdout=StringIO())

    assert School.objects.filter(name="Riverside School").count() == 1
    assert SchoolMembership.objects.count() == 1


@pytest.mark.django_db
def test_create_school_raises_for_unknown_username():
    with pytest.raises(CommandError):
        call_command("create_school", "Riverside School", "--username=missing", stdout=StringIO())
