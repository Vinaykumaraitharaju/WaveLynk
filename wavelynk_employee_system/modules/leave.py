from modules.email_service import send_leave_submitted_email, send_leave_status_email
from database import execute, fetch_all, fetch_one
from utils import now_str


def get_leave_types():
    rows = fetch_all(
        """
        SELECT id, leave_name, yearly_quota, is_active
        FROM leave_types
        ORDER BY leave_name
        """
    )
    return [dict(r) for r in rows]


def get_active_leave_types():
    rows = fetch_all(
        """
        SELECT leave_name, yearly_quota
        FROM leave_types
        WHERE is_active = 1
        ORDER BY leave_name
        """
    )
    return [dict(r) for r in rows]


def add_leave_type(leave_name: str, yearly_quota: int):
    execute(
        """
        INSERT INTO leave_types (leave_name, yearly_quota, is_active)
        VALUES (?, ?, 1)
        """,
        (leave_name.strip(), yearly_quota),
    )


def remove_leave_type(leave_id: int):
    execute("DELETE FROM leave_types WHERE id = ?", (leave_id,))


def apply_leave(
    user_id: int, leave_type: str, from_date: str, to_date: str, reason: str
):
    leave_id = execute(
        """
        INSERT INTO leave_requests (user_id, leave_type, from_date, to_date, reason, status, created_at)
        VALUES (?, ?, ?, ?, ?, 'Pending', ?)
        """,
        (user_id, leave_type, from_date, to_date, reason, now_str()),
    )

    user_row = fetch_one(
        """
        SELECT employee_id, full_name, manager_id, manager_name
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    )

    manager_email = None

    if user_row and user_row["manager_id"]:
        manager_row = fetch_one(
            """
            SELECT email
            FROM users
            WHERE id = ?
            LIMIT 1
            """,
            (user_row["manager_id"],),
        )
        if manager_row and manager_row["email"]:
            manager_email = manager_row["email"]

    if not manager_email and user_row and user_row["manager_name"]:
        manager_row = fetch_one(
            """
            SELECT email
            FROM users
            WHERE full_name = ?
            LIMIT 1
            """,
            (user_row["manager_name"],),
        )
        if manager_row and manager_row["email"]:
            manager_email = manager_row["email"]

    if manager_email:
        ok, msg = send_leave_submitted_email(
            manager_email,
            user_row["full_name"],
            user_row["employee_id"],
            leave_type,
            from_date,
            to_date,
            reason,
            leave_id,
        )
        print("Leave submit email:", ok, msg)
    else:
        print("Leave submit email skipped: manager email not found")


def get_user_leave_requests(user_id: int):
    rows = fetch_all(
        """
        SELECT id, leave_type, from_date, to_date, reason, status, created_at, approved_by
        FROM leave_requests
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,),
    )
    return [dict(r) for r in rows]


def get_leave_requests_for_manager(manager_user_id: int):
    rows = fetch_all(
        """
        SELECT lr.id, u.employee_id, u.full_name, lr.leave_type, lr.from_date, lr.to_date,
               lr.reason, lr.status, lr.created_at, lr.approved_by
        FROM leave_requests lr
        JOIN users u ON u.id = lr.user_id
        WHERE u.manager_id = ?
           OR u.manager_name = (
                SELECT full_name
                FROM users
                WHERE id = ?
                LIMIT 1
           )
        ORDER BY lr.id DESC
        """,
        (manager_user_id, manager_user_id),
    )
    return [dict(r) for r in rows]


def ensure_user_leave_balances(user_id: int):
    active_leave_types = get_active_leave_types()

    for leave in active_leave_types:
        existing = fetch_one(
            """
            SELECT id
            FROM leave_balances
            WHERE user_id = ? AND leave_type = ?
            """,
            (user_id, leave["leave_name"]),
        )

        if not existing:
            execute(
                """
                INSERT INTO leave_balances (user_id, leave_type, available, used)
                VALUES (?, ?, ?, 0)
                """,
                (user_id, leave["leave_name"], leave["yearly_quota"]),
            )


def get_user_leave_balances(user_id: int):
    ensure_user_leave_balances(user_id)

    rows = fetch_all(
        """
        SELECT leave_type, available, used
        FROM leave_balances
        WHERE user_id = ?
        ORDER BY leave_type
        """,
        (user_id,),
    )
    return [dict(r) for r in rows]


def get_all_leave_requests():
    rows = fetch_all(
        """
        SELECT lr.id, u.employee_id, u.full_name, lr.leave_type, lr.from_date, lr.to_date,
               lr.reason, lr.status, lr.created_at, lr.approved_by
        FROM leave_requests lr
        JOIN users u ON u.id = lr.user_id
        ORDER BY lr.id DESC
        """
    )
    return [dict(r) for r in rows]


def update_leave_status(leave_id: int, status: str, approved_by: str):
    req = fetch_one(
        """
        SELECT lr.user_id, lr.leave_type, lr.from_date, lr.to_date,
               u.full_name, u.email
        FROM leave_requests lr
        JOIN users u ON u.id = lr.user_id
        WHERE lr.id = ?
        """,
        (leave_id,),
    )

    if not req:
        return

    execute(
        """
        UPDATE leave_requests
        SET status = ?, approved_by = ?
        WHERE id = ?
        """,
        (status, approved_by, leave_id),
    )

    if status == "Approved":
        ensure_user_leave_balances(req["user_id"])

        balance = fetch_one(
            """
            SELECT id
            FROM leave_balances
            WHERE user_id = ? AND leave_type = ?
            """,
            (req["user_id"], req["leave_type"]),
        )

        if balance:
            execute(
                """
                UPDATE leave_balances
                SET available = CASE WHEN available > 0 THEN available - 1 ELSE 0 END,
                    used = used + 1
                WHERE user_id = ? AND leave_type = ?
                """,
                (req["user_id"], req["leave_type"]),
            )

    if req["email"]:
        ok, msg = send_leave_status_email(
            req["email"],
            req["full_name"],
            req["leave_type"],
            req["from_date"],
            req["to_date"],
            status,
            approved_by,
            leave_id,
        )
        print("Leave status email:", ok, msg)
    else:
        print("Leave status email skipped: employee email not found")
