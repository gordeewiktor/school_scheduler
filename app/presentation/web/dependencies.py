from app.application.services.conflicts import ConflictService
from app.application.services.schedules import ScheduleService
from app.infrastructure.repositories.django_lessons import DjangoLessonRepository


def build_schedule_service() -> ScheduleService:
    repository = DjangoLessonRepository()
    conflict_service = ConflictService(repository)
    return ScheduleService(repository, conflict_service)