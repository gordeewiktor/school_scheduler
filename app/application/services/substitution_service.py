from dataclasses import dataclass
from app.domain.models import Day, Teacher
from app.application.ports.repositories import (
    LessonRepository,
    ScheduledLesson,
)

@dataclass(frozen=True, slots=True)
class SubstitutionAssignment:
    lesson: ScheduledLesson
    substitute: Teacher | None


class SubstitutionService:
    def __init__(self, lesson_repository: LessonRepository) -> None:
        self.lesson_repository = lesson_repository
    
    def available_teachers(
        self,
        academic_year_id: int,
        day: Day,
        period_id: int,
        excluded_teacher_id: int | None = None,
    ) -> list[Teacher]:
        teachers = self.lesson_repository.list_teachers()
        lessons = self.lesson_repository.list_lessons_starting_at(
            academic_year_id, day, period_id
        )
        occupied_teacher_ids = {lesson.teacher_id for lesson in lessons}
        return [
            teacher
            for teacher in teachers
            if teacher.id not in occupied_teacher_ids
            and teacher.id != excluded_teacher_id
        ]
    
    def _select_substitute(
        self,
        teachers: list[Teacher],
        substitution_counts: dict[int, int],
    ) -> Teacher | None:
        if not teachers:
            return None

        return min(
            teachers,
            key=lambda teacher: (
                substitution_counts.get(teacher.id, 0),
                teacher.id,
            ),
        )
    
    def generate_plan(
        self,
        teacher_id: int,
        academic_year_id: int,
    ) -> list[SubstitutionAssignment]:
        lessons = self.lesson_repository.list_lessons_for_teacher(
            teacher_id,
            academic_year_id,
        )
        plan: list[SubstitutionAssignment] = []
        substitution_counts: dict[int, int] = {}

        for lesson in lessons:
            available = self.available_teachers(
                academic_year_id,
                lesson.day,
                lesson.start_period.id,
                excluded_teacher_id=teacher_id,
            )

            substitute = self._select_substitute(
                available,
                substitution_counts,
            )

            plan.append(
                SubstitutionAssignment(
                    lesson=lesson,
                    substitute=substitute,
                )
            )

            if substitute is not None:
                substitution_counts[substitute.id] = (
                    substitution_counts.get(substitute.id, 0) + 1
                )

        return plan
