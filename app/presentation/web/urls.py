from django.urls import path

from app.presentation.web import views

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("schedule/", views.ScheduleView.as_view(), name="schedule"),
    path("teachers/", views.TeacherListView.as_view(), name="teacher-list"),
    path("teachers/new/", views.TeacherCreateView.as_view(), name="teacher-create"),
    path("teachers/<int:pk>/edit/", views.TeacherUpdateView.as_view(), name="teacher-update"),
    path("teachers/<int:pk>/delete/", views.TeacherDeleteView.as_view(), name="teacher-delete"),
    path("rooms/", views.RoomListView.as_view(), name="room-list"),
    path("rooms/new/", views.RoomCreateView.as_view(), name="room-create"),
    path("rooms/<int:pk>/edit/", views.RoomUpdateView.as_view(), name="room-update"),
    path("rooms/<int:pk>/delete/", views.RoomDeleteView.as_view(), name="room-delete"),
    path("subjects/", views.SubjectListView.as_view(), name="subject-list"),
    path("subjects/new/", views.SubjectCreateView.as_view(), name="subject-create"),
    path("subjects/<int:pk>/edit/", views.SubjectUpdateView.as_view(), name="subject-update"),
    path("subjects/<int:pk>/delete/", views.SubjectDeleteView.as_view(), name="subject-delete"),
    path("student-groups/", views.StudentGroupListView.as_view(), name="student-group-list"),
    path("student-groups/new/", views.StudentGroupCreateView.as_view(), name="student-group-create"),
    path(
        "student-groups/<int:pk>/edit/",
        views.StudentGroupUpdateView.as_view(),
        name="student-group-update",
    ),
    path(
        "student-groups/<int:pk>/delete/",
        views.StudentGroupDeleteView.as_view(),
        name="student-group-delete",
    ),
    path("time-slots/", views.TimeSlotListView.as_view(), name="time-slot-list"),
    path("time-slots/new/", views.TimeSlotCreateView.as_view(), name="time-slot-create"),
    path("time-slots/<int:pk>/edit/", views.TimeSlotUpdateView.as_view(), name="time-slot-update"),
    path(
        "time-slots/<int:pk>/delete/",
        views.TimeSlotDeleteView.as_view(),
        name="time-slot-delete",
    ),
    path("lessons/", views.LessonListView.as_view(), name="lesson-list"),
    path("lessons/new/", views.LessonCreateView.as_view(), name="lesson-create"),
    path("lessons/<int:pk>/edit/", views.LessonUpdateView.as_view(), name="lesson-update"),
    path("lessons/<int:pk>/delete/", views.LessonDeleteView.as_view(), name="lesson-delete"),
]
