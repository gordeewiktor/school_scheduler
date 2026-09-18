from django.contrib import admin

from app.infrastructure.database.models import (
    AcademicYear,
    Period,
    Room,
    School,
    SchoolMembership,
    StudentGroup,
    Subject,
    Teacher,
)


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at"]
    search_fields = ["name"]
    ordering = ["name"]


@admin.register(SchoolMembership)
class SchoolMembershipAdmin(admin.ModelAdmin):
    list_display = ["user", "school", "role", "created_at"]
    list_filter = ["role", "school"]
    search_fields = ["user__username", "school__name"]
    list_select_related = ["user", "school"]
    ordering = ["school", "user"]


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ["name", "school", "default_period_duration"]
    list_filter = ["school"]
    search_fields = ["name", "school__name"]
    list_select_related = ["school"]
    ordering = ["school", "-name"]


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "school"]
    list_filter = ["school"]
    search_fields = ["name", "email", "school__name"]
    list_select_related = ["school"]
    ordering = ["school", "name"]


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ["name", "capacity", "school"]
    list_filter = ["school"]
    search_fields = ["name", "school__name"]
    list_select_related = ["school"]
    ordering = ["school", "name"]


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "school"]
    list_filter = ["school"]
    search_fields = ["name", "code", "school__name"]
    list_select_related = ["school"]
    ordering = ["school", "name"]


@admin.register(StudentGroup)
class StudentGroupAdmin(admin.ModelAdmin):
    list_display = ["name", "size", "school"]
    list_filter = ["school"]
    search_fields = ["name", "school__name"]
    list_select_related = ["school"]
    ordering = ["school", "name"]


@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    list_display = ["academic_year", "order", "name", "start_time", "end_time", "kind"]
    list_filter = ["academic_year", "kind"]
    search_fields = ["name", "academic_year__name"]
    list_select_related = ["academic_year"]
    ordering = ["academic_year", "order"]
