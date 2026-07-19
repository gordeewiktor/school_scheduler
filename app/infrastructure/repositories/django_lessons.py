from django.db.models import Q

from app.application.ports.repositories import ScheduledLesson
from app.domain.models import (
    Day,
    Lesson as DomainLesson,
    Period as DomainPeriod,
    Teacher as DomainTeacher,
)
from app.domain.policies import ExistingLesson, LessonRequest
from app.infrastructure.database.models import Lesson, Period, Teacher


class DjangoLessonRepository:
    def list_teachers(self) -> list[DomainTeacher]:
        return [
            DomainTeacher(id=teacher.id, name=teacher.name, email=teacher.email)
            for teacher in Teacher.objects.order_by("name")
        ]

    def get_period(self, period_id: int) -> DomainPeriod | None:
        try:
            return Period.objects.get(pk=period_id).to_domain()
        except Period.DoesNotExist:
            return None

    def list_periods(self, academic_year_id: int) -> list[DomainPeriod]:
        return [
            period.to_domain()
            for period in Period.objects.filter(academic_year_id=academic_year_id).order_by("order")
        ]

    def list_potential_conflicts(self, request: LessonRequest) -> list[ExistingLesson]:
        queryset = (
            Lesson.objects.select_related("start_period")
            .filter(day=request.day.value, start_period__academic_year_id=request.academic_year_id)
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
                day=Day(lesson.day),
                academic_year_id=lesson.start_period.academic_year_id,
                period_id=lesson.start_period_id,
            )
            for lesson in queryset
        ]

    def create_lesson(self, lesson: DomainLesson) -> DomainLesson:
        instance = Lesson.objects.create(**self._fields(lesson))
        return instance.to_domain()

    def update_lesson(self, lesson: DomainLesson) -> DomainLesson:
        if lesson.id is None:
            raise ValueError("Lesson id is required for updates.")
        instance = Lesson.objects.get(pk=lesson.id)
        for field, value in self._fields(lesson).items():
            setattr(instance, field, value)
        instance.save()
        return instance.to_domain()

    def list_lessons(self, academic_year_id: int) -> list[ScheduledLesson]:
        return self._project(
            self._base_queryset().filter(start_period__academic_year_id=academic_year_id)
        )

    def list_lessons_starting_at(
        self, academic_year_id: int, day: Day, period_id: int
    ) -> list[ScheduledLesson]:
        return self._project(
            self._base_queryset().filter(
                day=day.value,
                start_period_id=period_id,
                start_period__academic_year_id=academic_year_id,
            )
        )

    def list_lessons_for_teacher(
        self, teacher_id: int, academic_year_id: int
    ) -> list[ScheduledLesson]:
        return self._project(
            self._base_queryset().filter(
                teacher_id=teacher_id, start_period__academic_year_id=academic_year_id
            )
        )

    def list_lessons_for_room(
        self, room_id: int, academic_year_id: int
    ) -> list[ScheduledLesson]:
        return self._project(
            self._base_queryset().filter(
                room_id=room_id, start_period__academic_year_id=academic_year_id
            )
        )

    def list_lessons_for_student_group(
        self, student_group_id: int, academic_year_id: int
    ) -> list[ScheduledLesson]:
        return self._project(
            self._base_queryset().filter(
                student_group_id=student_group_id,
                start_period__academic_year_id=academic_year_id,
            )
        )
    
    def list_lessons_for_substitute(
        self, teacher_id: int, academic_year_id: int
    ) -> list[ScheduledLesson]:
        return self._project(
            self._base_queryset().filter(
                planned_substitute_id=teacher_id,
                start_period__academic_year_id=academic_year_id,
            )
        )

    @staticmethod
    def _fields(lesson: DomainLesson) -> dict[str, object]:
        return {
            "teacher_id": lesson.teacher_id,
            "subject_id": lesson.subject_id,
            "room_id": lesson.room_id,
            "student_group_id": lesson.student_group_id,
            "day": lesson.day.value,
            "start_period_id": lesson.start_period_id,
            "planned_substitute_id": lesson.planned_substitute_id,
            "notes": lesson.notes,
        }

    @staticmethod
    def _base_queryset():
        return Lesson.objects.select_related(
            "teacher", "subject", "room", "student_group", "start_period"
        )

    @staticmethod
    def _project(queryset) -> list[ScheduledLesson]:
        return [
            ScheduledLesson(
                id=lesson.id,
                teacher_id=lesson.teacher_id,
                teacher_name=lesson.teacher.name,
                subject_name=lesson.subject.name,
                room_id=lesson.room_id,
                room_name=lesson.room.name,
                student_group_id=lesson.student_group_id,
                student_group_name=lesson.student_group.name,
                day=Day(lesson.day),
                start_period=lesson.start_period.to_domain(),
                notes=lesson.notes,
            )
            for lesson in queryset
        ]
