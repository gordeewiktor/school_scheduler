from __future__ import annotations

from dataclasses import dataclass

from app.application.services.schedules import ScheduleService
from app.domain.models import Day, Lesson
from app.infrastructure.database.models import Room, StudentGroup, Subject, Teacher


@dataclass(frozen=True, slots=True)
class DemoTimetableResult:
    lessons_created: int


class DemoTimetableGenerator:
    DAY_CLASS_STEPS = (1, 3, 7, 9, 1)
    DAY_OFFSETS = (0, 2, 5, 1, 7)
    CLUSTER_PERIOD_STEPS = (
        (1, 3, 7, 9, 1),
        (3, 7, 9, 1, 3),
        (7, 9, 1, 3, 7),
        (9, 1, 3, 7, 9),
        (1, 7, 3, 9, 1),
    )
    CLUSTER_OFFSETS = (
        (0, 1, 4, 7, 2),
        (2, 5, 8, 1, 4),
        (5, 9, 3, 6, 0),
        (7, 2, 6, 0, 8),
        (9, 5, 1, 5, 3),
    )

    def __init__(self, schedule_service: ScheduleService) -> None:
        self.schedule_service = schedule_service

    def generate(
        self,
        academic_year_id: int,
        student_groups: list[StudentGroup],
        rooms: list[Room],
        subjects: list[Subject],
        teachers: list[Teacher],
    ) -> DemoTimetableResult:
        periods = [
            period
            for period in self.schedule_service.periods(academic_year_id)
            if period.accepts_lessons
        ]
        if not periods or not student_groups or not rooms or not subjects or not teachers:
            return DemoTimetableResult(lessons_created=0)

        subject_teacher_ids = self._subject_teacher_ids(subjects, teachers)
        teacher_loads = {teacher.id: 0 for teacher in teachers}
        lessons_created = 0

        for day_index, day in enumerate(Day):
            for period_index, period in enumerate(periods):
                busy_teacher_ids: set[int] = set()
                for group_index, student_group in enumerate(student_groups):
                    subject = subjects[
                        self._subject_index(
                            day_index,
                            period_index,
                            group_index,
                            len(subjects),
                        )
                    ]
                    teacher_id = self._select_teacher(
                        subject_teacher_ids[subject.id],
                        teacher_loads,
                        busy_teacher_ids,
                    )
                    room = rooms[group_index % len(rooms)]
                    self.schedule_service.create_lesson(
                        Lesson(
                            teacher_id=teacher_id,
                            subject_id=subject.id,
                            room_id=room.id,
                            student_group_id=student_group.id,
                            day=day,
                            start_period_id=period.id,
                        )
                    )
                    busy_teacher_ids.add(teacher_id)
                    teacher_loads[teacher_id] += 1
                    lessons_created += 1

        return DemoTimetableResult(lessons_created=lessons_created)

    def _subject_index(
        self,
        day_index: int,
        period_index: int,
        group_index: int,
        subject_count: int,
    ) -> int:
        cluster = group_index // subject_count
        class_remainder = group_index % subject_count
        cluster_index = cluster % len(self.CLUSTER_PERIOD_STEPS[day_index])
        return (
            self.CLUSTER_PERIOD_STEPS[day_index][cluster_index] * period_index
            + self.CLUSTER_OFFSETS[day_index][cluster_index]
            + self.DAY_CLASS_STEPS[day_index] * class_remainder
            + self.DAY_OFFSETS[day_index]
            + cluster
        ) % subject_count

    @staticmethod
    def _subject_teacher_ids(
        subjects: list[Subject],
        teachers: list[Teacher],
    ) -> dict[int, list[int]]:
        subject_teacher_ids = {subject.id: [] for subject in subjects}
        for index, teacher in enumerate(teachers):
            subject = subjects[index % len(subjects)]
            subject_teacher_ids[subject.id].append(teacher.id)
        return subject_teacher_ids

    @staticmethod
    def _select_teacher(
        teacher_ids: list[int],
        teacher_loads: dict[int, int],
        busy_teacher_ids: set[int],
    ) -> int:
        available_teacher_ids = [
            teacher_id for teacher_id in teacher_ids if teacher_id not in busy_teacher_ids
        ]
        return min(
            available_teacher_ids,
            key=lambda teacher_id: (teacher_loads[teacher_id], teacher_id),
        )
