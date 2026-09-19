from datetime import time

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from app.infrastructure.database.models import (
    AcademicYear,
    Lesson,
    Period,
    Room,
    School,
    StudentGroup,
    Subject,
    Teacher,
)


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


def _make_lesson(
    school, teacher_name="Ada", room_name="A101", subject_name="Math", group_name="Grade 1"
):
    year, period = _make_year_and_period(school)
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
    return year, period, lesson


# --- 4C-5: GeneratePlannedSubstitutionsView -------------------------------


@pytest.mark.django_db
def test_generate_planned_substitutions_rejects_another_schools_academic_year(
    make_principal_client,
):
    client_a = make_principal_client("alice", "School A")
    client_b = make_principal_client("bob", "School B")
    year_b, period_b, lesson_b = _make_lesson(client_b.school)
    Teacher.objects.create(school=client_b.school, name="Substitute")

    response = client_a.post(
        reverse("generate-planned-substitutions"), {"academic_year": year_b.pk}
    )

    assert response.status_code == 302
    # Fresh query, not just the response: the mutation must not have happened.
    refetched = Lesson.objects.get(pk=lesson_b.pk)
    assert refetched.planned_substitute_id is None


@pytest.mark.django_db
def test_generate_planned_substitutions_rejects_nonexistent_academic_year(
    make_principal_client,
):
    client_a = make_principal_client("alice", "School A")

    response = client_a.post(
        reverse("generate-planned-substitutions"), {"academic_year": 999999}
    )

    assert response.status_code == 302


@pytest.mark.django_db
def test_generate_planned_substitutions_still_works_for_current_school(
    make_principal_client,
):
    client_a = make_principal_client("alice", "School A")
    year_a, period_a, lesson_a = _make_lesson(client_a.school)
    Teacher.objects.create(school=client_a.school, name="Substitute Teacher")

    response = client_a.post(
        reverse("generate-planned-substitutions"), {"academic_year": year_a.pk}
    )

    assert response.status_code == 302
    refetched = Lesson.objects.get(pk=lesson_a.pk)
    assert refetched.planned_substitute_id is not None


# --- 4C-3: StaffScheduleView ------------------------------------------------


@pytest.mark.django_db
def test_staff_schedule_shows_current_school_data(make_principal_client):
    client_a = make_principal_client("alice", "School A")
    year_a, period_a, lesson_a = _make_lesson(client_a.school, teacher_name="Ada A")

    response = client_a.get(
        reverse("staff-schedule"),
        {"academic_year": year_a.pk, "day": "MONDAY", "period": period_a.pk},
    )

    assert response.status_code == 200
    assert response.context["staff_schedule"] is not None
    assert response.context["selected_slot"] is not None
    assert b"Ada A" in response.content


@pytest.mark.django_db
def test_staff_schedule_rejects_another_schools_academic_year(make_principal_client):
    client_a = make_principal_client("alice", "School A")
    client_b = make_principal_client("bob", "School B")
    year_b, period_b, lesson_b = _make_lesson(client_b.school, teacher_name="Bob B")

    response = client_a.get(reverse("staff-schedule"), {"academic_year": year_b.pk})

    assert response.status_code == 200
    assert response.context["staff_schedule"] is None
    assert response.context["selected_academic_year"] == ""
    assert b"Bob B" not in response.content


@pytest.mark.django_db
def test_staff_schedule_defaults_to_current_schools_academic_year(make_principal_client):
    client_a = make_principal_client("alice", "School A")
    client_b = make_principal_client("bob", "School B")
    year_a, period_a, lesson_a = _make_lesson(client_a.school, teacher_name="Ada A")
    _make_lesson(client_b.school, teacher_name="Bob B")

    response = client_a.get(
        reverse("staff-schedule"), {"day": "MONDAY", "period": period_a.pk}
    )

    assert response.status_code == 200
    assert response.context["selected_academic_year"] == str(year_a.pk)
    assert b"Ada A" in response.content
    assert b"Bob B" not in response.content


# --- 4C-4: TeacherSubstitutionForm/View ------------------------------------


@pytest.mark.django_db
def test_teacher_substitution_form_only_offers_current_school_choices(make_principal_client):
    client_a = make_principal_client("alice", "School A")
    client_b = make_principal_client("bob", "School B")
    year_a, period_a = _make_year_and_period(client_a.school)
    year_b, period_b = _make_year_and_period(client_b.school)

    response = client_a.get(reverse("teacher-substitution"))
    form = response.context["form"]

    assert list(form.fields["academic_year"].queryset) == [year_a]
    assert list(form.fields["period"].queryset) == [period_a]


@pytest.mark.django_db
def test_teacher_substitution_rejects_another_schools_academic_year(make_principal_client):
    client_a = make_principal_client("alice", "School A")
    client_b = make_principal_client("bob", "School B")
    year_b, period_b = _make_year_and_period(client_b.school)

    response = client_a.get(
        reverse("teacher-substitution"),
        {"academic_year": year_b.pk, "day": "MONDAY", "period": period_b.pk},
    )

    assert response.status_code == 200
    assert response.context["available_teachers"] is None
    assert response.context["form"].errors["academic_year"]


@pytest.mark.django_db
def test_teacher_substitution_rejects_another_schools_period(make_principal_client):
    client_a = make_principal_client("alice", "School A")
    client_b = make_principal_client("bob", "School B")
    year_a, period_a = _make_year_and_period(client_a.school)
    year_b, period_b = _make_year_and_period(client_b.school)

    response = client_a.get(
        reverse("teacher-substitution"),
        {"academic_year": year_a.pk, "day": "MONDAY", "period": period_b.pk},
    )

    assert response.status_code == 200
    assert response.context["available_teachers"] is None
    assert response.context["form"].errors["period"]


@pytest.mark.django_db
def test_teacher_substitution_still_works_for_current_school(make_principal_client):
    client_a = make_principal_client("alice", "School A")
    year_a, period_a, lesson_a = _make_lesson(client_a.school, teacher_name="Busy Teacher")
    Teacher.objects.create(school=client_a.school, name="Free Teacher")

    response = client_a.get(
        reverse("teacher-substitution"),
        {"academic_year": year_a.pk, "day": "MONDAY", "period": period_a.pk},
    )

    assert response.status_code == 200
    available_names = {teacher.name for teacher in response.context["available_teachers"]}
    assert available_names == {"Free Teacher"}


# --- 4C-2: ScheduleView -----------------------------------------------------


@pytest.mark.django_db
def test_schedule_academic_year_selector_only_offers_current_school(make_principal_client):
    client_a = make_principal_client("alice", "School A")
    client_b = make_principal_client("bob", "School B")
    year_a, period_a, lesson_a = _make_lesson(client_a.school, subject_name="Math A")
    year_b, period_b, lesson_b = _make_lesson(client_b.school, subject_name="Math B")

    response = client_a.get(reverse("schedule"), {"view": "student_group"})

    assert list(response.context["academic_years"]) == [year_a]


@pytest.mark.django_db
def test_schedule_ignores_another_schools_academic_year_id(make_principal_client):
    client_a = make_principal_client("alice", "School A")
    client_b = make_principal_client("bob", "School B")
    year_a, period_a, lesson_a = _make_lesson(client_a.school, subject_name="Math A")
    year_b, period_b, lesson_b = _make_lesson(client_b.school, subject_name="Math B")

    response = client_a.get(
        reverse("schedule"),
        {"view": "student_group", "academic_year": year_b.pk},
    )

    # A foreign academic_year id must not be honoured — falls back to
    # the current school's own academic year instead of School B's.
    assert response.context["selected_academic_year"] == str(year_a.pk)
    assert b"Math B" not in response.content


@pytest.mark.django_db
def test_schedule_selector_rejects_another_schools_resource_id(make_principal_client):
    client_a = make_principal_client("alice", "School A")
    client_b = make_principal_client("bob", "School B")
    year_a, period_a, lesson_a = _make_lesson(client_a.school, teacher_name="Ada A")
    year_b, period_b, lesson_b = _make_lesson(client_b.school, teacher_name="Bob B")
    foreign_teacher = lesson_b.teacher

    response = client_a.get(
        reverse("schedule"),
        {"view": "teacher", "teacher": foreign_teacher.pk, "academic_year": year_a.pk},
    )

    selector = response.context["page"].selector
    assert selector.selected == ""
    assert response.context["page"].waiting_for_selection is True
    assert b"Bob B" not in response.content


@pytest.mark.django_db
def test_schedule_still_works_for_current_school(make_principal_client):
    client_a = make_principal_client("alice", "School A")
    year_a, period_a, lesson_a = _make_lesson(client_a.school, teacher_name="Ada A")

    response = client_a.get(
        reverse("schedule"),
        {
            "view": "teacher",
            "teacher": lesson_a.teacher_id,
            "academic_year": year_a.pk,
        },
    )

    assert response.status_code == 200
    assert response.context["page"].show_timetable is True
    assert response.context["page"].selector.selected == str(lesson_a.teacher_id)
    assert response.context["selected_academic_year"] == str(year_a.pk)


@pytest.mark.django_db
def test_non_staff_principal_can_use_whole_school_view(make_principal_client):
    # Phase 4D: whole_school authorization is current-school-based, not
    # is_staff-based — a real, non-staff principal must be able to use it.
    client_a = make_principal_client("alice", "School A")
    year_a, period_a, lesson_a = _make_lesson(client_a.school, subject_name="Math A")

    response = client_a.get(
        reverse("schedule"), {"view": "whole_school", "academic_year": year_a.pk}
    )

    assert response.status_code == 200
    assert b"Math A" in response.content


@pytest.mark.django_db
def test_whole_school_view_scoped_to_current_school_for_non_staff_principal(
    make_principal_client,
):
    client_a = make_principal_client("alice", "School A")
    client_b = make_principal_client("bob", "School B")
    year_a, period_a, lesson_a = _make_lesson(client_a.school, subject_name="Math A")
    year_b, period_b, lesson_b = _make_lesson(client_b.school, subject_name="Math B")

    response = client_a.get(
        reverse("schedule"), {"view": "whole_school", "academic_year": year_b.pk}
    )

    assert response.status_code == 200
    assert b"Math B" not in response.content


@pytest.mark.django_db
def test_is_staff_without_membership_cannot_use_whole_school_view(client):
    # The vulnerability found during the Phase 4D audit: an is_staff
    # account with zero SchoolMembership rows must not be able to use
    # whole_school just because is_staff=True — is_staff is a Django
    # Admin privilege, not an application school-management context.
    staff_user = get_user_model().objects.create_user(
        username="dev", password="x", is_staff=True
    )
    client.force_login(staff_user)

    other_school = School.objects.create(name="Victim School")
    year, period, lesson = _make_lesson(other_school, subject_name="Secret Subject")

    response = client.get(
        reverse("schedule"), {"view": "whole_school", "academic_year": year.pk}
    )

    assert response.status_code == 403
    assert b"Secret Subject" not in response.content


# --- 4D-3: schedule.html application actions -------------------------------


@pytest.mark.django_db
def test_non_staff_principal_sees_and_can_use_application_actions(make_principal_client):
    client_a = make_principal_client("alice", "School A")
    year_a, period_a, lesson_a = _make_lesson(client_a.school)
    Teacher.objects.create(school=client_a.school, name="Substitute Teacher")

    response = client_a.get(
        reverse("schedule"), {"view": "whole_school", "academic_year": year_a.pk}
    )

    assert response.status_code == 200
    assert b"Add Lesson" in response.content
    assert b"Generate Planned Substitutions" in response.content
    # The lesson card is a clickable edit link, not a plain div.
    assert reverse("lesson-update", args=[lesson_a.pk]).encode() in response.content

    # And the actions actually work end-to-end, not just visually.
    generate_response = client_a.post(
        reverse("generate-planned-substitutions"), {"academic_year": year_a.pk}
    )
    assert generate_response.status_code == 302
    lesson_a.refresh_from_db()
    assert lesson_a.planned_substitute_id is not None


@pytest.mark.django_db
def test_is_staff_without_membership_does_not_see_application_actions(client):
    staff_user = get_user_model().objects.create_user(
        username="dev", password="x", is_staff=True
    )
    client.force_login(staff_user)

    response = client.get(reverse("schedule"))

    assert response.status_code == 200
    assert b"Add Lesson" not in response.content
    assert b"Generate Planned Substitutions" not in response.content
