from datetime import time

import pytest

from app.application.services.period_generation import BreakAfter, PeriodGenerationService
from app.domain.exceptions import (
    InvalidPeriodError,
    PeriodsAlreadyExistError,
    SchoolAuthorizationError,
)
from app.domain.models import Period, PeriodKind


class FakeLessonRepository:
    def __init__(self, school_id=1, existing_periods=None):
        self.school_id = school_id
        self.existing_periods = existing_periods or []
        self.created_specs = None

    def get_academic_year_school_id(self, academic_year_id):
        return self.school_id

    def list_periods(self, academic_year_id):
        return self.existing_periods

    def create_periods(self, academic_year_id, specs):
        self.created_specs = specs
        return [
            Period(
                id=index + 1,
                academic_year_id=academic_year_id,
                name=spec.name,
                order=spec.order,
                start_time=spec.start_time,
                end_time=spec.end_time,
                kind=spec.kind,
            )
            for index, spec in enumerate(specs)
        ]


def as_tuples(periods):
    return [(p.order, p.name, p.start_time, p.end_time, p.kind) for p in periods]


@pytest.mark.django_db
def test_generate_produces_the_expected_sequence_for_the_documented_example():
    repository = FakeLessonRepository()
    service = PeriodGenerationService(repository)

    periods = service.generate(
        academic_year_id=1,
        school_id=1,
        lesson_count=6,
        first_start_time=time(8, 0),
        lesson_duration_minutes=50,
        breaks=[
            BreakAfter(after_period=2, duration_minutes=10),
            BreakAfter(after_period=4, duration_minutes=10),
        ],
    )

    assert as_tuples(periods) == [
        (1, "Period 1", time(8, 0), time(8, 50), PeriodKind.LESSON),
        (2, "Period 2", time(8, 50), time(9, 40), PeriodKind.LESSON),
        (3, "Break after Period 2", time(9, 40), time(9, 50), PeriodKind.BREAK),
        (4, "Period 3", time(9, 50), time(10, 40), PeriodKind.LESSON),
        (5, "Period 4", time(10, 40), time(11, 30), PeriodKind.LESSON),
        (6, "Break after Period 4", time(11, 30), time(11, 40), PeriodKind.BREAK),
        (7, "Period 5", time(11, 40), time(12, 30), PeriodKind.LESSON),
        (8, "Period 6", time(12, 30), time(13, 20), PeriodKind.LESSON),
    ]


@pytest.mark.django_db
def test_generate_without_breaks_produces_sequential_lesson_periods_only():
    repository = FakeLessonRepository()
    service = PeriodGenerationService(repository)

    periods = service.generate(
        academic_year_id=1,
        school_id=1,
        lesson_count=3,
        first_start_time=time(9, 0),
        lesson_duration_minutes=45,
        breaks=[],
    )

    assert as_tuples(periods) == [
        (1, "Period 1", time(9, 0), time(9, 45), PeriodKind.LESSON),
        (2, "Period 2", time(9, 45), time(10, 30), PeriodKind.LESSON),
        (3, "Period 3", time(10, 30), time(11, 15), PeriodKind.LESSON),
    ]


@pytest.mark.django_db
def test_generate_rejects_a_school_id_that_does_not_own_the_academic_year():
    repository = FakeLessonRepository(school_id=1)
    service = PeriodGenerationService(repository)

    with pytest.raises(SchoolAuthorizationError):
        service.generate(
            academic_year_id=1,
            school_id=2,
            lesson_count=1,
            first_start_time=time(8, 0),
            lesson_duration_minutes=45,
            breaks=[],
        )
    assert repository.created_specs is None


@pytest.mark.django_db
def test_generate_rejects_an_academic_year_that_already_has_periods():
    existing = [
        Period(
            id=1, academic_year_id=1, name="Old Period", order=1,
            start_time=time(8, 0), end_time=time(8, 45), kind=PeriodKind.LESSON,
        )
    ]
    repository = FakeLessonRepository(existing_periods=existing)
    service = PeriodGenerationService(repository)

    with pytest.raises(PeriodsAlreadyExistError):
        service.generate(
            academic_year_id=1,
            school_id=1,
            lesson_count=1,
            first_start_time=time(8, 0),
            lesson_duration_minutes=45,
            breaks=[],
        )
    assert repository.created_specs is None


@pytest.mark.django_db
@pytest.mark.parametrize("lesson_count", [0, -1])
def test_generate_rejects_a_non_positive_lesson_count(lesson_count):
    repository = FakeLessonRepository()
    service = PeriodGenerationService(repository)

    with pytest.raises(InvalidPeriodError):
        service.generate(
            academic_year_id=1,
            school_id=1,
            lesson_count=lesson_count,
            first_start_time=time(8, 0),
            lesson_duration_minutes=45,
            breaks=[],
        )


@pytest.mark.django_db
def test_generate_rejects_a_non_positive_lesson_duration():
    repository = FakeLessonRepository()
    service = PeriodGenerationService(repository)

    with pytest.raises(InvalidPeriodError):
        service.generate(
            academic_year_id=1,
            school_id=1,
            lesson_count=2,
            first_start_time=time(8, 0),
            lesson_duration_minutes=0,
            breaks=[],
        )


@pytest.mark.django_db
def test_generate_rejects_a_non_positive_break_duration():
    repository = FakeLessonRepository()
    service = PeriodGenerationService(repository)

    with pytest.raises(InvalidPeriodError):
        service.generate(
            academic_year_id=1,
            school_id=1,
            lesson_count=2,
            first_start_time=time(8, 0),
            lesson_duration_minutes=45,
            breaks=[BreakAfter(after_period=1, duration_minutes=0)],
        )


@pytest.mark.django_db
def test_generate_rejects_a_break_position_outside_the_lesson_range():
    repository = FakeLessonRepository()
    service = PeriodGenerationService(repository)

    with pytest.raises(InvalidPeriodError):
        service.generate(
            academic_year_id=1,
            school_id=1,
            lesson_count=3,
            first_start_time=time(8, 0),
            lesson_duration_minutes=45,
            breaks=[BreakAfter(after_period=10, duration_minutes=10)],
        )


@pytest.mark.django_db
def test_generate_rejects_two_breaks_at_the_same_position():
    repository = FakeLessonRepository()
    service = PeriodGenerationService(repository)

    with pytest.raises(InvalidPeriodError):
        service.generate(
            academic_year_id=1,
            school_id=1,
            lesson_count=3,
            first_start_time=time(8, 0),
            lesson_duration_minutes=45,
            breaks=[
                BreakAfter(after_period=2, duration_minutes=5),
                BreakAfter(after_period=2, duration_minutes=10),
            ],
        )


@pytest.mark.django_db
def test_generate_rejects_a_schedule_that_crosses_midnight():
    repository = FakeLessonRepository()
    service = PeriodGenerationService(repository)

    with pytest.raises(InvalidPeriodError):
        service.generate(
            academic_year_id=1,
            school_id=1,
            lesson_count=1,
            first_start_time=time(23, 30),
            lesson_duration_minutes=50,
            breaks=[],
        )
    assert repository.created_specs is None
