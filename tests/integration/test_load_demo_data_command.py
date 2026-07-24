from io import StringIO
from datetime import time

import pytest
from django.core.management import call_command

from app.domain.models import Day
from app.infrastructure.database.models import (
    AcademicYear,
    Lesson,
    Period,
    Room,
    StudentGroup,
    Subject,
    Teacher,
)


@pytest.mark.django_db
def test_load_demo_data_creates_complete_master_data():
    output = StringIO()

    call_command("load_demo_data", stdout=output)

    academic_year = AcademicYear.objects.get()
    assert academic_year.name == "Demo 2026"
    assert Teacher.objects.count() == 80
    assert StudentGroup.objects.count() == 50
    assert Room.objects.count() == 50
    assert Subject.objects.count() == 10
    assert Period.objects.filter(academic_year=academic_year).count() == 12
    assert Period.objects.filter(
        academic_year=academic_year,
        kind=Period.Kind.LESSON,
    ).count() == 10
    assert Period.objects.filter(
        academic_year=academic_year,
        kind=Period.Kind.BREAK,
    ).count() == 2
    assert list(
        Period.objects.filter(academic_year=academic_year).values_list(
            "name",
            flat=True,
        )
    ) == [
        "Homeroom",
        "Period 1",
        "Period 2",
        "Morning Break",
        "Period 3",
        "Period 4",
        "Lunch Break",
        "Period 5",
        "Period 6",
        "Period 7",
        "Period 8",
        "After School",
    ]
    assert list(
        Period.objects.filter(academic_year=academic_year).values_list(
            "start_time",
            "end_time",
        )
    ) == [
        (time(8, 0), time(8, 30)),
        (time(8, 30), time(9, 15)),
        (time(9, 15), time(10, 0)),
        (time(10, 0), time(10, 30)),
        (time(10, 30), time(11, 15)),
        (time(11, 15), time(12, 0)),
        (time(12, 0), time(12, 50)),
        (time(12, 50), time(13, 35)),
        (time(13, 35), time(14, 20)),
        (time(14, 20), time(15, 5)),
        (time(15, 5), time(15, 50)),
        (time(15, 50), time(16, 30)),
    ]

    assert "Demo school loaded successfully." in output.getvalue()
    assert "Academic years: 1" in output.getvalue()
    assert "Teachers: 80" in output.getvalue()
    assert "Student groups: 50" in output.getvalue()
    assert "Rooms: 50" in output.getvalue()
    assert "Subjects: 10" in output.getvalue()
    assert "Periods: 10" in output.getvalue()
    assert "Breaks: 2" in output.getvalue()
    assert "Lessons created: 2500" in output.getvalue()
    assert "Lessons: 2500" in output.getvalue()


@pytest.mark.django_db
def test_load_demo_data_is_idempotent_and_reuses_existing_academic_year():
    AcademicYear.objects.create(name="2026")

    call_command("load_demo_data", stdout=StringIO())
    call_command("load_demo_data", stdout=StringIO())

    academic_year = AcademicYear.objects.get()
    assert academic_year.name == "2026"
    assert Teacher.objects.count() == 80
    assert StudentGroup.objects.count() == 50
    assert Room.objects.count() == 50
    assert Subject.objects.count() == 10
    assert Period.objects.filter(academic_year=academic_year).count() == 12
    assert Lesson.objects.filter(start_period__academic_year=academic_year).count() == 2500


@pytest.mark.django_db
def test_load_demo_data_generates_conflict_free_complete_timetable():
    call_command("load_demo_data", stdout=StringIO())

    academic_year = AcademicYear.objects.get()
    teaching_period_count = Period.objects.filter(
        academic_year=academic_year,
        kind=Period.Kind.LESSON,
    ).count()
    expected_lessons_per_group = teaching_period_count * 5

    for student_group in StudentGroup.objects.all():
        assert Lesson.objects.filter(student_group=student_group).count() == (
            expected_lessons_per_group
        )

    weekly_patterns = set()
    for student_group in StudentGroup.objects.all():
        daily_subject_sequences = []
        subject_periods: dict[str, set[int]] = {}
        for day in Day:
            daily_subject_sequence = tuple(
                Lesson.objects.filter(
                    student_group=student_group,
                    day=day,
                )
                .order_by("start_period__order")
                .values_list("subject__name", flat=True)
            )
            daily_subject_sequences.append(daily_subject_sequence)
            for lesson in Lesson.objects.filter(
                student_group=student_group,
                day=day,
            ).select_related("subject", "start_period"):
                subject_periods.setdefault(lesson.subject.name, set()).add(
                    lesson.start_period.order
                )

        assert len(set(daily_subject_sequences)) == 5
        assert all(len(periods) > 1 for periods in subject_periods.values())
        weekly_patterns.add(tuple(daily_subject_sequences))

    assert len(weekly_patterns) == StudentGroup.objects.count()

    for day, period_id in Lesson.objects.values_list("day", "start_period_id").distinct():
        slot_lessons = Lesson.objects.filter(day=day, start_period_id=period_id)
        assert slot_lessons.count() == 50
        assert slot_lessons.values("teacher_id").distinct().count() == slot_lessons.count()
        assert slot_lessons.values("room_id").distinct().count() == slot_lessons.count()
        assert slot_lessons.values("student_group_id").distinct().count() == (
            slot_lessons.count()
        )

    assert not Lesson.objects.filter(start_period__kind=Period.Kind.BREAK).exists()


@pytest.mark.django_db
def test_load_demo_data_rerun_does_not_duplicate_lessons():
    call_command("load_demo_data", stdout=StringIO())
    call_command("load_demo_data", stdout=StringIO())

    assert Lesson.objects.count() == 2500


@pytest.mark.django_db
def test_load_demo_data_uses_only_demo_master_data_for_generated_timetable():
    AcademicYear.objects.create(name="2027")
    Teacher.objects.create(name="Manual Teacher")
    StudentGroup.objects.create(name="Manual Class")
    Room.objects.create(name="Manual Room")
    Subject.objects.create(name="Manual Subject")

    call_command("load_demo_data", stdout=StringIO())

    academic_year = AcademicYear.objects.get(name="2027")
    generated_lessons = Lesson.objects.filter(start_period__academic_year=academic_year)
    assert generated_lessons.count() == 2500
    assert not generated_lessons.filter(teacher__name="Manual Teacher").exists()
    assert not generated_lessons.filter(student_group__name="Manual Class").exists()
    assert not generated_lessons.filter(room__name="Manual Room").exists()
    assert not generated_lessons.filter(subject__name="Manual Subject").exists()
