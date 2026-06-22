from dataclasses import dataclass

from app.domain.models import TimeSlot


@dataclass(frozen=True, slots=True)
class ExistingLesson:
    id: int
    teacher_id: int
    room_id: int
    student_group_id: int
    time_slot: TimeSlot


@dataclass(frozen=True, slots=True)
class LessonRequest:
    teacher_id: int
    room_id: int
    student_group_id: int
    time_slot: TimeSlot
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
        for lesson in existing_lessons:
            if request.lesson_id is not None and lesson.id == request.lesson_id:
                continue
            if not request.time_slot.overlaps(lesson.time_slot):
                continue
            if lesson.teacher_id == request.teacher_id:
                conflicts.append(
                    LessonConflict("teacher", "Teacher is already teaching then.", lesson.id)
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
