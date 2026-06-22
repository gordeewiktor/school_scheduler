import pytest
from app.domain.models import Timeslot

def test_timeslot_has_day():
    slot = Timeslot('Monday', 6, 7)

    assert slot.day == 'Monday'

def test_timeslot_has_start_time():
    slot = Timeslot('Monday', 6, 7)

    assert slot.start_time == 6

def test_timeslot_has_end_time():
    slot = Timeslot('Monday', 6, 7)

    assert slot.end_time == 7

def test_timeslots_overlap_from_right():
    slot1 = Timeslot('Tuesday', 2, 4)
    slot2 = Timeslot('Tuesday', 3, 5)

    assert slot1.overlaps(slot2)

def test_timeslots_overlap_from_left():
    slot1 = Timeslot('Tuesday', 2, 4)
    slot2 = Timeslot('Tuesday', 1, 3)

    assert slot1.overlaps(slot2)


def test_timeslot_can_be_inside_another():
    slot1 = Timeslot('Tuesday', 1, 4)
    slot2 = Timeslot('Tuesday', 2, 3)

    assert slot1.overlaps(slot2)


def test_timeslots_do_not_overlap():
    slot1 = Timeslot('Tuesday', 1, 2)
    slot2 = Timeslot('Tuesday', 3, 4)

    assert not slot1.overlaps(slot2)

def test_timeslots_on_different_days_do_not_overlap():
    slot1 = Timeslot('Monday', 2, 4)
    slot2 = Timeslot('Tuesday', 2, 4)

    assert not slot1.overlaps(slot2)

def test_adjacent_timeslots_do_not_overlap():
    slot1 = Timeslot('Tuesday', 2, 4)
    slot2 = Timeslot('Tuesday', 4, 6)

    assert not slot1.overlaps(slot2)