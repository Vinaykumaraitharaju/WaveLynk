from database import fetch_all
from utils import today_str


def team_summary():
    rows = fetch_all(
        """
        SELECT u.role, COUNT(*) AS total_users
        FROM users u
        WHERE u.is_active = 1
        GROUP BY u.role
        ORDER BY u.role
        """
    )
    return [dict(r) for r in rows]


def today_team_attendance():
    rows = fetch_all(
        """
        SELECT u.full_name AS Employee, u.role AS Role,
               a.login_time AS Login, a.logout_time AS Logout,
               a.status AS Status, a.break_minutes AS BreakMinutes
        FROM users u
        LEFT JOIN attendance a
          ON a.user_id = u.id
         AND a.attendance_date = ?
        WHERE u.is_active = 1
        ORDER BY u.full_name
        """,
        (today_str(),),
    )
    return [dict(r) for r in rows]