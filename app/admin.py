from django.contrib import admin

from app.infrastructure.database.models import Lesson, Room, StudentGroup, Subject, Teacher, TimeSlot


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ["name", "email"]
    search_fields = ["name", "email"]


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ["name", "capacity"]
    search_fields = ["name"]


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ["name", "code"]
    search_fields = ["name", "code"]


@admin.register(StudentGroup)
class StudentGroupAdmin(admin.ModelAdmin):
    list_display = ["name", "size"]
    search_fields = ["name"]


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ["day", "start_time", "end_time"]
    list_filter = ["day"]
    search_fields = ["day"]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ["subject", "teacher", "room", "student_group", "time_slot"]
    list_filter = ["teacher", "room", "student_group", "time_slot__day"]
    search_fields = [
        "subject__name",
        "teacher__name",
        "room__name",
        "student_group__name",
    ]
