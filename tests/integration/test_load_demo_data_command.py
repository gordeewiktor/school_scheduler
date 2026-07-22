from io import StringIO
from datetime import time

import pytest
from django.core.management import call_command

from app.infrastructure.database.models import (
    AcademicYear,
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
