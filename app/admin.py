from django.contrib import admin

from app.infrastructure.database.models import (
    AcademicYear,
    Period,
    Room,
    StudentGroup,
    Subject,
    Teacher,
)


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ["name", "default_period_duration"]
    search_fields = ["name"]
    ordering = ["-name"]


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ["name", "email"]
    search_fields = ["name", "email"]
    ordering = ["name"]


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ["name", "capacity"]
    search_fields = ["name"]
    ordering = ["name"]


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ["name", "code"]
    search_fields = ["name", "code"]
    ordering = ["name"]


@admin.register(StudentGroup)
class StudentGroupAdmin(admin.ModelAdmin):
    list_display = ["name", "size"]
    search_fields = ["name"]
    ordering = ["name"]


@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    list_display = ["academic_year", "order", "name", "start_time", "end_time", "kind"]
    list_filter = ["academic_year", "kind"]
    search_fields = ["name", "academic_year__name"]
    list_select_related = ["academic_year"]
    ordering = ["academic_year", "order"]
