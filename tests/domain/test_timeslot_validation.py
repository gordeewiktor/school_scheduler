import pytest

from app.domain.exceptions import InvalidTimeSlotError
from app.domain.models import TimeSlot


def test_timeslot_rejects_equal_start_and_end():
    with pytest.raises(InvalidTimeSlotError):
        TimeSlot("Monday", 9, 9)


def test_timeslot_rejects_start_after_end():
    with pytest.raises(InvalidTimeSlotError):
        TimeSlot("Monday", 11, 9)
