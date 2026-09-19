from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from app.domain.models import Day
from app.infrastructure.database.models import (
    AcademicYear,
    Lesson,
    Period,
    Room,
    School,
    SchoolMembership,
    StudentGroup,
    Subject,
    Teacher,
)

SCHOOL_NAMES = ("Riverside High", "Lincoln Academy")
USERNAMES = ("principal_riverside", "principal_lincoln")


@pytest.mark.django_db
def test_load_demo_data_creates_two_independent_schools_with_principals():
    output = StringIO()

    call_command("load_demo_data", stdout=output)

    assert School.objects.count() == 2
    assert set(School.objects.values_list("name", flat=True)) == set(SCHOOL_NAMES)
    assert get_user_model().objects.count() == 2
    assert set(get_user_model().objects.values_list("username", flat=True)) == set(USERNAMES)
    assert SchoolMembership.objects.count() == 2
    for membership in SchoolMembership.objects.select_related("user", "school"):
        assert membership.role == SchoolMembership.Role.PRINCIPAL
        assert membership.school.name in SCHOOL_NAMES
    assert "Login credentials:" in output.getvalue()
    assert "principal_riverside" in output.getvalue()
    assert "principal_lincoln" in output.getvalue()


@pytest.mark.django_db
@pytest.mark.parametrize("school_name", SCHOOL_NAMES)
def test_load_demo_data_creates_complete_data_for_each_school(school_name):
    call_command("load_demo_data", stdout=StringIO())

    school = School.objects.get(name=school_name)
    academic_year = AcademicYear.objects.get(school=school)

    assert academic_year.name == "Demo 2026"
    assert Teacher.objects.filter(school=school).count() == 16
    assert StudentGroup.objects.filter(school=school).count() == 10
    assert Room.objects.filter(school=school).count() == 10
    assert Subject.objects.filter(school=school).count() == 10
    assert Period.objects.filter(academic_year=academic_year).count() == 12
    assert Period.objects.filter(
        academic_year=academic_year, kind=Period.Kind.LESSON
    ).count() == 10
    assert Period.objects.filter(
        academic_year=academic_year, kind=Period.Kind.BREAK
    ).count() == 2
    assert Lesson.objects.filter(start_period__academic_year=academic_year).count() == 500


@pytest.mark.django_db
def test_load_demo_data_reuses_identical_names_across_independent_schools():
    call_command("load_demo_data", stdout=StringIO())

    academic_years = AcademicYear.objects.all()
    assert academic_years.count() == 2
    assert set(academic_years.values_list("name", flat=True)) == {"Demo 2026"}

    # Same teacher/subject/room/student-group names exist in both
    # schools, as separate rows — this is the point: the application
    # must keep them independent because they belong to different
    # Schools, not because the names differ.
    for model, name in [
        (Teacher, "Alice Chen"),
        (Subject, "Math"),
        (Room, "Room 101"),
        (StudentGroup, "Grade 7A"),
    ]:
        rows = model.objects.filter(name=name)
        assert rows.count() == 2
        assert {row.school_id for row in rows} == set(School.objects.values_list("id", flat=True))


@pytest.mark.django_db
def test_load_demo_data_is_idempotent():
    call_command("load_demo_data", stdout=StringIO())
    call_command("load_demo_data", stdout=StringIO())

    assert School.objects.count() == 2
    assert get_user_model().objects.count() == 2
    assert SchoolMembership.objects.count() == 2
    assert AcademicYear.objects.count() == 2
    for school in School.objects.all():
        assert Teacher.objects.filter(school=school).count() == 16
        assert StudentGroup.objects.filter(school=school).count() == 10
        assert Room.objects.filter(school=school).count() == 10
        academic_year = AcademicYear.objects.get(school=school)
        assert Lesson.objects.filter(start_period__academic_year=academic_year).count() == 500


@pytest.mark.django_db
def test_load_demo_data_does_not_touch_unrelated_existing_data():
    unrelated_school = School.objects.create(name="Some Other School")
    unrelated_year = AcademicYear.objects.create(school=unrelated_school, name="2027")
    unrelated_teacher = Teacher.objects.create(school=unrelated_school, name="Manual Teacher")

    call_command("load_demo_data", stdout=StringIO())

    unrelated_year.refresh_from_db()
    unrelated_teacher.refresh_from_db()
    assert Period.objects.filter(academic_year=unrelated_year).count() == 0
    assert Lesson.objects.filter(start_period__academic_year=unrelated_year).count() == 0
    assert Teacher.objects.filter(school=unrelated_school).count() == 1
    assert School.objects.filter(name="Some Other School").exists()
    assert School.objects.count() == 3


@pytest.mark.django_db
@pytest.mark.parametrize("school_name", SCHOOL_NAMES)
def test_load_demo_data_generates_conflict_free_timetable_per_school(school_name):
    call_command("load_demo_data", stdout=StringIO())

    school = School.objects.get(name=school_name)
    academic_year = AcademicYear.objects.get(school=school)
    teaching_period_count = Period.objects.filter(
        academic_year=academic_year, kind=Period.Kind.LESSON
    ).count()

    for student_group in StudentGroup.objects.filter(school=school):
        assert Lesson.objects.filter(student_group=student_group).count() == (
            teaching_period_count * 5
        )

    for day, period_id in Lesson.objects.filter(
        start_period__academic_year=academic_year
    ).values_list("day", "start_period_id").distinct():
        slot_lessons = Lesson.objects.filter(
            start_period__academic_year=academic_year, day=day, start_period_id=period_id
        )
        assert slot_lessons.values("teacher_id").distinct().count() == slot_lessons.count()
        assert slot_lessons.values("room_id").distinct().count() == slot_lessons.count()
        assert slot_lessons.values("student_group_id").distinct().count() == (
            slot_lessons.count()
        )

    assert not Lesson.objects.filter(
        start_period__academic_year=academic_year, start_period__kind=Period.Kind.BREAK
    ).exists()


@pytest.mark.django_db
@pytest.mark.parametrize("school_name", SCHOOL_NAMES)
def test_load_demo_data_generates_some_planned_substitutions_per_school(school_name):
    call_command("load_demo_data", stdout=StringIO())

    school = School.objects.get(name=school_name)
    academic_year = AcademicYear.objects.get(school=school)

    assert Lesson.objects.filter(
        start_period__academic_year=academic_year, planned_substitute__isnull=False
    ).exists()


@pytest.mark.django_db
def test_load_demo_data_never_mixes_lessons_across_the_two_schools():
    call_command("load_demo_data", stdout=StringIO())

    riverside = School.objects.get(name="Riverside High")
    lincoln = School.objects.get(name="Lincoln Academy")

    riverside_lessons = Lesson.objects.filter(
        start_period__academic_year__school=riverside
    )
    for lesson in riverside_lessons.select_related(
        "teacher", "room", "subject", "student_group"
    ):
        assert lesson.teacher.school_id == riverside.id
        assert lesson.room.school_id == riverside.id
        assert lesson.subject.school_id == riverside.id
        assert lesson.student_group.school_id == riverside.id

    assert not riverside_lessons.filter(teacher__school=lincoln).exists()
