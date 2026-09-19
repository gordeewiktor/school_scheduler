from app.application.services.conflicts import ConflictService
from app.application.services.period_generation import PeriodGenerationService
from app.application.services.schedules import ScheduleService
from app.infrastructure.repositories.django_lessons import DjangoLessonRepository
from app.application.services.substitution_service import SubstitutionService


def build_schedule_service() -> ScheduleService:
    repository = DjangoLessonRepository()
    conflict_service = ConflictService(repository)
    return ScheduleService(repository, conflict_service)

def build_substitution_service() -> SubstitutionService:
    repository = DjangoLessonRepository()
    return SubstitutionService(repository)

def build_period_generation_service() -> PeriodGenerationService:
    repository = DjangoLessonRepository()
    return PeriodGenerationService(repository)