class DomainError(Exception):
    """Base class for business-rule errors."""


class InvalidTimeSlotError(DomainError):
    """Raised when a time slot has invalid bounds."""


class ScheduleConflictError(DomainError):
    """Raised when a lesson would conflict with an existing lesson."""
