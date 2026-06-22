import pytest
from app.domain.models import Teacher

def test_teacher_has_name():
    teacher = Teacher('Viktor')

    assert teacher.name == 'Viktor'

def test_teacher_starts_with_empty_availability():
    teacher = Teacher('Viktor')

    assert teacher.availability == []

def test_teacher_accept_availability():
    teacher = Teacher('Viktor', [6, 7])

    assert teacher.availability == [6, 7]

def test_teacher_add_availability():
    teacher = Teacher('Viktor')

    teacher.add_availability(1)
    teacher.add_availability(2)

    assert teacher.availability == [1, 2]

def test_teacher_can_not_add_same_time_slot_twice():
    teacher = Teacher('Vikor', [1])

    with pytest.raises(ValueError):
        teacher.add_availability(1)
    
    assert teacher.availability == [1]

