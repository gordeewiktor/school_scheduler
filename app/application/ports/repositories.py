from __future__ import annotations

from typing import Protocol

from app.domain.models import Lesson
from app.domain.policies import ExistingLesson, LessonRequest


class LessonRepository(Protocol):
    def list_potential_conflicts(self, request: LessonRequest) -> list[ExistingLesson]:
        ...

    def create_lesson(self, lesson: Lesson) -> Lesson:
        ...

    def update_lesson(self, lesson: Lesson) -> Lesson:
        ...

    def list_lessons(self) -> list[object]:
        ...

    def list_lessons_for_teacher(self, teacher_id: int) -> list[object]:
        ...

    def list_lessons_for_room(self, room_id: int) -> list[object]:
        ...

    def list_lessons_for_student_group(self, student_group_id: int) -> list[object]:
        ...
