from datetime import time

from app.application.ports.repositories import ScheduledLesson
from app.application.services.substitution_service import SubstitutionService
from app.domain.models import Day, Period, PeriodKind, Teacher


def make_period(order, kind=PeriodKind.LESSON):
    return Period(
        order,
        1,
        f"Period {order}",
        order,
        time(8 + order),
        time(9 + order),
        kind,
    )


def scheduled(
    lesson_id,
    day=Day.MONDAY,
    order=1,
    teacher_id=1,
    room_id=1,
    group_id=1,
):
    return ScheduledLesson(
        id=lesson_id,
        teacher_id=teacher_id,
        teacher_name=f"Teacher {teacher_id}",
        subject_name="Math",
        room_id=room_id,
        room_name=f"Room {room_id}",
        student_group_id=group_id,
        student_group_name=f"Group {group_id}",
        day=day,
        start_period=make_period(order),
    )


class FakeLessonRepository:
    def __init__(self, lessons=None, teachers=None):
        self.lessons = lessons or []
        self.teachers = teachers or []
        self.planned_substitutes = {}

    def list_teachers(self):
        return self.teachers

    def list_lessons(self, academic_year_id):
        return [
            lesson
            for lesson in self.lessons
            if lesson.start_period.academic_year_id == academic_year_id
        ]

    def list_lessons_starting_at(self, academic_year_id, day, period_id):
        return [
            lesson
            for lesson in self.lessons
            if lesson.start_period.academic_year_id == academic_year_id
            and lesson.day == day
            and lesson.start_period.id == period_id
        ]

    def list_lessons_for_teacher(self, teacher_id, academic_year_id):
        return [
            lesson
            for lesson in self.lessons
            if lesson.teacher_id == teacher_id
            and lesson.start_period.academic_year_id == academic_year_id
        ]

    def set_planned_substitute(self, lesson_id, teacher_id):
        self.planned_substitutes[lesson_id] = teacher_id


def test_available_teachers_excludes_teachers_with_lesson_starting_in_selected_period():
    teachers = [
        Teacher(id=1, name="Ada"),
        Teacher(id=2, name="Grace"),
        Teacher(id=3, name="Katherine"),
    ]

    lessons = [
        scheduled(1, teacher_id=1, day=Day.MONDAY, order=1),
        scheduled(2, teacher_id=2, day=Day.MONDAY, order=2),
        scheduled(3, teacher_id=3, day=Day.TUESDAY, order=1),
    ]

    repository = FakeLessonRepository(
        lessons=lessons,
        teachers=teachers,
    )

    service = SubstitutionService(repository)

    result = service.available_teachers(1, Day.MONDAY, 1)

    assert [teacher.name for teacher in result] == ["Grace", "Katherine"]


def test_available_teachers_returns_all_teachers_when_schedule_is_empty():
    teachers = [
        Teacher(id=1, name="Ada"),
        Teacher(id=2, name="Grace"),
    ]

    repository = FakeLessonRepository(teachers=teachers)
    service = SubstitutionService(repository)

    result = service.available_teachers(1, Day.MONDAY, 1)

    assert result == teachers


def test_available_teachers_excludes_absent_teacher():
    teachers = [
        Teacher(id=1, name="Ada"),
        Teacher(id=2, name="Grace"),
    ]

    repository = FakeLessonRepository(teachers=teachers)
    service = SubstitutionService(repository)

    result = service.available_teachers(
        1,
        Day.MONDAY,
        1,
        excluded_teacher_id=1,
    )

    assert [teacher.id for teacher in result] == [2]


def test_generate_plan_breaks_ties_by_teacher_id():
    teachers = [
        Teacher(id=3, name="Katherine"),
        Teacher(id=1, name="Ada"),
        Teacher(id=2, name="Grace"),
    ]
    lessons = [
        scheduled(1, teacher_id=1, day=Day.MONDAY, order=1),
    ]

    repository = FakeLessonRepository(lessons=lessons, teachers=teachers)
    service = SubstitutionService(repository)

    plan = service.generate_plan(teacher_id=1, academic_year_id=1)

    assert [assignment.substitute.id for assignment in plan] == [2]


def test_generate_plan_distributes_substitutions_fairly():
    teachers = [
        Teacher(id=1, name="Ada"),
        Teacher(id=2, name="Grace"),
        Teacher(id=3, name="Katherine"),
    ]
    lessons = [
        scheduled(1, teacher_id=1, day=Day.MONDAY, order=1),
        scheduled(2, teacher_id=1, day=Day.MONDAY, order=2),
        scheduled(3, teacher_id=1, day=Day.TUESDAY, order=1),
        scheduled(4, teacher_id=1, day=Day.TUESDAY, order=2),
    ]

    repository = FakeLessonRepository(lessons=lessons, teachers=teachers)
    service = SubstitutionService(repository)

    plan = service.generate_plan(teacher_id=1, academic_year_id=1)

    assert [assignment.substitute.id for assignment in plan] == [2, 3, 2, 3]


def test_generate_plan_updates_counts_as_generation_progresses():
    teachers = [
        Teacher(id=1, name="Ada"),
        Teacher(id=2, name="Grace"),
        Teacher(id=3, name="Katherine"),
    ]
    lessons = [
        scheduled(1, teacher_id=1, day=Day.MONDAY, order=1),
        scheduled(2, teacher_id=3, day=Day.MONDAY, order=1),
        scheduled(3, teacher_id=1, day=Day.MONDAY, order=2),
    ]

    repository = FakeLessonRepository(lessons=lessons, teachers=teachers)
    service = SubstitutionService(repository)

    plan = service.generate_plan(teacher_id=1, academic_year_id=1)

    assert [assignment.substitute.id for assignment in plan] == [2, 3]


def test_generate_planned_substitutions_excludes_regular_teacher():
    teachers = [
        Teacher(id=1, name="Ada"),
        Teacher(id=2, name="Grace"),
    ]
    lessons = [
        scheduled(1, teacher_id=1, day=Day.MONDAY, order=1),
    ]

    repository = FakeLessonRepository(lessons=lessons, teachers=teachers)
    plan = SubstitutionService(repository).generate_planned_substitutions(1)

    assert [assignment.substitute.id for assignment in plan] == [2]
    assert repository.planned_substitutes == {1: 2}


def test_generate_planned_substitutions_excludes_teachers_teaching_that_period():
    teachers = [
        Teacher(id=1, name="Ada"),
        Teacher(id=2, name="Grace"),
        Teacher(id=3, name="Katherine"),
    ]
    lessons = [
        scheduled(1, teacher_id=1, day=Day.MONDAY, order=1),
        scheduled(2, teacher_id=2, day=Day.MONDAY, order=1),
    ]

    repository = FakeLessonRepository(lessons=lessons, teachers=teachers)
    plan = SubstitutionService(repository).generate_planned_substitutions(1)

    assert [
        assignment.substitute.id if assignment.substitute is not None else None
        for assignment in plan
    ] == [3, None]
    assert repository.planned_substitutes == {1: 3, 2: None}


def test_generate_planned_substitutions_excludes_substitutes_already_assigned_that_period():
    teachers = [
        Teacher(id=1, name="Ada"),
        Teacher(id=2, name="Grace"),
        Teacher(id=3, name="Katherine"),
        Teacher(id=4, name="Dorothy"),
    ]
    lessons = [
        scheduled(1, teacher_id=1, day=Day.MONDAY, order=1),
        scheduled(2, teacher_id=2, day=Day.MONDAY, order=1),
    ]

    repository = FakeLessonRepository(lessons=lessons, teachers=teachers)
    plan = SubstitutionService(repository).generate_planned_substitutions(1)

    assert [assignment.substitute.id for assignment in plan] == [3, 4]
    assert repository.planned_substitutes == {1: 3, 2: 4}


def test_generate_planned_substitutions_distributes_fairly():
    teachers = [
        Teacher(id=1, name="Ada"),
        Teacher(id=2, name="Grace"),
        Teacher(id=3, name="Katherine"),
    ]
    lessons = [
        scheduled(1, teacher_id=1, day=Day.MONDAY, order=1),
        scheduled(2, teacher_id=1, day=Day.MONDAY, order=2),
        scheduled(3, teacher_id=1, day=Day.TUESDAY, order=1),
        scheduled(4, teacher_id=1, day=Day.TUESDAY, order=2),
    ]

    repository = FakeLessonRepository(lessons=lessons, teachers=teachers)
    plan = SubstitutionService(repository).generate_planned_substitutions(1)

    assert [assignment.substitute.id for assignment in plan] == [2, 3, 2, 3]


def test_generate_planned_substitutions_breaks_ties_by_teacher_id():
    teachers = [
        Teacher(id=3, name="Katherine"),
        Teacher(id=1, name="Ada"),
        Teacher(id=2, name="Grace"),
    ]
    lessons = [
        scheduled(1, teacher_id=1, day=Day.MONDAY, order=1),
    ]

    repository = FakeLessonRepository(lessons=lessons, teachers=teachers)
    plan = SubstitutionService(repository).generate_planned_substitutions(1)

    assert [assignment.substitute.id for assignment in plan] == [2]


def test_generate_planned_substitutions_leaves_lesson_empty_when_no_substitute_available():
    teachers = [
        Teacher(id=1, name="Ada"),
    ]
    lessons = [
        scheduled(1, teacher_id=1, day=Day.MONDAY, order=1),
    ]

    repository = FakeLessonRepository(lessons=lessons, teachers=teachers)
    plan = SubstitutionService(repository).generate_planned_substitutions(1)

    assert [assignment.substitute for assignment in plan] == [None]
    assert repository.planned_substitutes == {1: None}


def test_generate_planned_substitutions_updates_counts_as_generation_progresses():
    teachers = [
        Teacher(id=1, name="Ada"),
        Teacher(id=2, name="Grace"),
        Teacher(id=3, name="Katherine"),
    ]
    lessons = [
        scheduled(1, teacher_id=1, day=Day.MONDAY, order=1),
        scheduled(2, teacher_id=3, day=Day.MONDAY, order=1),
        scheduled(3, teacher_id=1, day=Day.MONDAY, order=2),
    ]

    repository = FakeLessonRepository(lessons=lessons, teachers=teachers)
    plan = SubstitutionService(repository).generate_planned_substitutions(1)

    assert [
        assignment.substitute.id if assignment.substitute is not None else None
        for assignment in plan
    ] == [2, None, 3]
