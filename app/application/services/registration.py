from django.contrib.auth import get_user_model
from django.contrib.auth import password_validation
from django.contrib.auth.models import AbstractUser
from django.db import transaction

from app.infrastructure.database.models import School, SchoolMembership


def register_principal(
    *, username: str, password: str, school_name: str
) -> tuple[AbstractUser, School, SchoolMembership]:
    """Atomically create a new User, a brand-new School, and a PRINCIPAL
    SchoolMembership linking them.

    `school_name` is only ever used to name a newly created School — it
    is never treated as a lookup key, so this can never attach the
    caller to an existing School. Raises `django.core.exceptions.
    ValidationError` if `password` fails the configured password
    validators, or `django.db.utils.IntegrityError` if `username` is
    already taken; either way, nothing is persisted.
    """
    User = get_user_model()
    with transaction.atomic():
        password_validation.validate_password(password, User(username=username))
        user = User.objects.create_user(username=username, password=password)
        school = School.objects.create(name=school_name)
        membership = SchoolMembership.objects.create(
            user=user, school=school, role=SchoolMembership.Role.PRINCIPAL
        )
    return user, school, membership
