import pytest

from app.infrastructure.database.models import School, Teacher


@pytest.mark.django_db
def test_teacher_keeps_name_and_email():
    school = School.objects.create(name="Test School")
    teacher = Teacher.objects.create(school=school, name="Viktor", email="viktor@example.com")

    assert teacher.name == "Viktor"
    assert teacher.email == "viktor@example.com"
