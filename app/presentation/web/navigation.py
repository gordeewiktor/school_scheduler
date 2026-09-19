from dataclasses import dataclass
from typing import Any

from app.presentation.web.school_access import CurrentSchoolService


@dataclass(frozen=True, slots=True)
class NavigationItem:
    label: str
    url_name: str


class NavigationBuilder:
    # Shown once the request has a resolvable current school — i.e. an
    # authenticated PRINCIPAL SchoolMembership — regardless of is_staff.
    SCHOOL_MANAGEMENT_ITEMS = (
        NavigationItem("Timetable", "schedule"),
        NavigationItem("Staff Schedule", "staff-schedule"),
        NavigationItem("Lessons", "lesson-list"),
        NavigationItem("Teacher Substitution", "teacher-substitution"),
    )
    PUBLIC_ITEMS = (
        NavigationItem("Timetable", "schedule"),
    )
    # Django Admin is a genuinely separate authorization system — this
    # is the one item that stays is_staff-gated, appended independently
    # of school-management access.
    ADMIN_ITEM = NavigationItem("Admin", "admin:index")

    @classmethod
    def for_request(cls, request: Any) -> tuple[NavigationItem, ...]:
        user = request.user
        if not user.is_authenticated:
            return cls.PUBLIC_ITEMS

        current_school = CurrentSchoolService.resolve(request)
        items = cls.SCHOOL_MANAGEMENT_ITEMS if current_school is not None else cls.PUBLIC_ITEMS
        if user.is_staff:
            items = items + (cls.ADMIN_ITEM,)
        return items


def navigation(request: Any) -> dict[str, tuple[NavigationItem, ...]]:
    return {"navigation_items": NavigationBuilder.for_request(request)}
