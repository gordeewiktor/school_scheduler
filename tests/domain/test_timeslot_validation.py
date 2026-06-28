from datetime import time

import pytest

from app.domain.exceptions import InvalidPeriodError
from app.domain.models import Period, PeriodKind


def period(**overrides):
    values = dict(
        id=1,
        academic_year_id=1,
        name="Period 1",
        order=1,
        start_time=time(9),
        end_time=time(10),
        kind=PeriodKind.LESSON,
    )
    values.update(overrides)
    return Period(**values)


def test_period_rejects_equal_start_and_end():
    with pytest.raises(InvalidPeriodError):
        period(end_time=time(9))


def test_period_rejects_start_after_end():
    with pytest.raises(InvalidPeriodError):
        period(start_time=time(11))


def test_period_rejects_non_positive_order():
    with pytest.raises(InvalidPeriodError):
        period(order=0)


def test_break_period_does_not_accept_lessons():
    assert not period(kind=PeriodKind.BREAK).accepts_lessons
