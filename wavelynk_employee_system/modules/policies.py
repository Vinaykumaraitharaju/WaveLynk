from database import fetch_one, execute


def get_policy():
    row = fetch_one("SELECT * FROM company_policy ORDER BY id LIMIT 1")
    return dict(row) if row else None


def update_policy(
    login_time,
    logout_time,
    login_grace_minutes,
    logout_grace_minutes,
    tea_break_minutes,
    lunch_break_minutes,
    personal_break_minutes,
):
    row = fetch_one("SELECT id FROM company_policy ORDER BY id LIMIT 1")
    if row:
        execute(
            """
            UPDATE company_policy
            SET login_time = ?, logout_time = ?, login_grace_minutes = ?,
                logout_grace_minutes = ?, tea_break_minutes = ?,
                lunch_break_minutes = ?, personal_break_minutes = ?
            WHERE id = ?
            """,
            (
                login_time,
                logout_time,
                login_grace_minutes,
                logout_grace_minutes,
                tea_break_minutes,
                lunch_break_minutes,
                personal_break_minutes,
                row["id"],
            ),
        )
    else:
        execute(
            """
            INSERT INTO company_policy (
                login_time, logout_time, login_grace_minutes, logout_grace_minutes,
                tea_break_minutes, lunch_break_minutes, personal_break_minutes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                login_time,
                logout_time,
                login_grace_minutes,
                logout_grace_minutes,
                tea_break_minutes,
                lunch_break_minutes,
                personal_break_minutes,
            ),
        )