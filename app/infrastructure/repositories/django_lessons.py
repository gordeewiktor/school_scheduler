from django.db.models import Q

from app.domain.models import Lesson as DomainLesson
from app.domain.policies import ExistingLesson, LessonRequest
from app.infrastructure.database.models import Lesson


class DjangoLessonRepository:
    def list_potential_conflicts(self, request: LessonRequest) -> list[ExistingLesson]:
        queryset = (
            Lesson.objects.select_related("time_slot")
            .filter(time_slot__day=request.time_slot.day)
            .filter(
                Q(teacher_id=request.teacher_id)
                | Q(room_id=request.room_id)
                | Q(student_group_id=request.student_group_id)
            )
        )
        if request.lesson_id is not None:
            queryset = queryset.exclude(pk=request.lesson_id)

        return [
            ExistingLesson(
                id=lesson.id,
                teacher_id=lesson.teacher_id,
                room_id=lesson.room_id,
                student_group_id=lesson.student_group_id,
                time_slot=lesson.time_slot.to_domain(),
            )
            for lesson in queryset
        ]

    def create_lesson(self, lesson: DomainLesson) -> DomainLesson:
        instance = Lesson.objects.create(
            teacher_id=lesson.teacher_id,
            subject_id=lesson.subject_id,
            room_id=lesson.room_id,
            student_group_id=lesson.student_group_id,
            time_slot_id=lesson.time_slot_id,
        )
        return instance.to_domain()

    def update_lesson(self, lesson: DomainLesson) -> DomainLesson:
        if lesson.id is None:
            raise ValueError("Lesson id is required for updates.")
        instance = Lesson.objects.get(pk=lesson.id)
        instance.teacher_id = lesson.teacher_id
        instance.subject_id = lesson.subject_id
        instance.room_id = lesson.room_id
        instance.student_group_id = lesson.student_group_id
        instance.time_slot_id = lesson.time_slot_id
        instance.save()
        return instance.to_domain()

    def list_lessons(self) -> list[Lesson]:
        return list(self._base_queryset())

    def list_lessons_for_teacher(self, teacher_id: int) -> list[Lesson]:
        return list(self._base_queryset().filter(teacher_id=teacher_id))

    def list_lessons_for_room(self, room_id: int) -> list[Lesson]:
        return list(self._base_queryset().filter(room_id=room_id))

    def list_lessons_for_student_group(self, student_group_id: int) -> list[Lesson]:
        return list(self._base_queryset().filter(student_group_id=student_group_id))

    def _base_queryset(self):
        return Lesson.objects.select_related(
            "teacher",
            "subject",
            "room",
            "student_group",
            "time_slot",
        )
