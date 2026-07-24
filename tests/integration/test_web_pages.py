from datetime import time

import pytest
from django.contrib.auth import get_user_model
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


@pytest.fixture
def authenticated_client(client):
    user = get_user_model().objects.create_superuser(
        username="scheduler", email="scheduler@example.com", password="test-password"
    )
    client.force_login(user)
    return client


@pytest.fixture
def regular_client(client):
    user = get_user_model().objects.create_user(
        username="viewer", password="test-password"
    )
    client.force_login(user)
    return client


@pytest.fixture
def lesson_form_data(db):
    year = AcademicYear.objects.create(name="2026")
    first = Period.objects.create(
        academic_year=year, name="Period 1", order=1,
        start_time=time(8), end_time=time(9)
    )
    second = Period.objects.create(
        academic_year=year, name="Period 2", order=2,
        start_time=time(9), end_time=time(10)
    )
    return {
        "teacher": Teacher.objects.create(name="Ada"),
        "subject": Subject.objects.create(name="Math"),
        "room": Room.objects.create(name="A101"),
        "student_group": StudentGroup.objects.create(name="Grade 1"),
        "day": "MONDAY",
        "start_period": first,
        "second_period": second,
        "notes": "",
    }


def post_data(values):
    return {
        key: value.pk if hasattr(value, "pk") else value
        for key, value in values.items()
        if key != "second_period"
    }


@pytest.mark.django_db
def test_login_page_renders(client):
    response = client.get(reverse("login"))
    assert response.status_code == 200
    assert b"Login" in response.content


@pytest.mark.django_db
def test_schedule_home_is_public(client):
    response = client.get(reverse("schedule"))
    assert response.status_code == 200
    assert b">Timetable<" in response.content
    assert b"Principal Login" in response.content
    assert reverse("schedule") == "/"


@pytest.mark.django_db
def test_create_period_from_time_input(authenticated_client):
    year = AcademicYear.objects.create(name="2026")
    response = authenticated_client.post(
        reverse("period-create"),
        {
            "academic_year": year.pk,
            "name": "Period 1",
            "order": 1,
            "start_time": "12:00",
            "end_time": "13:00",
            "kind": "LESSON",
        },
    )
    assert response.status_code == 302
    assert Period.objects.filter(academic_year=year, order=1).exists()


@pytest.mark.django_db
def test_invalid_period_time_returns_form_errors(authenticated_client):
    year = AcademicYear.objects.create(name="2026")
    response = authenticated_client.post(
        reverse("period-create"),
        {
            "academic_year": year.pk,
            "name": "Period 1",
            "order": 1,
            "start_time": "invalid",
            "end_time": "invalid",
            "kind": "LESSON",
        },
    )
    assert response.status_code == 200
    assert response.context["form"].errors["start_time"] == ["Enter a valid time."]
    assert response.context["form"].errors["end_time"] == ["Enter a valid time."]


@pytest.mark.django_db
def test_schedule_uses_period_columns_and_breaks(authenticated_client):
    year = AcademicYear.objects.create(name="2026")
    Period.objects.create(
        academic_year=year, name="Morning Break", order=1,
        start_time=time(10), end_time=time(10, 30), kind=Period.Kind.BREAK
    )
    response = authenticated_client.get(
        reverse("schedule"), {"view": "whole_school", "academic_year": year.pk}
    )
    assert response.status_code == 200
    assert b"Morning Break" in response.content
    assert len(response.context["periods"]) == 1


@pytest.mark.django_db
def test_lesson_form_writes_through_service(authenticated_client, lesson_form_data):
    response = authenticated_client.post(reverse("lesson-create"), post_data(lesson_form_data))
    assert response.status_code == 302
    lesson = Lesson.objects.get()
    assert lesson.day == "MONDAY"
    assert lesson.start_period == lesson_form_data["start_period"]


@pytest.mark.django_db
def test_lesson_form_returns_conflict_on_same_teacher(authenticated_client, lesson_form_data):
    authenticated_client.post(reverse("lesson-create"), post_data(lesson_form_data))
    response = authenticated_client.post(reverse("lesson-create"), post_data(lesson_form_data))
    assert response.status_code == 200
    assert "Teacher is already teaching then." in response.context["form"].errors["teacher"]
    assert Lesson.objects.count() == 1


@pytest.mark.django_db
def test_whole_school_cards_use_compact_names_and_omit_room(
    authenticated_client, lesson_form_data
):
    lesson_form_data["subject"].name = "Mathematics"
    lesson_form_data["subject"].save()
    lesson_form_data["teacher"].name = "Teacher Bobby"
    lesson_form_data["teacher"].save()
    lesson_form_data["student_group"].name = "EP1"
    lesson_form_data["student_group"].save()
    authenticated_client.post(reverse("lesson-create"), post_data(lesson_form_data))

    response = authenticated_client.get(
        reverse("schedule"),
        {
            "view": "whole_school",
            "academic_year": lesson_form_data["start_period"].academic_year_id,
        },
    )

    assert b"<strong>Math</strong>" in response.content
    assert b"Bobby" in response.content
    assert b"EP1" in response.content
    assert b"A101" not in response.content


@pytest.mark.django_db
def test_focused_timetable_uses_adaptive_lesson_cards(
    authenticated_client, lesson_form_data
):
    authenticated_client.post(reverse("lesson-create"), post_data(lesson_form_data))

    response = authenticated_client.get(
        reverse("schedule"),
        {
            "view": "teacher",
            "teacher": lesson_form_data["teacher"].pk,
            "academic_year": lesson_form_data["start_period"].academic_year_id,
        },
    )

    assert b"<table" in response.content
    assert b"lesson-card" in response.content
    assert b"A101" in response.content
    assert b"Grade 1" in response.content
    assert b'>Ada</span>' not in response.content
    assert b'<div class="whole-school-grid"' not in response.content


@pytest.mark.django_db
def test_schedule_defaults_to_latest_academic_year(authenticated_client):
    older = AcademicYear.objects.create(name="2025")
    newer = AcademicYear.objects.create(name="2026")
    Period.objects.create(
        academic_year=older,
        name="Old Period",
        order=1,
        start_time=time(8),
        end_time=time(9),
    )
    Period.objects.create(
        academic_year=newer,
        name="Current Period",
        order=1,
        start_time=time(8),
        end_time=time(9),
    )

    response = authenticated_client.get(reverse("schedule"), {"view": "whole_school"})

    assert response.context["selected_academic_year"] == str(newer.pk)
    assert b"Current Period" in response.content
    assert b"Old Period" not in response.content


@pytest.mark.django_db
def test_timetable_lessons_link_to_existing_edit_flow(
    authenticated_client, lesson_form_data
):
    authenticated_client.post(reverse("lesson-create"), post_data(lesson_form_data))
    lesson = Lesson.objects.get()

    response = authenticated_client.get(
        reverse("schedule"),
        {
            "view": "teacher",
            "teacher": lesson_form_data["teacher"].pk,
            "academic_year": lesson_form_data["start_period"].academic_year_id,
        },
    )

    assert reverse("lesson-update", args=[lesson.pk]).encode() in response.content


@pytest.mark.django_db
def test_timetable_displays_planned_substitute(
    authenticated_client, lesson_form_data
):
    substitute = Teacher.objects.create(name="Grace")
    Lesson.objects.create(
        teacher=lesson_form_data["teacher"],
        planned_substitute=substitute,
        subject=lesson_form_data["subject"],
        room=lesson_form_data["room"],
        student_group=lesson_form_data["student_group"],
        day="MONDAY",
        start_period=lesson_form_data["start_period"],
    )

    response = authenticated_client.get(
        reverse("schedule"),
        {
            "view": "teacher",
            "teacher": lesson_form_data["teacher"].pk,
            "academic_year": lesson_form_data["start_period"].academic_year_id,
        },
    )

    assert b"Sub: Grace" in response.content


@pytest.mark.django_db
def test_whole_school_cards_link_to_edit_and_display_planned_substitute(
    authenticated_client, lesson_form_data
):
    substitute = Teacher.objects.create(name="Grace")
    lesson = Lesson.objects.create(
        teacher=lesson_form_data["teacher"],
        planned_substitute=substitute,
        subject=lesson_form_data["subject"],
        room=lesson_form_data["room"],
        student_group=lesson_form_data["student_group"],
        day="MONDAY",
        start_period=lesson_form_data["start_period"],
    )

    response = authenticated_client.get(
        reverse("schedule"),
        {
            "view": "whole_school",
            "academic_year": lesson_form_data["start_period"].academic_year_id,
        },
    )

    assert reverse("lesson-update", args=[lesson.pk]).encode() in response.content
    assert b"Sub: Grace" in response.content


@pytest.mark.django_db
def test_schedule_shows_generate_planned_substitutions_button(
    authenticated_client, lesson_form_data
):
    response = authenticated_client.get(
        reverse("schedule"),
        {
            "view": "whole_school",
            "academic_year": lesson_form_data["start_period"].academic_year_id,
        },
    )

    assert b"Generate Planned Substitutions" in response.content
    assert reverse("generate-planned-substitutions").encode() in response.content


@pytest.mark.django_db
def test_generation_buttons_require_confirmation(authenticated_client, lesson_form_data):
    response = authenticated_client.get(
        reverse("schedule"),
        {
            "view": "whole_school",
            "academic_year": lesson_form_data["start_period"].academic_year_id,
        },
    )

    assert b"return confirm(" in response.content
    assert b"Generate planned substitutions?" in response.content
    assert b"Existing automatically generated substitutions may be replaced." in response.content


@pytest.mark.django_db
def test_generate_planned_substitutions_updates_timetable(
    authenticated_client, lesson_form_data
):
    substitute = Teacher.objects.create(name="Grace")
    Lesson.objects.create(
        teacher=lesson_form_data["teacher"],
        subject=lesson_form_data["subject"],
        room=lesson_form_data["room"],
        student_group=lesson_form_data["student_group"],
        day="MONDAY",
        start_period=lesson_form_data["start_period"],
    )
    next_url = (
        reverse("schedule")
        + f"?view=teacher&teacher={lesson_form_data['teacher'].pk}"
        + f"&academic_year={lesson_form_data['start_period'].academic_year_id}"
    )

    response = authenticated_client.post(
        reverse("generate-planned-substitutions"),
        {
            "academic_year": lesson_form_data["start_period"].academic_year_id,
            "next": next_url,
        },
        follow=True,
    )

    lesson = Lesson.objects.get()
    assert lesson.planned_substitute == substitute
    assert response.redirect_chain == [(next_url, 302)]
    assert b"Planned substitutions generated." in response.content
    assert b"Sub: Grace" in response.content


@pytest.mark.django_db
def test_lesson_edit_form_displays_current_substitution_teacher(
    authenticated_client, lesson_form_data
):
    substitute = Teacher.objects.create(name="Grace")
    lesson = Lesson.objects.create(
        teacher=lesson_form_data["teacher"],
        planned_substitute=substitute,
        subject=lesson_form_data["subject"],
        room=lesson_form_data["room"],
        student_group=lesson_form_data["student_group"],
        day="MONDAY",
        start_period=lesson_form_data["start_period"],
    )

    response = authenticated_client.get(reverse("lesson-update", args=[lesson.pk]))

    assert response.status_code == 200
    assert b"Substitution Teacher" in response.content
    assert b"No substitution teacher" in response.content
    assert f'value="{substitute.pk}" selected'.encode() in response.content


@pytest.mark.django_db
def test_lesson_edit_can_add_substitution_teacher(authenticated_client, lesson_form_data):
    substitute = Teacher.objects.create(name="Grace")
    lesson = Lesson.objects.create(
        teacher=lesson_form_data["teacher"],
        subject=lesson_form_data["subject"],
        room=lesson_form_data["room"],
        student_group=lesson_form_data["student_group"],
        day="MONDAY",
        start_period=lesson_form_data["start_period"],
    )
    data = post_data(lesson_form_data)
    data["planned_substitute"] = substitute.pk

    response = authenticated_client.post(reverse("lesson-update", args=[lesson.pk]), data)

    lesson.refresh_from_db()
    assert response.status_code == 302
    assert lesson.planned_substitute == substitute


@pytest.mark.django_db
def test_lesson_edit_can_change_substitution_teacher(authenticated_client, lesson_form_data):
    original = Teacher.objects.create(name="Grace")
    replacement = Teacher.objects.create(name="Katherine")
    lesson = Lesson.objects.create(
        teacher=lesson_form_data["teacher"],
        planned_substitute=original,
        subject=lesson_form_data["subject"],
        room=lesson_form_data["room"],
        student_group=lesson_form_data["student_group"],
        day="MONDAY",
        start_period=lesson_form_data["start_period"],
    )
    data = post_data(lesson_form_data)
    data["planned_substitute"] = replacement.pk

    response = authenticated_client.post(reverse("lesson-update", args=[lesson.pk]), data)

    lesson.refresh_from_db()
    assert response.status_code == 302
    assert lesson.planned_substitute == replacement


@pytest.mark.django_db
def test_lesson_edit_can_remove_substitution_teacher(authenticated_client, lesson_form_data):
    substitute = Teacher.objects.create(name="Grace")
    lesson = Lesson.objects.create(
        teacher=lesson_form_data["teacher"],
        planned_substitute=substitute,
        subject=lesson_form_data["subject"],
        room=lesson_form_data["room"],
        student_group=lesson_form_data["student_group"],
        day="MONDAY",
        start_period=lesson_form_data["start_period"],
    )
    data = post_data(lesson_form_data)
    data["planned_substitute"] = ""

    response = authenticated_client.post(reverse("lesson-update", args=[lesson.pk]), data)

    lesson.refresh_from_db()
    assert response.status_code == 302
    assert lesson.planned_substitute is None


@pytest.mark.django_db
def test_lesson_edit_validates_substitution_teacher(authenticated_client, lesson_form_data):
    lesson = Lesson.objects.create(
        teacher=lesson_form_data["teacher"],
        subject=lesson_form_data["subject"],
        room=lesson_form_data["room"],
        student_group=lesson_form_data["student_group"],
        day="MONDAY",
        start_period=lesson_form_data["start_period"],
    )
    data = post_data(lesson_form_data)
    data["planned_substitute"] = "9999"

    response = authenticated_client.post(reverse("lesson-update", args=[lesson.pk]), data)

    lesson.refresh_from_db()
    assert response.status_code == 200
    assert "Select a valid choice." in response.context["form"].errors["planned_substitute"][0]
    assert lesson.planned_substitute is None


@pytest.mark.django_db
def test_existing_lesson_editing_continues_to_update_core_fields(
    authenticated_client, lesson_form_data
):
    new_room = Room.objects.create(name="B202")
    lesson = Lesson.objects.create(
        teacher=lesson_form_data["teacher"],
        subject=lesson_form_data["subject"],
        room=lesson_form_data["room"],
        student_group=lesson_form_data["student_group"],
        day="MONDAY",
        start_period=lesson_form_data["start_period"],
    )
    data = post_data(lesson_form_data)
    data["room"] = new_room.pk
    data["notes"] = "Bring lab materials."

    response = authenticated_client.post(reverse("lesson-update", args=[lesson.pk]), data)

    lesson.refresh_from_db()
    assert response.status_code == 302
    assert lesson.room == new_room
    assert lesson.notes == "Bring lab materials."


@pytest.mark.django_db
def test_schedule_starts_with_view_choices_and_no_timetable(authenticated_client):
    AcademicYear.objects.create(name="2026")

    response = authenticated_client.get(reverse("schedule"))

    assert response.status_code == 200
    assert response.context["page"].waiting_for_view is True
    assert response.context["page"].show_timetable is False
    assert response.context["rows"] == []
    assert b"Choose what you want to view" in response.content
    assert b"<table" not in response.content


@pytest.mark.django_db
def test_teacher_view_only_exposes_teacher_selector(authenticated_client):
    AcademicYear.objects.create(name="2026")
    Teacher.objects.create(name="Ada")
    Room.objects.create(name="A101")
    StudentGroup.objects.create(name="Grade 1")

    response = authenticated_client.get(reverse("schedule"), {"view": "teacher"})

    selector = response.context["page"].selector
    assert selector.name == "teacher"
    assert response.context["page"].waiting_for_selection is True
    assert b'name="teacher"' in response.content
    assert b'name="room"' not in response.content
    assert b'name="student_group"' not in response.content


@pytest.mark.django_db
def test_administrator_navigation(authenticated_client):
    response = authenticated_client.get(reverse("schedule"))

    assert response.status_code == 200
    assert b">Timetable<" in response.content
    assert b">Lessons<" in response.content
    assert b">Admin<" in response.content
    assert b">Teacher Substitution<" not in response.content
    assert b">Teachers<" not in response.content
    assert b">Rooms<" not in response.content


@pytest.mark.django_db
def test_regular_user_navigation(regular_client):
    response = regular_client.get(reverse("schedule"))

    assert response.status_code == 200
    assert b">Timetable<" in response.content
    assert b">Teacher Substitution<" not in response.content
    assert b">Lessons<" not in response.content
    assert b">Admin<" not in response.content
    assert b"Whole School" not in response.content


@pytest.mark.django_db
def test_teacher_substitution_lookup_requires_principal(regular_client):
    assert regular_client.get(reverse("teacher-substitution")).status_code == 403


@pytest.mark.django_db
def test_administrator_can_access_django_admin(authenticated_client):
    assert authenticated_client.get(reverse("admin:index")).status_code == 200
    assert authenticated_client.get(reverse("admin:app_teacher_changelist")).status_code == 200


@pytest.mark.django_db
def test_regular_user_cannot_access_administration_pages(regular_client):
    assert regular_client.get(reverse("admin:index")).status_code == 302
    assert regular_client.get(reverse("lesson-list")).status_code == 403
    assert regular_client.get(reverse("teacher-list")).status_code == 403
    assert regular_client.get(reverse("schedule"), {"view": "whole_school"}).status_code == 403


@pytest.mark.django_db
def test_public_user_cannot_access_administration_pages(client):
    assert client.get(reverse("lesson-list")).status_code == 302
    assert client.get(reverse("teacher-list")).status_code == 302
    assert client.get(reverse("generate-planned-substitutions")).status_code == 302
    assert client.post(reverse("generate-planned-substitutions")).status_code == 302


@pytest.mark.django_db
def test_public_user_can_access_focused_schedule(client):
    year = AcademicYear.objects.create(name="2026")
    teacher = Teacher.objects.create(name="Ada")

    response = client.get(
        reverse("schedule"),
        {"view": "teacher", "teacher": teacher.pk, "academic_year": year.pk},
    )

    assert response.status_code == 200
    assert response.context["page"].current_view == "teacher"


@pytest.mark.django_db
def test_public_user_can_access_student_group_and_room_schedules(client):
    year = AcademicYear.objects.create(name="2026")
    student_group = StudentGroup.objects.create(name="Grade 1")
    room = Room.objects.create(name="A101")

    student_group_response = client.get(
        reverse("schedule"),
        {
            "view": "student_group",
            "student_group": student_group.pk,
            "academic_year": year.pk,
        },
    )
    room_response = client.get(
        reverse("schedule"),
        {
            "view": "room",
            "room": room.pk,
            "academic_year": year.pk,
        },
    )

    assert student_group_response.status_code == 200
    assert room_response.status_code == 200


@pytest.mark.django_db
def test_public_user_cannot_access_whole_school_schedule(client):
    AcademicYear.objects.create(name="2026")

    response = client.get(reverse("schedule"), {"view": "whole_school"})

    assert response.status_code == 403


@pytest.mark.django_db
def test_teacher_substitution_form_submission_lists_available_teachers(
    authenticated_client, lesson_form_data
):
    busy_teacher = lesson_form_data["teacher"]
    free_teacher = Teacher.objects.create(name="Grace")
    Lesson.objects.create(
        teacher=busy_teacher,
        subject=lesson_form_data["subject"],
        room=lesson_form_data["room"],
        student_group=lesson_form_data["student_group"],
        day="MONDAY",
        start_period=lesson_form_data["start_period"],
    )

    response = authenticated_client.get(
        reverse("teacher-substitution"),
        {
            "academic_year": lesson_form_data["start_period"].academic_year_id,
            "day": "MONDAY",
            "period": lesson_form_data["start_period"].pk,
        },
    )

    assert response.status_code == 200
    assert [teacher.name for teacher in response.context["available_teachers"]] == [
        free_teacher.name
    ]
    assert free_teacher.name.encode() in response.content
    assert busy_teacher.name.encode() not in response.content
