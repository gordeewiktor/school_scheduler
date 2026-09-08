from dataclasses import dataclass

from app.domain.models import Day


@dataclass(frozen=True, slots=True)
class ExistingLesson:
    id: int
    teacher_id: int
    room_id: int
    student_group_id: int
    day: Day
    academic_year_id: int
    period_id: int
    planned_substitute_id: int | None = None


@dataclass(frozen=True, slots=True)
class LessonRequest:
    teacher_id: int
    room_id: int
    student_group_id: int
    day: Day
    academic_year_id: int
    period_id: int
    planned_substitute_id: int | None = None
    lesson_id: int | None = None


@dataclass(frozen=True, slots=True)
class LessonConflict:
    field: str
    message: str
    lesson_id: int


class LessonConflictPolicy:
    def find_conflicts(
        self,
        request: LessonRequest,
        existing_lessons: list[ExistingLesson],
    ) -> list[LessonConflict]:
        conflicts: list[LessonConflict] = []
        if request.planned_substitute_id is not None:
            if request.planned_substitute_id == request.teacher_id:
                conflicts.append(
                    LessonConflict(
                        "planned_substitute",
                        "Teacher cannot substitute for themselves.",
                        request.lesson_id or 0,
                    )
                )
        for lesson in existing_lessons:
            if request.lesson_id is not None and lesson.id == request.lesson_id:
                continue
            if request.day != lesson.day or request.academic_year_id != lesson.academic_year_id:
                continue
            if request.period_id != lesson.period_id:
                continue
            occupied_teacher_ids = {lesson.teacher_id}
            if lesson.planned_substitute_id is not None:
                occupied_teacher_ids.add(lesson.planned_substitute_id)
            if lesson.teacher_id == request.teacher_id:
                conflicts.append(
                    LessonConflict("teacher", "Teacher is already teaching then.", lesson.id)
                )
            if lesson.planned_substitute_id == request.teacher_id:
                conflicts.append(
                    LessonConflict(
                        "teacher",
                        "Teacher is already substituting then.",
                        lesson.id,
                    )
                )
            if (
                request.planned_substitute_id is not None
                and request.planned_substitute_id in occupied_teacher_ids
            ):
                conflicts.append(
                    LessonConflict(
                        "planned_substitute",
                        "Substitute teacher is already occupied then.",
                        lesson.id,
                    )
                )
            if lesson.room_id == request.room_id:
                conflicts.append(
                    LessonConflict("room", "Room is already in use then.", lesson.id)
                )
            if lesson.student_group_id == request.student_group_id:
                conflicts.append(
                    LessonConflict(
                        "student_group",
                        "Student group already has a lesson then.",
                        lesson.id,
                    )
                )
        return conflicts
