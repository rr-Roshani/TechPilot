from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP


def percentage(numerator, denominator):
    """Return a whole-number percentage, rounding half up and handling zero."""
    if not denominator:
        return 0
    value = Decimal(numerator) * Decimal(100) / Decimal(denominator)
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def summarize_missions(mission_rows):
    """Count scheduled day slots against the 20 mission career plan."""
    by_day = {}
    for row in mission_rows:
        by_day.setdefault(row["day_number"], []).append(row)

    completed_days = 0
    earned_xp = 0
    for rows in by_day.values():
        completed_rows = [row for row in rows if row["completed"]]
        if completed_rows:
            completed_days += 1
            # A day is one planned mission. Duplicate database rows must not
            # award its XP more than once.
            earned_xp += completed_rows[0]["xp"]

    # The career plan always offers 20 mission days, including before a user
    # has opened the missions page and generated their database rows.
    total_days = 20
    return {
        "mission_count": total_days,
        "missions_completed": completed_days,
        "mission_progress": percentage(completed_days, total_days),
        "earned_xp": earned_xp,
    }


def assessment_percentage(attempt):
    """Calculate a completed attempt's score from its saved answer counts."""
    if (
        attempt is None
        or not attempt.is_completed
        or attempt.total_questions <= 0
        or not 0 <= attempt.correct_answers <= attempt.total_questions
    ):
        return 0
    return percentage(attempt.correct_answers, attempt.total_questions)


def current_day_streak(completion_dates, today):
    """Count consecutive distinct completion dates ending today or yesterday."""
    dates = set(completion_dates)
    anchor = today if today in dates else today - timedelta(days=1)
    streak = 0
    while anchor in dates:
        streak += 1
        anchor -= timedelta(days=1)
    return streak
