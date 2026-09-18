from datetime import time

import pytest
from django.urls import reverse

from app.infrastructure.database.models import (
    AcademicYear,
    Lesson,
    Period,
    Room,
    StudentGroup,
    Subject,
    Teacher,
)

# (model, list_url, update_url, delete_url, extra_kwargs_for_create)
DIRECT_SCHOOL_RESOURCES = [
    (Teacher, "teacher-list", "teacher-update", "teacher-delete", {"name": "Ada"}),
    (Room, "room-list", "room-update", "room-delete", {"name": "A101"}),
    (Subject, "subject-list", "subject-update", "subject-delete", {"name": "Math"}),
    (
        StudentGroup,
        "student-group-list",
        "student-group-update",
        "student-group-delete",
        {"name": "Grade 1"},
    ),
    (AcademicYear, "academic-year-list", "academic-year-update", "academic-year-delete", {"name": "2026"}),
]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "model,list_url,update_url,delete_url,extra", DIRECT_SCHOOL_RESOURCES
)
def test_list_only_shows_current_school_objects(
    make_principal_client, model, list_url, update_url, delete_url, extra
):
    client_a = make_principal_client("alice", "School A")
    client_b = make_principal_client("bob", "School B")
    obj_a = model.objects.create(school=client_a.school, **extra)
    foreign_extra = {**extra, "name": f"Foreign {extra['name']}"}
    obj_b = model.objects.create(school=client_b.school, **foreign_extra)

    response = client_a.get(reverse(list_url))

    assert response.status_code == 200
    assert obj_a.name.encode() in response.content
    assert obj_b.name.encode() not in response.content


@pytest.mark.django_db
@pytest.mark.parametrize(
    "model,list_url,update_url,delete_url,extra", DIRECT_SCHOOL_RESOURCES
)
def test_get_update_of_another_schools_object_is_404(
    make_principal_client, model, list_url, update_url, delete_url, extra
):
    client_a = make_principal_client("alice", "School A")
    client_b = make_principal_client("bob", "School B")
    obj_b = model.objects.create(school=client_b.school, **extra)

    response = client_a.get(reverse(update_url, args=[obj_b.pk]))

    assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.parametrize(
    "model,list_url,update_url,delete_url,extra", DIRECT_SCHOOL_RESOURCES
)
def test_post_update_of_another_schools_object_is_404_and_object_unchanged(
    make_principal_client, model, list_url, update_url, delete_url, extra
):
    client_a = make_principal_client("alice", "School A")
    client_b = make_principal_client("bob", "School B")
    obj_b = model.objects.create(school=client_b.school, **extra)

    response = client_a.post(
        reverse(update_url, args=[obj_b.pk]), {**extra, "name": "Hijacked"}
    )

    assert response.status_code == 404
    obj_b.refresh_from_db()
    assert obj_b.name == extra["name"]
    assert obj_b.school == client_b.school


@pytest.mark.django_db
@pytest.mark.parametrize(
    "model,list_url,update_url,delete_url,extra", DIRECT_SCHOOL_RESOURCES
)
def test_get_delete_of_another_schools_object_is_404(
    make_principal_client, model, list_url, update_url, delete_url, extra
):
    client_a = make_principal_client("alice", "School A")
    client_b = make_principal_client("bob", "School B")
    obj_b = model.objects.create(school=client_b.school, **extra)

    response = client_a.get(reverse(delete_url, args=[obj_b.pk]))

    assert response.status_code == 404


@pytest.mark.django_db
@pytest.mark.parametrize(
    "model,list_url,update_url,delete_url,extra", DIRECT_SCHOOL_RESOURCES
)
def test_post_delete_of_another_schools_object_is_404_and_object_remains(
    make_principal_client, model, list_url, update_url, delete_url, extra
):
    client_a = make_principal_client("alice", "School A")
    client_b = make_principal_client("bob", "School B")
    obj_b = model.objects.create(school=client_b.school, **extra)

    response = client_a.post(reverse(delete_url, args=[obj_b.pk]))

    assert response.status_code == 404
    assert model.objects.filter(pk=obj_b.pk).exists()


# (model, create_url, valid_post_data)
CREATE_CASES = [
    (Teacher, "teacher-create", {"name": "Ada", "email": ""}),
    (Room, "room-create", {"name": "A101"}),
    (Subject, "subject-create", {"name": "Math", "code": ""}),
    (StudentGroup, "student-group-create", {"name": "Grade 1"}),
    (AcademicYear, "academic-year-create", {"name": "2026", "default_period_duration": 45}),
]


@pytest.mark.django_db
@pytest.mark.parametrize("model,create_url,data", CREATE_CASES)
def test_create_assigns_current_school_regardless_of_posted_school(
    make_principal_client, model, create_url, data
):
    client_a = make_principal_client("alice", "School A")
    other_school = make_principal_client("bob", "School B").school

    response = client_a.post(reverse(create_url), {**data, "school": other_school.id})

    assert response.status_code == 302
    created = model.objects.get()
    assert created.school == client_a.school
    assert created.school != other_school


@pytest.mark.django_db
@pytest.mark.parametrize("model,create_url,data", CREATE_CASES)
def test_create_form_has_no_school_field(make_principal_client, model, create_url, data):
    client_a = make_principal_client("alice", "School A")

    response = client_a.get(reverse(create_url))

    assert response.status_code == 200
    assert "school" not in response.context["form"].fields


@pytest.mark.django_db
@pytest.mark.parametrize("model,create_url,data", CREATE_CASES)
def test_create_enforces_per_school_name_uniqueness(make_principal_client, model, create_url, data):
    client_a = make_principal_client("alice", "School A")
    model.objects.create(school=client_a.school, **data)

    response = client_a.post(reverse(create_url), data)

    assert response.status_code == 200
    assert response.context["form"].errors
    assert model.objects.filter(school=client_a.school).count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize("model,create_url,data", CREATE_CASES)
def test_create_allows_same_name_in_a_different_school(make_principal_client, model, create_url, data):
    client_a = make_principal_client("alice", "School A")
    other_school = make_principal_client("bob", "School B").school
    model.objects.create(school=other_school, **data)

    response = client_a.post(reverse(create_url), data)

    assert response.status_code == 302
    assert model.objects.filter(school=client_a.school, name=data["name"]).exists()


def _make_year_and_period(school, year_name="2026", period_name="Period 1", order=1):
    year = AcademicYear.objects.create(school=school, name=year_name)
    period = Period.objects.create(
        academic_year=year,
        name=period_name,
        order=order,
        start_time=time(8),
        end_time=time(9),
    )
    return year, period


@pytest.mark.django_db
def test_period_list_only_shows_current_school_periods(make_principal_client):
    client_a = make_principal_client("alice", "School A")
    client_b = make_principal_client("bob", "School B")
    _, period_a = _make_year_and_period(client_a.school, period_name="Period A")
    _, period_b = _make_year_and_period(client_b.school, period_name="Period B")

    response = client_a.get(reverse("period-list"))

    assert response.status_code == 200
    assert b"Period A" in response.content
    assert b"Period B" not in response.content


@pytest.mark.django_db
def test_period_update_of_another_schools_period_is_404(make_principal_client):
    client_a = make_principal_client("alice", "School A")
    client_b = make_principal_client("bob", "School B")
    _, period_b = _make_year_and_period(client_b.school)

    get_response = client_a.get(reverse("period-update", args=[period_b.pk]))
    post_response = client_a.post(
        reverse("period-update", args=[period_b.pk]),
        {
            "academic_year": period_b.academic_year_id,
            "name": "Hijacked",
            "order": period_b.order,
            "start_time": "08:00",
            "end_time": "09:00",
            "kind": Period.Kind.LESSON,
        },
    )

    assert get_response.status_code == 404
    assert post_response.status_code == 404
    period_b.refresh_from_db()
    assert period_b.name != "Hijacked"


@pytest.mark.django_db
def test_period_delete_of_another_schools_period_is_404(make_principal_client):
    client_a = make_principal_client("alice", "School A")
    client_b = make_principal_client("bob", "School B")
    _, period_b = _make_year_and_period(client_b.school)

    get_response = client_a.get(reverse("period-delete", args=[period_b.pk]))
    post_response = client_a.post(reverse("period-delete", args=[period_b.pk]))

    assert get_response.status_code == 404
    assert post_response.status_code == 404
    assert Period.objects.filter(pk=period_b.pk).exists()


def _make_lesson(school, teacher_name="Ada", room_name="A101", subject_name="Math", group_name="Grade 1"):
    _, period = _make_year_and_period(school)
    teacher = Teacher.objects.create(school=school, name=teacher_name)
    room = Room.objects.create(school=school, name=room_name)
    subject = Subject.objects.create(school=school, name=subject_name)
    group = StudentGroup.objects.create(school=school, name=group_name)
    lesson = Lesson.objects.create(
        teacher=teacher,
        subject=subject,
        room=room,
        student_group=group,
        day=Lesson.Day.MONDAY,
        start_period=period,
    )
    return lesson


@pytest.mark.django_db
def test_lesson_list_only_shows_current_school_lessons(make_principal_client):
    client_a = make_principal_client("alice", "School A")
    client_b = make_principal_client("bob", "School B")
    lesson_a = _make_lesson(client_a.school, subject_name="Math A")
    lesson_b = _make_lesson(client_b.school, subject_name="Math B")

    response = client_a.get(reverse("lesson-list"))

    assert response.status_code == 200
    assert b"Math A" in response.content
    assert b"Math B" not in response.content
    assert lesson_a.pk != lesson_b.pk


@pytest.mark.django_db
def test_lesson_update_of_another_schools_lesson_is_404(make_principal_client):
    client_a = make_principal_client("alice", "School A")
    client_b = make_principal_client("bob", "School B")
    lesson_b = _make_lesson(client_b.school)

    get_response = client_a.get(reverse("lesson-update", args=[lesson_b.pk]))

    assert get_response.status_code == 404


@pytest.mark.django_db
def test_lesson_delete_of_another_schools_lesson_is_404(make_principal_client):
    client_a = make_principal_client("alice", "School A")
    client_b = make_principal_client("bob", "School B")
    lesson_b = _make_lesson(client_b.school)

    get_response = client_a.get(reverse("lesson-delete", args=[lesson_b.pk]))
    post_response = client_a.post(reverse("lesson-delete", args=[lesson_b.pk]))

    assert get_response.status_code == 404
    assert post_response.status_code == 404
    assert Lesson.objects.filter(pk=lesson_b.pk).exists()


# --- 4B-4: form queryset isolation -----------------------------------------


@pytest.mark.django_db
def test_period_create_form_only_offers_current_school_academic_years(make_principal_client):
    client_a = make_principal_client("alice", "School A")
    client_b = make_principal_client("bob", "School B")
    year_a = AcademicYear.objects.create(school=client_a.school, name="2026")
    year_b = AcademicYear.objects.create(school=client_b.school, name="2026")

    response = client_a.get(reverse("period-create"))

    offered_ids = {ay.pk for ay in response.context["form"].fields["academic_year"].queryset}
    assert offered_ids == {year_a.pk}
    assert year_b.pk not in offered_ids


@pytest.mark.django_db
def test_period_create_rejects_another_schools_academic_year(make_principal_client):
    client_a = make_principal_client("alice", "School A")
    client_b = make_principal_client("bob", "School B")
    year_b = AcademicYear.objects.create(school=client_b.school, name="2026")

    response = client_a.post(
        reverse("period-create"),
        {
            "academic_year": year_b.pk,
            "name": "Period 1",
            "order": 1,
            "start_time": "08:00",
            "end_time": "09:00",
            "kind": Period.Kind.LESSON,
        },
    )

    assert response.status_code == 200
    assert response.context["form"].errors["academic_year"]
    assert not Period.objects.exists()


@pytest.mark.django_db
def test_period_update_rejects_another_schools_academic_year(make_principal_client):
    client_a = make_principal_client("alice", "School A")
    client_b = make_principal_client("bob", "School B")
    year_a, period_a = _make_year_and_period(client_a.school)
    year_b = AcademicYear.objects.create(school=client_b.school, name="2027")

    response = client_a.post(
        reverse("period-update", args=[period_a.pk]),
        {
            "academic_year": year_b.pk,
            "name": period_a.name,
            "order": period_a.order,
            "start_time": "08:00",
            "end_time": "09:00",
            "kind": Period.Kind.LESSON,
        },
    )

    assert response.status_code == 200
    assert response.context["form"].errors["academic_year"]
    period_a.refresh_from_db()
    assert period_a.academic_year_id == year_a.id


LESSON_FORM_FIELDS = ["teacher", "planned_substitute", "subject", "room", "student_group"]


@pytest.mark.django_db
def test_lesson_create_form_only_offers_current_school_choices(make_principal_client):
    client_a = make_principal_client("alice", "School A")
    client_b = make_principal_client("bob", "School B")
    lesson_a_deps = _make_lesson(client_a.school)
    _make_lesson(client_b.school)

    response = client_a.get(reverse("lesson-create"))
    form = response.context["form"]

    for field_name in LESSON_FORM_FIELDS:
        offered_schools = {obj.school_id for obj in form.fields[field_name].queryset}
        assert offered_schools <= {client_a.school.id}
    offered_period_schools = {
        period.academic_year.school_id
        for period in form.fields["start_period"].queryset.select_related("academic_year")
    }
    assert offered_period_schools <= {client_a.school.id}


@pytest.mark.django_db
@pytest.mark.parametrize("field_name", LESSON_FORM_FIELDS)
def test_lesson_create_rejects_another_schools_resource(make_principal_client, field_name):
    client_a = make_principal_client("alice", "School A")
    client_b = make_principal_client("bob", "School B")
    _, period_a = _make_year_and_period(client_a.school)
    teacher_a = Teacher.objects.create(school=client_a.school, name="Ada")
    room_a = Room.objects.create(school=client_a.school, name="A101")
    subject_a = Subject.objects.create(school=client_a.school, name="Math")
    group_a = StudentGroup.objects.create(school=client_a.school, name="Grade 1")

    foreign_teacher = Teacher.objects.create(school=client_b.school, name="Foreign Teacher")
    foreign_room = Room.objects.create(school=client_b.school, name="Foreign Room")
    foreign_subject = Subject.objects.create(school=client_b.school, name="Foreign Subject")
    foreign_group = StudentGroup.objects.create(school=client_b.school, name="Foreign Group")
    foreign_by_field = {
        "teacher": foreign_teacher.pk,
        "planned_substitute": foreign_teacher.pk,
        "subject": foreign_subject.pk,
        "room": foreign_room.pk,
        "student_group": foreign_group.pk,
    }

    data = {
        "teacher": teacher_a.pk,
        "planned_substitute": "",
        "subject": subject_a.pk,
        "room": room_a.pk,
        "student_group": group_a.pk,
        "day": "MONDAY",
        "start_period": period_a.pk,
        "notes": "",
    }
    data[field_name] = foreign_by_field[field_name]

    response = client_a.post(reverse("lesson-create"), data)

    assert response.status_code == 200
    assert response.context["form"].errors[field_name]
    assert not Lesson.objects.exists()


@pytest.mark.django_db
def test_lesson_create_rejects_another_schools_start_period(make_principal_client):
    client_a = make_principal_client("alice", "School A")
    client_b = make_principal_client("bob", "School B")
    teacher_a = Teacher.objects.create(school=client_a.school, name="Ada")
    room_a = Room.objects.create(school=client_a.school, name="A101")
    subject_a = Subject.objects.create(school=client_a.school, name="Math")
    group_a = StudentGroup.objects.create(school=client_a.school, name="Grade 1")
    _, period_b = _make_year_and_period(client_b.school)

    response = client_a.post(
        reverse("lesson-create"),
        {
            "teacher": teacher_a.pk,
            "planned_substitute": "",
            "subject": subject_a.pk,
            "room": room_a.pk,
            "student_group": group_a.pk,
            "day": "MONDAY",
            "start_period": period_b.pk,
            "notes": "",
        },
    )

    assert response.status_code == 200
    assert response.context["form"].errors["start_period"]
    assert not Lesson.objects.exists()
