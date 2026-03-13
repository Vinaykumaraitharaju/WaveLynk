from database import fetch_all, execute
from utils import hash_password


def list_users():
    rows = fetch_all(
        """
        SELECT id, username, full_name, role, is_active
        FROM users
        ORDER BY id
        """
    )
    return [dict(r) for r in rows]


def create_user(username: str, full_name: str, role: str, password: str):
    execute(
        """
        INSERT INTO users (username, full_name, role, password_hash, is_active)
        VALUES (?, ?, ?, ?, 1)
        """,
        (username, full_name, role, hash_password(password)),
    )


def set_user_active(user_id: int, is_active: int):
    execute("UPDATE users SET is_active = ? WHERE id = ?", (is_active, user_id))