from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class NavigationItem:
    label: str
    url_name: str


class NavigationBuilder:
    ADMINISTRATOR_ITEMS = (
        NavigationItem("Schedule", "schedule"),
        NavigationItem("Lessons", "lesson-list"),
        NavigationItem("Admin", "admin:index"),
    )
    REGULAR_USER_ITEMS = (
        NavigationItem("Schedule", "schedule"),
        NavigationItem("Teacher Substitution", "teacher-substitution"),
    )

    @classmethod
    def for_user(cls, user: Any) -> tuple[NavigationItem, ...]:
        if not user.is_authenticated:
            return ()
        if user.is_staff:
            return cls.ADMINISTRATOR_ITEMS
        return cls.REGULAR_USER_ITEMS


def navigation(request: Any) -> dict[str, tuple[NavigationItem, ...]]:
    return {"navigation_items": NavigationBuilder.for_user(request.user)}
