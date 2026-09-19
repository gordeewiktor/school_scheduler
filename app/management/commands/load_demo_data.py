from __future__ import annotations

from dataclasses import dataclass
from datetime import time

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from app.application.services.conflicts import ConflictService
from app.application.services.registration import register_principal
from app.application.services.schedules import ScheduleService
from app.application.services.substitution_service import SubstitutionService
from app.infrastructure.database.models import (
    AcademicYear,
    Lesson,
    Period,
    Room,
    School,
    SchoolMembership,
    StudentGroup,
    Subject,
    Teacher,
)
from app.infrastructure.repositories.django_lessons import DjangoLessonRepository
from app.management.demo_timetable import DemoTimetableGenerator


@dataclass(frozen=True, slots=True)
class DemoPeriod:
    name: str
    start_time: time
    end_time: time
    kind: str


@dataclass(frozen=True, slots=True)
class DemoSchoolSpec:
    school_name: str
    username: str
    password: str


class Command(BaseCommand):
    help = (
        "Load demo data for two independent, isolated demo schools — "
        "useful for manually exercising the multi-school application."
    )

    # Deliberately identical across both demo schools — this is what
    # lets the loaded data demonstrate that same-named records
    # (academic year, teachers, subjects, rooms, student groups) stay
    # fully independent once they belong to different Schools. Only
    # the School name and principal login differ per school.
    ACADEMIC_YEAR_NAME = "Demo 2026"

    SUBJECTS = (
        ("English", "ENG"),
        ("Math", "MATH"),
        ("Science", "SCI"),
        ("Thai", "THAI"),
        ("Social Studies", "SOC"),
        ("Art", "ART"),
        ("Music", "MUS"),
        ("P.E.", "PE"),
        ("Computer", "COMP"),
        ("Activity", "ACT"),
    )

    PERIODS = (
        DemoPeriod("Homeroom", time(8, 0), time(8, 30), Period.Kind.LESSON),
        DemoPeriod("Period 1", time(8, 30), time(9, 15), Period.Kind.LESSON),
        DemoPeriod("Period 2", time(9, 15), time(10, 0), Period.Kind.LESSON),
        DemoPeriod("Morning Break", time(10, 0), time(10, 30), Period.Kind.BREAK),
        DemoPeriod("Period 3", time(10, 30), time(11, 15), Period.Kind.LESSON),
        DemoPeriod("Period 4", time(11, 15), time(12, 0), Period.Kind.LESSON),
        DemoPeriod("Lunch Break", time(12, 0), time(12, 50), Period.Kind.BREAK),
        DemoPeriod("Period 5", time(12, 50), time(13, 35), Period.Kind.LESSON),
        DemoPeriod("Period 6", time(13, 35), time(14, 20), Period.Kind.LESSON),
        DemoPeriod("Period 7", time(14, 20), time(15, 5), Period.Kind.LESSON),
        DemoPeriod("Period 8", time(15, 5), time(15, 50), Period.Kind.LESSON),
        DemoPeriod("After School", time(15, 50), time(16, 30), Period.Kind.LESSON),
    )

    # 10 rooms/groups (matched 1:1 — the timetable generator dedicates
    # one room per student group for the whole week) and 16 teachers
    # (more than the 10 needed at any single moment, so some teachers
    # are always free — enough to make substitution generation
    # meaningful rather than trivially empty).
    TEACHER_NAMES = (
        "Alice Chen", "Ben Carter", "Carla Diaz", "David Kim",
        "Ella Brown", "Frank Lopez", "Grace Kim", "Henry Wolfe",
        "Ivy Novak", "Jack Ortiz", "Kelly Adams", "Liam Young",
        "Maya Patel", "Noah Scott", "Olivia Reyes", "Peter Hughes",
    )
    ROOM_NAMES = (
        "Room 101", "Room 102", "Room 103", "Room 104", "Room 105",
        "Lab 1", "Lab 2", "Gym", "Art Studio", "Library",
    )
    STUDENT_GROUP_NAMES = (
        "Grade 7A", "Grade 7B", "Grade 8A", "Grade 8B",
        "Grade 9A", "Grade 9B", "Grade 10A", "Grade 10B",
        "Grade 11A", "Grade 11B",
    )

    DEMO_SCHOOLS = (
        DemoSchoolSpec("Riverside High", "principal_riverside", "Demo-Pass-2026!"),
        DemoSchoolSpec("Lincoln Academy", "principal_lincoln", "Demo-Pass-2026!"),
    )

    def handle(self, *args, **options) -> None:
        self.stdout.write("Loading demo data for two independent schools...")
        self.stdout.write("")

        for spec in self.DEMO_SCHOOLS:
            self._load_school(spec)

        self.stdout.write(self.style.SUCCESS("All demo schools loaded successfully."))
        self.stdout.write("")
        self.stdout.write("Login credentials:")
        for spec in self.DEMO_SCHOOLS:
            self.stdout.write(f"  {spec.school_name}: {spec.username} / {spec.password}")

    def _load_school(self, spec: DemoSchoolSpec) -> None:
        self.stdout.write(f"=== {spec.school_name} ===")

        school = self._load_school_and_principal(spec)
        academic_year = self._load_academic_year(school)
        self._load_periods(academic_year)
        self._load_teachers(school)
        self._load_student_groups(school)
        self._load_rooms(school)
        self._load_subjects(school)

        self.stdout.write("Generating timetable...")
        self._clear_lessons(academic_year)
        result = self._generate_timetable(academic_year)
        self.stdout.write(f"Lessons created: {result.lessons_created}")

        self.stdout.write("Generating planned substitutions...")
        self._substitution_service().generate_planned_substitutions(academic_year.id)

        self.stdout.write(self.style.SUCCESS(f"{spec.school_name}: OK"))
        self.stdout.write(f"  Login: {spec.username} / {spec.password}")
        self.stdout.write(f"  Teachers: {Teacher.objects.filter(school=school).count()}")
        self.stdout.write(
            f"  Student groups: {StudentGroup.objects.filter(school=school).count()}"
        )
        self.stdout.write(f"  Rooms: {Room.objects.filter(school=school).count()}")
        self.stdout.write(f"  Subjects: {Subject.objects.filter(school=school).count()}")
        self.stdout.write(
            "  Periods: "
            f"{Period.objects.filter(academic_year=academic_year, kind=Period.Kind.LESSON).count()}"
        )
        self.stdout.write(
            "  Breaks: "
            f"{Period.objects.filter(academic_year=academic_year, kind=Period.Kind.BREAK).count()}"
        )
        self.stdout.write(
            "  Lessons: "
            f"{Lesson.objects.filter(start_period__academic_year=academic_year).count()}"
        )
        self.stdout.write("")

    def _load_school_and_principal(self, spec: DemoSchoolSpec) -> School:
        """Idempotent: if this demo principal's username already
        exists, reuse the School they were originally registered
        with (looked up via their own PRINCIPAL SchoolMembership) —
        never a fresh School, and never any other pre-existing School
        or AcademicYear in the database. Only on a genuinely first run
        does this create a new User/School/SchoolMembership, via the
        same register_principal() atomic operation the web
        registration flow uses.
        """
        User = get_user_model()
        existing_user = User.objects.filter(username=spec.username).first()
        if existing_user is not None:
            membership = SchoolMembership.objects.get(
                user=existing_user, role=SchoolMembership.Role.PRINCIPAL
            )
            return membership.school

        _user, school, _membership = register_principal(
            username=spec.username,
            password=spec.password,
            school_name=spec.school_name,
        )
        return school

    def _load_academic_year(self, school: School) -> AcademicYear:
        academic_year, _created = AcademicYear.objects.get_or_create(
            school=school,
            name=self.ACADEMIC_YEAR_NAME,
            defaults={"default_period_duration": 45},
        )
        return academic_year

    def _load_periods(self, academic_year: AcademicYear) -> None:
        for order, period in enumerate(self.PERIODS, start=1):
            Period.objects.update_or_create(
                academic_year=academic_year,
                order=order,
                defaults={
                    "name": period.name,
                    "start_time": period.start_time,
                    "end_time": period.end_time,
                    "kind": period.kind,
                },
            )

    def _load_teachers(self, school: School) -> None:
        for name in self.TEACHER_NAMES:
            Teacher.objects.update_or_create(
                school=school, name=name, defaults={"email": ""}
            )

    def _load_student_groups(self, school: School) -> None:
        for name in self.STUDENT_GROUP_NAMES:
            StudentGroup.objects.update_or_create(
                school=school, name=name, defaults={"size": None}
            )

    def _load_rooms(self, school: School) -> None:
        for name in self.ROOM_NAMES:
            Room.objects.update_or_create(
                school=school, name=name, defaults={"capacity": None}
            )

    def _load_subjects(self, school: School) -> None:
        for name, code in self.SUBJECTS:
            Subject.objects.update_or_create(
                school=school, name=name, defaults={"code": code}
            )

    def _clear_lessons(self, academic_year: AcademicYear) -> None:
        Lesson.objects.filter(start_period__academic_year=academic_year).delete()

    def _generate_timetable(self, academic_year: AcademicYear):
        school = academic_year.school
        generator = DemoTimetableGenerator(self._schedule_service())
        return generator.generate(
            academic_year_id=academic_year.id,
            student_groups=self._demo_student_groups(school),
            rooms=self._demo_rooms(school),
            subjects=self._demo_subjects(school),
            teachers=self._demo_teachers(school),
        )

    @staticmethod
    def _schedule_service() -> ScheduleService:
        repository = DjangoLessonRepository()
        return ScheduleService(repository, ConflictService(repository))

    @staticmethod
    def _substitution_service() -> SubstitutionService:
        return SubstitutionService(DjangoLessonRepository())

    def _demo_teachers(self, school: School) -> list[Teacher]:
        return list(
            Teacher.objects.filter(
                school=school, name__in=self.TEACHER_NAMES
            ).order_by("name")
        )

    def _demo_student_groups(self, school: School) -> list[StudentGroup]:
        return list(
            StudentGroup.objects.filter(
                school=school, name__in=self.STUDENT_GROUP_NAMES
            ).order_by("name")
        )

    def _demo_rooms(self, school: School) -> list[Room]:
        return list(
            Room.objects.filter(school=school, name__in=self.ROOM_NAMES).order_by("name")
        )

    def _demo_subjects(self, school: School) -> list[Subject]:
        return [
            Subject.objects.get(school=school, name=name) for name, _code in self.SUBJECTS
        ]
