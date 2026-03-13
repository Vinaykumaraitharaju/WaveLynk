from database import fetch_all, fetch_one
from utils import today_str, format_dt
from modules.breaks import get_break_timer
from modules.holidays import is_today_holiday


def get_live_status():
    holiday = is_today_holiday()

    rows = fetch_all(
        """
        SELECT u.id,
               u.employee_id,
               u.full_name,
               u.role,
               u.department,
               u.employment_status,
               a.id AS attendance_id,
               a.status,
               a.login_time,
               a.logout_time,
               a.break_minutes
        FROM users u
        LEFT JOIN attendance a
          ON a.user_id = u.id AND a.attendance_date = ?
        WHERE u.is_active = 1
        ORDER BY CAST(u.employee_id AS INTEGER)
        """,
        (today_str(),),
    )

    data = []

    for r in rows:
        status = r["status"] or "Offline"
        break_type = "-"
        break_timer = "-"

        if holiday and status in ["Offline", "Not Started"]:
            status = "Holiday"

        if r["attendance_id"] and status == "On Break":
            timer = get_break_timer(r["attendance_id"])
            if timer:
                break_type = timer["break_type"]

                if timer["is_exceeded"]:
                    break_timer = f"Exceeded by {timer['exceeded']}m"
                else:
                    break_timer = (
                        f"{timer['used_minutes']}m / {timer['allowed_minutes']}m"
                    )

        data.append(
            {
                "Employee ID": r["employee_id"],
                "Employee": r["full_name"],
                "Role": r["role"],
                "Department": r["department"],
                "Employment Status": r["employment_status"],
                "Status": status,
                "Break Type": break_type,
                "Break Timer": break_timer,
                "Login": format_dt(r["login_time"]),
                "Logout": format_dt(r["logout_time"]),
            }
        )

    return data


def get_live_status_counts():
    present = fetch_one(
        """
        SELECT COUNT(*) AS c
        FROM attendance
        WHERE attendance_date = ? AND login_time IS NOT NULL
        """,
        (today_str(),),
    )["c"]

    on_break = fetch_one(
        """
        SELECT COUNT(*) AS c
        FROM attendance
        WHERE attendance_date = ? AND status = 'On Break'
        """,
        (today_str(),),
    )["c"]

    working = fetch_one(
        """
        SELECT COUNT(*) AS c
        FROM attendance
        WHERE attendance_date = ? AND status = 'Working'
        """,
        (today_str(),),
    )["c"]

    completed = fetch_one(
        """
        SELECT COUNT(*) AS c
        FROM attendance
        WHERE attendance_date = ? AND status = 'Completed'
        """,
        (today_str(),),
    )["c"]

    not_started = fetch_one(
        """
        SELECT COUNT(*) AS c
        FROM users u
        WHERE u.is_active = 1
          AND u.id NOT IN (
              SELECT a.user_id
              FROM attendance a
              WHERE a.attendance_date = ?
          )
        """,
        (today_str(),),
    )["c"]

    on_leave = fetch_one(
        """
        SELECT COUNT(*) AS c
        FROM leave_requests
        WHERE status = 'Approved'
          AND from_date <= ?
          AND to_date >= ?
        """,
        (today_str(), today_str()),
    )["c"]

    holiday = is_today_holiday()
    holiday_workers = present if holiday else 0

    return {
        "present": present,
        "on_break": on_break,
        "working": working,
        "completed": completed,
        "not_started": not_started,
        "on_leave": on_leave,
        "holiday_workers": holiday_workers,
        "holiday_name": holiday["holiday_name"] if holiday else "",
    }
