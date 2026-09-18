from __future__ import annotations

from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from app.infrastructure.database.models import School, SchoolMembership

CURRENT_SCHOOL_SESSION_KEY = "current_school_id"


class CurrentSchoolService:
    """Resolves and validates which School an authenticated user is
    currently acting within.

    The session only ever stores a workspace *selection*. It is never
    treated as proof of access on its own: every resolution re-checks
    the database for a live, PRINCIPAL SchoolMembership, so a
    membership revoked mid-session stops granting access on the very
    next request, and a session value that was never valid (tampered,
    stale, or belonging to a school the user was removed from) is
    silently discarded rather than trusted.
    """

    @staticmethod
    def memberships_for(user) -> list[SchoolMembership]:
        return list(
            SchoolMembership.objects.filter(
                user=user, role=SchoolMembership.Role.PRINCIPAL
            ).select_related("school")
        )

    @classmethod
    def resolve(cls, request: HttpRequest) -> School | None:
        """Return the user's current School, or None if it cannot be
        determined without asking them (not authenticated, no
        membership at all, or several memberships with nothing validly
        selected yet)."""
        if not request.user.is_authenticated:
            return None

        memberships = cls.memberships_for(request.user)

        selected_id = request.session.get(CURRENT_SCHOOL_SESSION_KEY)
        if selected_id is not None:
            membership = next(
                (m for m in memberships if m.school_id == selected_id), None
            )
            if membership is not None:
                return membership.school
            # The session points at a school the user is no longer (or
            # never was) a member of. Never trust it — drop it.
            request.session.pop(CURRENT_SCHOOL_SESSION_KEY, None)

        if len(memberships) == 1:
            school = memberships[0].school
            request.session[CURRENT_SCHOOL_SESSION_KEY] = school.id
            return school

        return None

    @classmethod
    def set_current(cls, request: HttpRequest, school_id: Any) -> School | None:
        """Validate that the user actually belongs to `school_id` and,
        only then, store it as their current school. Returns None (and
        changes nothing) for an invalid, foreign, or nonexistent id —
        the caller decides what to do about that."""
        try:
            school_id = int(school_id)
        except (TypeError, ValueError):
            return None

        membership = (
            SchoolMembership.objects.filter(
                user=request.user,
                school_id=school_id,
                role=SchoolMembership.Role.PRINCIPAL,
            )
            .select_related("school")
            .first()
        )
        if membership is None:
            return None

        request.session[CURRENT_SCHOOL_SESSION_KEY] = membership.school_id
        return membership.school


class SchoolAccessRequiredMixin(LoginRequiredMixin):
    """Requires an authenticated user with a resolvable current School
    (see CurrentSchoolService) and exposes it as `self.current_school`.

    This is deliberately independent of Django's `is_staff`/
    `is_superuser` — being Django staff says nothing about which
    School, if any, a user may act within. Django Admin authorization
    is a separate system and is untouched by this mixin.
    """

    current_school: School | None = None

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        school = CurrentSchoolService.resolve(request)
        if school is None:
            if len(CurrentSchoolService.memberships_for(request.user)) > 1:
                return redirect("choose-school")
            return render(request, "scheduler/no_school_access.html", status=403)

        self.current_school = school
        return super().dispatch(request, *args, **kwargs)
