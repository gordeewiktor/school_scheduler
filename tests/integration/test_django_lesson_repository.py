from datetime import time

import pytest

from app.application.services.conflicts import ConflictService
from app.application.services.schedules import ScheduleService
from app.domain.exceptions import InvalidLessonPlacementError, ScheduleConflictError
from app.domain.models import Day, Lesson as DomainLesson
from app.infrastructure.database.models import AcademicYear, Period, Room, StudentGroup, Subject, Teacher
from app.infrastructure.repositories.django_lessons import DjangoLessonRepository


@pytest.fixture
def school_data(db):
    year = AcademicYear.objects.create(name="2026")
    periods = [
        Period.objects.create(academic_year=year, name="Period 1", order=1, start_time=time(8), end_time=time(9)),
        Period.objects.create(academic_year=year, name="Period 2", order=2, start_time=time(9), end_time=time(10)),
        Period.objects.create(academic_year=year, name="Break", order=3, start_time=time(10), end_time=time(10, 30), kind=Period.Kind.BREAK),
        Period.objects.create(academic_year=year, name="Period 3", order=4, start_time=time(10, 30), end_time=time(11, 30)),
    ]
    return {
        "year": year,
        "periods": periods,
        "teacher": Teacher.objects.create(name="Ada Lovelace"),
        "other_teacher": Teacher.objects.create(name="Grace Hopper"),
        "room": Room.objects.create(name="A101"),
        "other_room": Room.objects.create(name="B202"),
        "subject": Subject.objects.create(name="Math"),
        "group": StudentGroup.objects.create(name="Grade 1"),
        "other_group": StudentGroup.objects.create(name="Grade 2"),
    }


def service():
    repository = DjangoLessonRepository()
    return ScheduleService(repository, ConflictService(repository))


def command(data, **overrides):
    values = dict(
        teacher_id=data["teacher"].pk,
        subject_id=data["subject"].pk,
        room_id=data["room"].pk,
        student_group_id=data["group"].pk,
        day=Day.MONDAY,
        start_period_id=data["periods"][0].pk,
    )
    values.update(overrides)
    return DomainLesson(**values)


@pytest.mark.django_db
@pytest.mark.parametrize("resource", ["teacher", "room", "student_group"])
def test_service_rejects_each_resource_conflict(school_data, resource):
    service().create_lesson(command(school_data))
    overrides = {
        "teacher_id": school_data["other_teacher"].pk,
        "room_id": school_data["other_room"].pk,
        "student_group_id": school_data["other_group"].pk,
    }
    overrides[f"{resource}_id"] = {
        "teacher": school_data["teacher"].pk,
        "room": school_data["room"].pk,
        "student_group": school_data["group"].pk,
    }[resource]
    with pytest.raises(ScheduleConflictError):
        service().create_lesson(command(school_data, **overrides))


@pytest.mark.django_db
def test_service_allows_adjacent_periods(school_data):
    service().create_lesson(command(school_data))
    saved = service().create_lesson(
        command(
            school_data,
            start_period_id=school_data["periods"][1].pk,
        )
    )
    assert saved.id is not None


@pytest.mark.django_db
def test_service_rejects_break_period(school_data):
    with pytest.raises(InvalidLessonPlacementError):
        service().create_lesson(command(school_data, start_period_id=school_data["periods"][2].pk))


@pytest.mark.django_db
def test_service_update_excludes_current_lesson(school_data):
    saved = service().create_lesson(command(school_data))
    updated = service().update_lesson(command(school_data, id=saved.id, notes="Updated"))
    assert updated.notes == "Updated"


@pytest.mark.django_db
def test_same_reusable_period_can_be_used_on_different_days(school_data):
    service().create_lesson(command(school_data, day=Day.MONDAY))
    saved = service().create_lesson(command(school_data, day=Day.TUESDAY))
    assert saved.id is not None


@pytest.mark.django_db
def test_update_rejects_conflict_with_another_lesson(school_data):
    first = service().create_lesson(command(school_data))
    second = service().create_lesson(
        command(
            school_data,
            start_period_id=school_data["periods"][1].pk,
            room_id=school_data["other_room"].pk,
            student_group_id=school_data["other_group"].pk,
        )
    )
    with pytest.raises(ScheduleConflictError):
        service().update_lesson(
            command(
                school_data,
                id=second.id,
                start_period_id=school_data["periods"][0].pk,
                room_id=school_data["other_room"].pk,
                student_group_id=school_data["other_group"].pk,
            )
        )
    assert first.id != second.id


@pytest.mark.django_db
def test_repository_lists_teachers_as_domain_models(school_data):
    teachers = DjangoLessonRepository().list_teachers()

    assert [teacher.name for teacher in teachers] == ["Ada Lovelace", "Grace Hopper"]
    assert all(teacher.__class__.__module__ == "app.domain.models" for teacher in teachers)


@pytest.mark.django_db
def test_repository_lists_lessons_starting_at_selected_period_only(school_data):
    repository = DjangoLessonRepository()
    service().create_lesson(command(school_data))
    service().create_lesson(
        command(
            school_data,
            teacher_id=school_data["other_teacher"].pk,
            room_id=school_data["other_room"].pk,
            student_group_id=school_data["other_group"].pk,
            start_period_id=school_data["periods"][1].pk,
        )
    )

    lessons = repository.list_lessons_starting_at(
        school_data["year"].pk,
        Day.MONDAY,
        school_data["periods"][0].pk,
    )

    assert [lesson.teacher_id for lesson in lessons] == [school_data["teacher"].pk]


@pytest.mark.django_db
def test_repository_projects_planned_substitute_name(school_data):
    repository = DjangoLessonRepository()
    saved = service().create_lesson(
        command(
            school_data,
            planned_substitute_id=school_data["other_teacher"].pk,
        )
    )

    lessons = repository.list_lessons(school_data["year"].pk)

    assert [(lesson.id, lesson.planned_substitute_name) for lesson in lessons] == [
        (saved.id, "Grace Hopper")
    ]
