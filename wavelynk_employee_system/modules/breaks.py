from database import fetch_one, execute
from utils import now_str, parse_dt, minutes_between, today_str
from modules.policies import get_policy


def get_break_limit(break_type: str):
    policy = get_policy()
    mapping = {
        "Tea Break": int(policy["tea_break_minutes"]),
        "Lunch Break": int(policy["lunch_break_minutes"]),
        "Personal Break": int(policy["personal_break_minutes"]),
    }
    return mapping.get(break_type, int(policy["personal_break_minutes"]))


def get_active_break(attendance_id: int):
    row = fetch_one(
        """
        SELECT *
        FROM breaks
        WHERE attendance_id = ? AND status = 'Active'
        ORDER BY id DESC
        LIMIT 1
        """,
        (attendance_id,),
    )
    return row


def get_break_timer(attendance_id: int):
    row = get_active_break(attendance_id)
    if not row:
        return None

    used = minutes_between(parse_dt(row["break_start"]), parse_dt(now_str()))
    allowed = int(row["allowed_minutes"] or 0)
    remaining = allowed - used
    exceeded = max(used - allowed, 0)

    return {
        "break_type": row["break_type"],
        "break_start": row["break_start"],
        "allowed_minutes": allowed,
        "used_minutes": used,
        "remaining_minutes": remaining,
        "exceeded": exceeded,
        "is_exceeded": exceeded > 0,
    }


def end_break_by_user(user_id: int):
    attendance = fetch_one(
        """
        SELECT *
        FROM attendance
        WHERE user_id = ? AND attendance_date = ?
        """,
        (user_id, today_str()),
    )

    if not attendance:
        return False, "Attendance not found for today."

    active_break = get_active_break(attendance["id"])
    if not active_break:
        return False, "No active break found."

    end_time = now_str()
    actual_minutes = minutes_between(
        parse_dt(active_break["break_start"]), parse_dt(end_time)
    )
    allowed = int(active_break["allowed_minutes"] or 0)
    exceeded = max(actual_minutes - allowed, 0)

    execute(
        """
        UPDATE breaks
        SET break_end = ?,
            actual_minutes = ?,
            exceeded_minutes = ?,
            status = 'Completed'
        WHERE id = ?
        """,
        (end_time, actual_minutes, exceeded, active_break["id"]),
    )

    execute(
        """
        UPDATE attendance
        SET break_minutes = break_minutes + ?,
            status = 'Working'
        WHERE id = ?
        """,
        (actual_minutes, attendance["id"]),
    )

    if exceeded > 0:
        return True, f"Break ended. You exceeded by {exceeded} minute(s)."

    return True, "Break ended successfully."
