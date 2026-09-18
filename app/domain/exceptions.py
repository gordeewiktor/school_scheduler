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


class SchoolAuthorizationError(DomainError):
    """Raised when a caller-supplied school does not own the data an
    operation was asked to act on.

    Distinct from CrossSchoolLessonError: that guard checks whether a
    lesson's own components agree with *each other*; this one checks
    whether the caller is even entitled to the school they agree on.
    """


class ScheduleConflictError(DomainError):
    """Raised when a lesson would conflict with an existing lesson."""

    def __init__(self, conflicts: list[LessonConflict]) -> None:
        self.conflicts = conflicts
        super().__init__("; ".join(conflict.message for conflict in conflicts))
