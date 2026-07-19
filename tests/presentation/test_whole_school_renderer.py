from datetime import time

from app.application.ports.repositories import ScheduledLesson
from app.domain.models import Day, Period, PeriodKind
from app.presentation.web.schedule_renderers import WholeSchoolTimetableRenderer


def period(identifier: int, order: int, kind: PeriodKind = PeriodKind.LESSON) -> Period:
    return Period(
        id=identifier,
        academic_year_id=1,
        name=f"Period {order}",
        order=order,
        start_time=time(8 + order),
        end_time=time(9 + order),
        kind=kind,
    )


def lesson(
    identifier: int,
    start_period: Period,
    subject: str = "Mathematics",
    teacher: str = "Teacher Bobby",
) -> ScheduledLesson:
    return ScheduledLesson(
        id=identifier,
        teacher_id=identifier,
        teacher_name=teacher,
        subject_name=subject,
        room_id=identifier,
        room_name="Room 101",
        student_group_id=identifier,
        student_group_name=f"EP{identifier}",
        day=Day.MONDAY,
        start_period=start_period,
    )


def test_whole_school_renderer_stacks_concurrent_cards():
    periods = [period(1, 1), period(2, 2), period(3, 3)]
    first = lesson(1, periods[0])
    concurrent = lesson(2, periods[0])

    timetable = WholeSchoolTimetableRenderer().render(
        {Day.MONDAY: [first, concurrent]}, periods
    )

    monday = timetable.rows[0]
    assert len(timetable.rows) == 5
    assert monday.lane_count == 2
    assert [(card.column, card.lane) for card in monday.cards] == [
        (2, 1),
        (2, 2),
    ]


def test_whole_school_renderer_uses_compact_display_names_without_room():
    first_period = period(1, 1)

    timetable = WholeSchoolTimetableRenderer().render(
        {Day.MONDAY: [lesson(1, first_period)]}, [first_period]
    )

    card = timetable.rows[0].cards[0]
    assert card.subject == "Math"
    assert card.teacher == "Bobby"
    assert card.student_group == "EP1"
    assert not hasattr(card, "room")


def test_whole_school_renderer_marks_break_columns():
    break_period = period(1, 1, PeriodKind.BREAK)

    timetable = WholeSchoolTimetableRenderer().render({}, [break_period])

    assert all(row.period_cells[0].is_break for row in timetable.rows)
