from collections.abc import Iterable

from app.application.ports.repositories import LessonRepository
from app.application.services.conflicts import ConflictService
from app.domain.exceptions import ScheduleConflictError
from app.domain.models import Lesson
from app.domain.policies import LessonRequest


class ScheduleService:
    DAY_ORDER = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    def __init__(
        self,
        lesson_repository: LessonRepository,
        conflict_service: ConflictService,
    ) -> None:
        self.lesson_repository = lesson_repository
        self.conflict_service = conflict_service

    def create_lesson(self, lesson: Lesson, request: LessonRequest) -> Lesson:
        conflicts = self.conflict_service.find_conflicts(request)
        if conflicts:
            messages = "; ".join(conflict.message for conflict in conflicts)
            raise ScheduleConflictError(messages)
        return self.lesson_repository.create_lesson(lesson)

    def update_lesson(self, lesson: Lesson, request: LessonRequest) -> Lesson:
        conflicts = self.conflict_service.find_conflicts(request)
        if conflicts:
            messages = "; ".join(conflict.message for conflict in conflicts)
            raise ScheduleConflictError(messages)
        return self.lesson_repository.update_lesson(lesson)

    def weekly_schedule(self, lessons: Iterable[object]) -> dict[str, list[object]]:
        grouped: dict[str, list[object]] = {}
        for lesson in lessons:
            grouped.setdefault(lesson.time_slot.day, []).append(lesson)

        return {
            day: sorted(day_lessons, key=lambda lesson: lesson.time_slot.start_time)
            for day, day_lessons in sorted(
                grouped.items(),
                key=lambda item: self.DAY_ORDER.index(item[0]),
            )
        }

    def schedule_for_teacher(self, teacher_id: int) -> dict[str, list[object]]:
        return self.weekly_schedule(self.lesson_repository.list_lessons_for_teacher(teacher_id))

    def schedule_for_room(self, room_id: int) -> dict[str, list[object]]:
        return self.weekly_schedule(self.lesson_repository.list_lessons_for_room(room_id))

    def schedule_for_student_group(self, student_group_id: int) -> dict[str, list[object]]:
        return self.weekly_schedule(
            self.lesson_repository.list_lessons_for_student_group(student_group_id)
        )
