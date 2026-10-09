from django.urls import reverse
import pytest

from app.infrastructure.database.models import (
    AcademicYear,
    Lesson,
    Period,
    Room,
    StudentGroup,
    Subject,
    Teacher,
)

# Phase 10 audit: ProtectedDeleteMixin correctly blocked these deletes,
# but object_confirm_delete.html never rendered the form's non-field
# error, so the user saw the same confirmation page again with no
# explanation. This is the exact message ProtectedDeleteMixin.form_valid()
# attaches on a blocked delete.
PROTECTED_DELETE_ERROR = b"This item is used by a lesson and cannot be deleted."

PROTECTED_DELETE_CASES = [
    ("teacher", "teacher-delete", Teacher),
    ("room", "room-delete", Room),
    ("subject", "subject-delete", Subject),
    ("student_group", "student-group-delete", StudentGroup),
    ("period", "period-delete", Period),
    ("year", "academic-year-delete", AcademicYear),
]


def _make_protected_school_data(client):
    school = client.school
    year = AcademicYear.objects.create(school=school, name="2026")
    period = Period.objects.create(
        academic_year=year, name="Period 1", order=1,
        start_time="08:00", end_time="09:00",
    )
    teacher = Teacher.objects.create(school=school, name="Ada")
    room = Room.objects.create(school=school, name="A101")
    subject = Subject.objects.create(school=school, name="Math")
    student_group = StudentGroup.objects.create(school=school, name="Grade 1")
    Lesson.objects.create(
        teacher=teacher,
        subject=subject,
        room=room,
        student_group=student_group,
        day=Lesson.Day.MONDAY,
        start_period=period,
    )
    return {
        "year": year,
        "period": period,
        "teacher": teacher,
        "room": room,
        "subject": subject,
        "student_group": student_group,
    }


@pytest.mark.django_db
@pytest.mark.parametrize("key,delete_url,model", PROTECTED_DELETE_CASES)
def test_deleting_a_resource_referenced_by_a_lesson_shows_an_error(
    make_principal_client, key, delete_url, model
):
    client = make_principal_client("alice", "School A")
    data = _make_protected_school_data(client)
    target = data[key]

    response = client.post(reverse(delete_url, args=[target.pk]))

    assert response.status_code == 200
    assert PROTECTED_DELETE_ERROR in response.content
    assert model.objects.filter(pk=target.pk).exists()


@pytest.mark.django_db
def test_deleting_an_unreferenced_teacher_still_succeeds(make_principal_client):
    # Guards against the fix over-correcting: a resource with no
    # Lesson referencing it must still delete normally.
    client = make_principal_client("alice", "School A")
    teacher = Teacher.objects.create(school=client.school, name="Unused Teacher")

    response = client.post(reverse("teacher-delete", args=[teacher.pk]))

    assert response.status_code == 302
    assert not Teacher.objects.filter(pk=teacher.pk).exists()
