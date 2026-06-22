from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time

from app.domain.exceptions import InvalidTimeSlotError


@dataclass(slots=True)
class Teacher:
    name: str
    availability: list[object] = field(default_factory=list)

    def add_availability(self, slot: object) -> None:
        if slot in self.availability:
            raise ValueError("Time slot already exists")
        self.availability.append(slot)


@dataclass(frozen=True, slots=True)
class Room:
    name: str
    capacity: int | None = None


@dataclass(frozen=True, slots=True)
class Subject:
    name: str


@dataclass(frozen=True, slots=True)
class StudentGroup:
    name: str
    size: int | None = None


@dataclass(frozen=True, slots=True)
class TimeSlot:
    day: str
    start_time: time | int
    end_time: time | int

    def __post_init__(self) -> None:
        if self.start_time >= self.end_time:
            raise InvalidTimeSlotError("Start time must be before end time.")

    def overlaps(self, other: "TimeSlot") -> bool:
        if self.day != other.day:
            return False
        return self.start_time < other.end_time and self.end_time > other.start_time


Timeslot = TimeSlot


@dataclass(frozen=True, slots=True)
class Lesson:
    teacher_id: int
    subject_id: int
    room_id: int
    student_group_id: int
    time_slot_id: int
    id: int | None = None
