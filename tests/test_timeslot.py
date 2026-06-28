from datetime import time

from app.domain.models import Period, PeriodKind


def test_period_contains_reusable_timing_and_kind():
    period = Period(1, 2026, "Lunch", 4, time(12), time(13), PeriodKind.BREAK)

    assert period.academic_year_id == 2026
    assert period.name == "Lunch"
    assert period.order == 4
    assert period.start_time == time(12)
    assert period.end_time == time(13)
    assert period.kind == PeriodKind.BREAK
