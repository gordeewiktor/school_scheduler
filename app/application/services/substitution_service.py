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
        occupied_teacher_ids.update(
            lesson.planned_substitute_id
            for lesson in lessons
            if lesson.planned_substitute_id is not None
        )
        return [
            teacher
            for teacher in teachers
            if teacher.id not in occupied_teacher_ids
            and teacher.id != excluded_teacher_id
        ]
    
    def _select_substitute(
        self,
        teaching_free_teachers: list[Teacher],
        substitutes_at_period: set[int],
        substitution_counts: dict[int, int],
    ) -> Teacher | None:
        preferred_teachers = [
            teacher
            for teacher in teaching_free_teachers
            if teacher.id not in substitutes_at_period
        ]
        candidates = preferred_teachers or teaching_free_teachers
        if not candidates:
            return None

        return min(
            candidates,
            key=lambda teacher: (
                substitution_counts.get(teacher.id, 0),
                teacher.id,
            ),
        )

    def _teaching_free_teachers(
        self,
        lesson: ScheduledLesson,
        teachers: list[Teacher],
        teaching_by_period: dict[tuple[Day, int], set[int]],
    ) -> list[Teacher]:
        period_key = (lesson.day, lesson.start_period.id)
        teaching_teacher_ids = teaching_by_period.get(period_key, set())
        return [
            teacher
            for teacher in teachers
            if teacher.id != lesson.teacher_id
            and teacher.id not in teaching_teacher_ids
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
            teaching_free_teachers = self._teaching_free_teachers(
                lesson,
                teachers,
                teaching_by_period,
            )
            substitute = self._select_substitute(
                teaching_free_teachers,
                substitutes_by_period.get(period_key, set()),
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
        teachers = self.lesson_repository.list_teachers()
        teaching_by_period: dict[tuple[Day, int], set[int]] = {}
        for scheduled_lesson in self.lesson_repository.list_lessons(academic_year_id):
            period_key = (scheduled_lesson.day, scheduled_lesson.start_period.id)
            teaching_by_period.setdefault(period_key, set()).add(
                scheduled_lesson.teacher_id
            )
        plan: list[SubstitutionAssignment] = []
        substitution_counts: dict[int, int] = {}
        substitutes_by_period: dict[tuple[Day, int], set[int]] = {}

        for lesson in lessons:
            period_key = (lesson.day, lesson.start_period.id)
            teaching_free_teachers = self._teaching_free_teachers(
                lesson,
                teachers,
                teaching_by_period,
            )

            substitute = self._select_substitute(
                teaching_free_teachers,
                substitutes_by_period.get(period_key, set()),
                substitution_counts,
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
