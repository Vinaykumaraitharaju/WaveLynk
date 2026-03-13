from database import execute, fetch_one, fetch_all
from utils import (
    today_str,
    now_str,
    parse_dt,
    format_dt,
    combine_date_time,
    minutes_between,
)
from modules.policies import get_policy
from modules.breaks import get_break_limit


def _get_today_attendance(user_id: int):
    return fetch_one(
        """
        SELECT *
        FROM attendance
        WHERE user_id = ? AND attendance_date = ?
        """,
        (user_id, today_str()),
    )


def start_work(user_id: int):
    row = _get_today_attendance(user_id)

    # If attendance already exists for today
    if row:
        # Work already ended
        if row["logout_time"]:
            return False, "Work already completed for today."

        # Work already active
        if row["login_time"]:
            if row["status"] == "On Break":
                return False, "You are currently on break. End break first."
            return False, "Work already started."

    policy = get_policy()
    login_now = now_str()
    late_login = 0

    expected_login = combine_date_time(today_str(), policy["login_time"])
    actual_login = parse_dt(login_now)

    if minutes_between(expected_login, actual_login) > int(
        policy["login_grace_minutes"]
    ):
        late_login = 1

    if not row:
        execute(
            """
            INSERT INTO attendance (
                user_id,
                attendance_date,
                login_time,
                status,
                break_minutes,
                late_login,
                early_logout,
                overtime_minutes,
                work_minutes
            )
            VALUES (?, ?, ?, 'Working', 0, ?, 0, 0, 0)
            """,
            (user_id, today_str(), login_now, late_login),
        )
    else:
        execute(
            """
            UPDATE attendance
            SET login_time = ?,
                logout_time = NULL,
                status = 'Working',
                break_minutes = 0,
                late_login = ?,
                early_logout = 0,
                overtime_minutes = 0,
                work_minutes = 0,
                remarks = NULL
            WHERE id = ?
            """,
            (login_now, late_login, row["id"]),
        )

    return True, "Work started successfully."


def start_break(user_id: int, break_type: str):
    attendance = _get_today_attendance(user_id)

    if not attendance or not attendance["login_time"]:
        return False, "Start work first."

    if attendance["logout_time"]:
        return False, "Work already ended for today."

    if attendance["status"] == "On Break":
        return False, "A break is already active."

    allowed = get_break_limit(break_type)

    execute(
        """
        UPDATE attendance
        SET status = 'On Break'
        WHERE id = ?
        """,
        (attendance["id"],),
    )

    execute(
        """
        INSERT INTO breaks (
            attendance_id,
            break_type,
            break_start,
            allowed_minutes,
            status
        )
        VALUES (?, ?, ?, ?, 'Active')
        """,
        (attendance["id"], break_type, now_str(), allowed),
    )

    return True, f"{break_type} started successfully."


def end_work(user_id: int):
    attendance = _get_today_attendance(user_id)

    if not attendance or not attendance["login_time"]:
        return False, "No active work session found for today."

    if attendance["logout_time"]:
        return False, "Work already ended for today."

    if attendance["status"] == "On Break":
        from modules.breaks import end_break_by_user

        end_break_by_user(user_id)

    attendance = _get_today_attendance(user_id)
    logout_now = now_str()
    policy = get_policy()

    login_dt = parse_dt(attendance["login_time"])
    logout_dt = parse_dt(logout_now)

    total_minutes = minutes_between(login_dt, logout_dt)
    break_minutes = int(attendance["break_minutes"] or 0)
    work_minutes = max(total_minutes - break_minutes, 0)

    expected_logout = combine_date_time(today_str(), policy["logout_time"])

    early_logout = 0
    overtime_minutes = 0

    if logout_dt < expected_logout:
        if minutes_between(logout_dt, expected_logout) > int(
            policy["logout_grace_minutes"]
        ):
            early_logout = 1

    if logout_dt > expected_logout:
        overtime_minutes = minutes_between(expected_logout, logout_dt)

    execute(
        """
        UPDATE attendance
        SET logout_time = ?,
            status = 'Completed',
            early_logout = ?,
            overtime_minutes = ?,
            work_minutes = ?
        WHERE id = ?
        """,
        (logout_now, early_logout, overtime_minutes, work_minutes, attendance["id"]),
    )

    return True, "Work ended successfully."


def get_today_attendance_summary(user_id: int):
    row = _get_today_attendance(user_id)

    if not row:
        return {
            "login_time": "-",
            "logout_time": "-",
            "break_minutes": 0,
            "work_hours": "0h 0m",
            "status": "Not Started",
            "late_login": "No",
            "early_logout": "No",
            "overtime": "0m",
            "attendance_id": None,
        }

    work_minutes = int(row["work_minutes"] or 0)
    break_minutes = int(row["break_minutes"] or 0)
    status = row["status"] or "Not Started"

    if row["login_time"] and not row["logout_time"]:
        running_minutes = max(
            minutes_between(parse_dt(row["login_time"]), parse_dt(now_str()))
            - break_minutes,
            0,
        )
        work_minutes = running_minutes

    return {
        "login_time": format_dt(row["login_time"]),
        "logout_time": format_dt(row["logout_time"]),
        "break_minutes": break_minutes,
        "work_hours": f"{work_minutes // 60}h {work_minutes % 60}m",
        "status": status,
        "late_login": "Yes" if row["late_login"] else "No",
        "early_logout": "Yes" if row["early_logout"] else "No",
        "overtime": f"{int(row['overtime_minutes'] or 0)}m",
        "attendance_id": row["id"],
    }


def get_user_attendance_history(user_id: int):
    rows = fetch_all(
        """
        SELECT attendance_date, login_time, logout_time, status, break_minutes,
               late_login, early_logout, overtime_minutes, work_minutes
        FROM attendance
        WHERE user_id = ?
        ORDER BY attendance_date DESC
        """,
        (user_id,),
    )

    data = []
    for r in rows:
        work_minutes = int(r["work_minutes"] or 0)
        data.append(
            {
                "Date": r["attendance_date"],
                "Login": format_dt(r["login_time"]),
                "Logout": format_dt(r["logout_time"]),
                "Status": r["status"],
                "Break Minutes": int(r["break_minutes"] or 0),
                "Late Login": "Yes" if r["late_login"] else "No",
                "Early Logout": "Yes" if r["early_logout"] else "No",
                "Overtime Minutes": int(r["overtime_minutes"] or 0),
                "Work Hours": f"{work_minutes // 60}h {work_minutes % 60}m",
            }
        )
    return data


def get_team_attendance():
    rows = fetch_all(
        """
        SELECT u.id AS user_id,
               u.employee_id,
               u.full_name,
               u.department,
               u.role,
               a.attendance_date,
               a.login_time,
               a.logout_time,
               a.status,
               a.break_minutes,
               a.late_login,
               a.early_logout,
               a.overtime_minutes,
               a.work_minutes
        FROM attendance a
        JOIN users u ON u.id = a.user_id
        ORDER BY a.attendance_date DESC, CAST(u.employee_id AS INTEGER)
        """
    )
    return [dict(r) for r in rows]
