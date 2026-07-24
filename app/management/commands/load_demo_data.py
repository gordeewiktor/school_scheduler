from __future__ import annotations

from dataclasses import dataclass
from datetime import time

from django.core.management.base import BaseCommand

from app.application.services.conflicts import ConflictService
from app.application.services.schedules import ScheduleService
from app.application.services.substitution_service import SubstitutionService
from app.infrastructure.database.models import (
    AcademicYear,
    Lesson,
    Period,
    Room,
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


class Command(BaseCommand):
    help = "Load complete demo school data, including a generated timetable."

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

    def handle(self, *args, **options) -> None:
        self.stdout.write("Loading demo school...")
        self.stdout.write("")

        self.stdout.write("Creating academic year and periods...")
        academic_year = self._load_academic_year()
        self._load_periods(academic_year)
        self.stdout.write(self.style.SUCCESS("OK"))

        self.stdout.write("Creating teachers...")
        self._load_teachers()
        self.stdout.write(self.style.SUCCESS("OK"))

        self.stdout.write("Creating student groups...")
        self._load_student_groups()
        self.stdout.write(self.style.SUCCESS("OK"))

        self.stdout.write("Creating rooms...")
        self._load_rooms()
        self.stdout.write(self.style.SUCCESS("OK"))

        self.stdout.write("Creating subjects...")
        self._load_subjects()
        self.stdout.write(self.style.SUCCESS("OK"))

        self.stdout.write("Generating timetable...")
        self._clear_lessons(academic_year)
        result = self._generate_timetable(academic_year)
        self.stdout.write(self.style.SUCCESS("########## 100%"))
        self.stdout.write(f"Lessons created: {result.lessons_created}")

        self.stdout.write("Generating planned substitutions...")
        self._substitution_service().generate_planned_substitutions(academic_year.id)
        self.stdout.write(self.style.SUCCESS("OK"))
        self.stdout.write("")

        self.stdout.write(self.style.SUCCESS("Demo school loaded successfully."))
        self.stdout.write("")
        self.stdout.write(f"Academic years: {AcademicYear.objects.count()}")
        self.stdout.write(f"Teachers: {Teacher.objects.count()}")
        self.stdout.write(f"Student groups: {StudentGroup.objects.count()}")
        self.stdout.write(f"Rooms: {Room.objects.count()}")
        self.stdout.write(f"Subjects: {Subject.objects.count()}")
        self.stdout.write(
            "Periods: "
            f"{Period.objects.filter(academic_year=academic_year, kind=Period.Kind.LESSON).count()}"
        )
        self.stdout.write(
            "Breaks: "
            f"{Period.objects.filter(academic_year=academic_year, kind=Period.Kind.BREAK).count()}"
        )
        self.stdout.write(
            "Lessons: "
            f"{Lesson.objects.filter(start_period__academic_year=academic_year).count()}"
        )
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Done."))

    def _load_academic_year(self) -> AcademicYear:
        existing = AcademicYear.objects.first()
        if existing is not None:
            return existing
        return AcademicYear.objects.create(
            name=self.ACADEMIC_YEAR_NAME,
            default_period_duration=45,
        )

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

    def _load_teachers(self) -> None:
        for index in range(1, 81):
            Teacher.objects.update_or_create(
                name=f"Teacher {index:02d}",
                defaults={"email": ""},
            )

    def _load_student_groups(self) -> None:
        for index in range(1, 51):
            StudentGroup.objects.update_or_create(
                name=f"Class {index:02d}",
                defaults={"size": None},
            )

    def _load_rooms(self) -> None:
        for index in range(1, 51):
            Room.objects.update_or_create(
                name=f"Room {index:02d}",
                defaults={"capacity": None},
            )

    def _load_subjects(self) -> None:
        for name, code in self.SUBJECTS:
            Subject.objects.update_or_create(
                name=name,
                defaults={"code": code},
            )

    def _clear_lessons(self, academic_year: AcademicYear) -> None:
        Lesson.objects.filter(start_period__academic_year=academic_year).delete()

    def _generate_timetable(self, academic_year: AcademicYear):
        generator = DemoTimetableGenerator(self._schedule_service())
        return generator.generate(
            academic_year_id=academic_year.id,
            student_groups=self._demo_student_groups(),
            rooms=self._demo_rooms(),
            subjects=self._demo_subjects(),
            teachers=self._demo_teachers(),
        )

    @staticmethod
    def _schedule_service() -> ScheduleService:
        repository = DjangoLessonRepository()
        return ScheduleService(repository, ConflictService(repository))

    @staticmethod
    def _substitution_service() -> SubstitutionService:
        return SubstitutionService(DjangoLessonRepository())

    @staticmethod
    def _demo_teachers() -> list[Teacher]:
        names = [f"Teacher {index:02d}" for index in range(1, 81)]
        return list(Teacher.objects.filter(name__in=names).order_by("name"))

    @staticmethod
    def _demo_student_groups() -> list[StudentGroup]:
        names = [f"Class {index:02d}" for index in range(1, 51)]
        return list(StudentGroup.objects.filter(name__in=names).order_by("name"))

    @staticmethod
    def _demo_rooms() -> list[Room]:
        names = [f"Room {index:02d}" for index in range(1, 51)]
        return list(Room.objects.filter(name__in=names).order_by("name"))

    def _demo_subjects(self) -> list[Subject]:
        return [
            Subject.objects.get(name=name)
            for name, _code in self.SUBJECTS
        ]
