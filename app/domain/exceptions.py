from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.policies import LessonConflict


class DomainError(Exception):
    """Base class for business-rule errors."""


class InvalidPeriodError(DomainError):
    """Raised when a period has invalid bounds or ordering."""


class InvalidLessonPlacementError(DomainError):
    """Raised when a lesson cannot occupy its requested periods."""


class CrossSchoolLessonError(DomainError):
    """Raised when a lesson's resources do not all belong to one school."""


class ScheduleConflictError(DomainError):
    """Raised when a lesson would conflict with an existing lesson."""

    def __init__(self, conflicts: list[LessonConflict]) -> None:
        self.conflicts = conflicts
        super().__init__("; ".join(conflict.message for conflict in conflicts))
