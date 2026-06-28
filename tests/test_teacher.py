import pytest

from app.infrastructure.database.models import Teacher


@pytest.mark.django_db
def test_teacher_keeps_name_and_email():
    teacher = Teacher.objects.create(name="Viktor", email="viktor@example.com")

    assert teacher.name == "Viktor"
    assert teacher.email == "viktor@example.com"
