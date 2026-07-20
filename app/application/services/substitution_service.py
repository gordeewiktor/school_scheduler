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

    def _eligible_teachers(
        self,
        lesson: ScheduledLesson,
        teachers: list[Teacher],
        teaching_by_period: dict[tuple[Day, int], set[int]],
        substitutes_by_period: dict[tuple[Day, int], set[int]],
    ) -> list[Teacher]:
        period_key = (lesson.day, lesson.start_period.id)
        unavailable_teacher_ids = (
            teaching_by_period.get(period_key, set())
            | substitutes_by_period.get(period_key, set())
        )
        return [
            teacher
            for teacher in teachers
            if teacher.id != lesson.teacher_id
            and teacher.id not in unavailable_teacher_ids
        ]

    def generate_planned_substitutions(
        self,
        academic_year_id: int,
    ) -> list[SubstitutionAssignment]:
        lessons = sorted(
            self.lesson_repository.list_lessons(academic_year_id),
            key=lambda lesson: (
                list(Day).index(lesson.day),
                lesson.start_period.order,
                lesson.id,
            ),
        )
        teachers = self.lesson_repository.list_teachers()
        teaching_by_period: dict[tuple[Day, int], set[int]] = {}
        substitutes_by_period: dict[tuple[Day, int], set[int]] = {}
        substitution_counts: dict[int, int] = {}
        plan: list[SubstitutionAssignment] = []

        for lesson in lessons:
            period_key = (lesson.day, lesson.start_period.id)
            teaching_by_period.setdefault(period_key, set()).add(lesson.teacher_id)

        for lesson in lessons:
            period_key = (lesson.day, lesson.start_period.id)
            eligible = self._eligible_teachers(
                lesson,
                teachers,
                teaching_by_period,
                substitutes_by_period,
            )
            substitute = self._select_substitute(
                eligible,
                substitution_counts,
            )
            substitute_id = substitute.id if substitute is not None else None

            self.lesson_repository.set_planned_substitute(
                lesson.id,
                substitute_id,
            )
            plan.append(
                SubstitutionAssignment(
                    lesson=lesson,
                    substitute=substitute,
                )
            )

            if substitute is not None:
                substitutes_by_period.setdefault(period_key, set()).add(substitute.id)
                substitution_counts[substitute.id] = (
                    substitution_counts.get(substitute.id, 0) + 1
                )

        return plan
    
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
