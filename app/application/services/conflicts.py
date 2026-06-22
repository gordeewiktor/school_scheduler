from app.application.ports.repositories import LessonRepository
from app.domain.policies import LessonConflict, LessonConflictPolicy, LessonRequest


class ConflictService:
    def __init__(
        self,
        lesson_repository: LessonRepository,
        policy: LessonConflictPolicy | None = None,
    ) -> None:
        self.lesson_repository = lesson_repository
        self.policy = policy or LessonConflictPolicy()

    def find_conflicts(self, request: LessonRequest) -> list[LessonConflict]:
        lessons = self.lesson_repository.list_potential_conflicts(request)
        return self.policy.find_conflicts(request, lessons)

    def has_conflicts(self, request: LessonRequest) -> bool:
        return bool(self.find_conflicts(request))
