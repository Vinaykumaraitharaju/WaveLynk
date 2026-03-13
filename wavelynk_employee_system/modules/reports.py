import pandas as pd
from database import fetch_all


def attendance_report_df():
    rows = fetch_all(
        """
        SELECT u.employee_id, u.full_name, u.department, a.attendance_date, a.login_time, a.logout_time,
               a.status, a.break_minutes, a.late_login, a.early_logout, a.overtime_minutes, a.work_minutes
        FROM attendance a
        JOIN users u ON u.id = a.user_id
        ORDER BY a.attendance_date DESC, CAST(u.employee_id AS INTEGER)
        """
    )
    return pd.DataFrame([dict(r) for r in rows])


def leave_report_df():
    rows = fetch_all(
        """
        SELECT u.employee_id, u.full_name, u.department, lr.leave_type, lr.from_date, lr.to_date,
               lr.reason, lr.status, lr.created_at, lr.approved_by
        FROM leave_requests lr
        JOIN users u ON u.id = lr.user_id
        ORDER BY lr.id DESC
        """
    )
    return pd.DataFrame([dict(r) for r in rows])


def payroll_summary_df():
    rows = fetch_all(
        """
        SELECT u.employee_id, u.full_name, u.department,
               COUNT(a.id) AS attendance_days,
               SUM(a.work_minutes) AS total_work_minutes,
               SUM(a.overtime_minutes) AS overtime_minutes,
               SUM(a.late_login) AS late_days,
               SUM(a.early_logout) AS early_logout_days
        FROM users u
        LEFT JOIN attendance a ON a.user_id = u.id
        WHERE u.is_active = 1
        GROUP BY u.id, u.employee_id, u.full_name, u.department
        ORDER BY CAST(u.employee_id AS INTEGER)
        """
    )
    data = []
    for r in rows:
        total_work_minutes = r["total_work_minutes"] or 0
        overtime_minutes = r["overtime_minutes"] or 0
        data.append(
            {
                "Employee ID": r["employee_id"],
                "Employee": r["full_name"],
                "Department": r["department"],
                "Attendance Days": r["attendance_days"],
                "Total Work Hours": f"{total_work_minutes // 60}h {total_work_minutes % 60}m",
                "Overtime Hours": f"{overtime_minutes // 60}h {overtime_minutes % 60}m",
                "Late Days": r["late_days"] or 0,
                "Early Logout Days": r["early_logout_days"] or 0,
            }
        )
    return pd.DataFrame(data)