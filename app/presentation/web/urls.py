from django.urls import path

from app.presentation.web import views

urlpatterns = [
    path("", views.ScheduleView.as_view(), name="schedule"),
    path(
        "generate-planned-substitutions/",
        views.GeneratePlannedSubstitutionsView.as_view(),
        name="generate-planned-substitutions",
    ),
    path(
        "teacher-substitution/",
        views.TeacherSubstitutionView.as_view(),
        name="teacher-substitution",
    ),
    path("lessons/", views.LessonListView.as_view(), name="lesson-list"),
    path("lessons/new/", views.LessonCreateView.as_view(), name="lesson-create"),
    path("lessons/<int:pk>/edit/", views.LessonUpdateView.as_view(), name="lesson-update"),
    path("lessons/<int:pk>/delete/", views.LessonDeleteView.as_view(), name="lesson-delete"),
]

# Legacy administrator-only CRUD tools. They remain available for compatibility and
# development diagnostics, but Django Admin is the supported management interface.
legacy_management_urlpatterns = [
    path("legacy/teachers/", views.TeacherListView.as_view(), name="teacher-list"),
    path("legacy/teachers/new/", views.TeacherCreateView.as_view(), name="teacher-create"),
    path("legacy/teachers/<int:pk>/edit/", views.TeacherUpdateView.as_view(), name="teacher-update"),
    path("legacy/teachers/<int:pk>/delete/", views.TeacherDeleteView.as_view(), name="teacher-delete"),
    path("legacy/rooms/", views.RoomListView.as_view(), name="room-list"),
    path("legacy/rooms/new/", views.RoomCreateView.as_view(), name="room-create"),
    path("legacy/rooms/<int:pk>/edit/", views.RoomUpdateView.as_view(), name="room-update"),
    path("legacy/rooms/<int:pk>/delete/", views.RoomDeleteView.as_view(), name="room-delete"),
    path("legacy/subjects/", views.SubjectListView.as_view(), name="subject-list"),
    path("legacy/subjects/new/", views.SubjectCreateView.as_view(), name="subject-create"),
    path("legacy/subjects/<int:pk>/edit/", views.SubjectUpdateView.as_view(), name="subject-update"),
    path("legacy/subjects/<int:pk>/delete/", views.SubjectDeleteView.as_view(), name="subject-delete"),
    path("legacy/student-groups/", views.StudentGroupListView.as_view(), name="student-group-list"),
    path("legacy/student-groups/new/", views.StudentGroupCreateView.as_view(), name="student-group-create"),
    path(
        "legacy/student-groups/<int:pk>/edit/",
        views.StudentGroupUpdateView.as_view(),
        name="student-group-update",
    ),
    path(
        "legacy/student-groups/<int:pk>/delete/",
        views.StudentGroupDeleteView.as_view(),
        name="student-group-delete",
    ),
    path("legacy/academic-years/", views.AcademicYearListView.as_view(), name="academic-year-list"),
    path("legacy/academic-years/new/", views.AcademicYearCreateView.as_view(), name="academic-year-create"),
    path(
        "legacy/academic-years/<int:pk>/edit/",
        views.AcademicYearUpdateView.as_view(),
        name="academic-year-update",
    ),
    path(
        "legacy/academic-years/<int:pk>/delete/",
        views.AcademicYearDeleteView.as_view(),
        name="academic-year-delete",
    ),
    path("legacy/periods/", views.PeriodListView.as_view(), name="period-list"),
    path("legacy/periods/new/", views.PeriodCreateView.as_view(), name="period-create"),
    path("legacy/periods/<int:pk>/edit/", views.PeriodUpdateView.as_view(), name="period-update"),
    path("legacy/periods/<int:pk>/delete/", views.PeriodDeleteView.as_view(), name="period-delete"),
]

urlpatterns += legacy_management_urlpatterns
