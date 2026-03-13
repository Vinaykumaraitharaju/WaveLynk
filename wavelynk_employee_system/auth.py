import random
from datetime import timedelta

import streamlit as st

from database import fetch_one, execute
from utils import hash_password, is_strong_password, now_dt, now_str
from modules.notifications import send_password_reset_otp_email


def authenticate_user(username: str, password: str):
    row = fetch_one(
        """
        SELECT id, employee_id, username, full_name, role, department, phone, email,
               joining_date, employment_status, manager_id, manager_name, password_hash, is_active
        FROM users
        WHERE LOWER(TRIM(username)) = LOWER(TRIM(?))
        """,
        (username,),
    )
    if not row:
        return None
    if not row["is_active"]:
        return None
    if row["password_hash"] != hash_password(password):
        return None

    return {
        "id": row["id"],
        "employee_id": row["employee_id"],
        "username": row["username"],
        "full_name": row["full_name"],
        "role": row["role"],
        "department": row["department"],
        "phone": row["phone"],
        "email": row["email"],
        "joining_date": row["joining_date"],
        "employment_status": row["employment_status"],
        "manager_name": row["manager_name"],
        "manager_id": row["manager_id"],
    }


def verify_current_password(user_id: int, current_password: str) -> bool:
    row = fetch_one(
        """
        SELECT password_hash
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    )
    if not row:
        return False
    return row["password_hash"] == hash_password(current_password)


def change_user_password(
    user_id: int, current_password: str, new_password: str, confirm_password: str
):
    if not verify_current_password(user_id, current_password):
        return False, "Current password is incorrect."

    if new_password != confirm_password:
        return False, "New password and confirm password do not match."

    is_valid, errors = is_strong_password(new_password)
    if not is_valid:
        return False, " ".join(errors)

    if current_password == new_password:
        return False, "New password must be different from current password."

    execute(
        """
        UPDATE users
        SET password_hash = ?
        WHERE id = ?
        """,
        (hash_password(new_password), user_id),
    )
    return True, "Password changed successfully."


def _find_user_by_username_or_email(identifier: str):
    identifier = identifier.strip()

    return fetch_one(
        """
        SELECT id, username, full_name, email, is_active
        FROM users
        WHERE LOWER(TRIM(username)) = LOWER(TRIM(?))
           OR LOWER(TRIM(email)) = LOWER(TRIM(?))
        LIMIT 1
        """,
        (identifier, identifier),
    )


def create_password_reset_otp(identifier: str):
    user = _find_user_by_username_or_email(identifier)
    if not user:
        return False, "No active user found with that username or email."

    if not user["is_active"]:
        return False, "This user account is inactive."

    if not user["email"] or "@" not in str(user["email"]):
        return False, "No valid registered email found for this account."

    otp_code = f"{random.randint(100000, 999999)}"
    expires_at = (now_dt() + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")

    execute(
        """
        UPDATE password_reset_otps
        SET is_used = 1
        WHERE user_id = ? AND is_used = 0
        """,
        (user["id"],),
    )

    execute(
        """
        INSERT INTO password_reset_otps (user_id, otp_code, expires_at, is_used, created_at)
        VALUES (?, ?, ?, 0, ?)
        """,
        (user["id"], otp_code, expires_at, now_str()),
    )

    ok, msg = send_password_reset_otp_email(
        user["email"],
        user["full_name"] or user["username"],
        otp_code,
    )

    if not ok:
        return False, f"Could not send OTP email. {msg}"

    return True, "Password reset OTP sent to your registered email."


def reset_password_with_otp(
    identifier: str, otp_code: str, new_password: str, confirm_password: str
):
    user = _find_user_by_username_or_email(identifier)
    if not user:
        return False, "No active user found with that username or email."

    if new_password != confirm_password:
        return False, "New password and confirm password do not match."

    is_valid, errors = is_strong_password(new_password)
    if not is_valid:
        return False, " ".join(errors)

    row = fetch_one(
        """
        SELECT id, expires_at, is_used
        FROM password_reset_otps
        WHERE user_id = ? AND otp_code = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (user["id"], otp_code.strip()),
    )

    if not row:
        return False, "Invalid OTP."

    if row["is_used"]:
        return False, "This OTP has already been used."

    try:
        expires_at_dt = now_dt().fromisoformat(row["expires_at"])
    except Exception:
        return False, "OTP expiry format is invalid."

    if now_dt() > expires_at_dt:
        return False, "OTP has expired."

    execute(
        """
        UPDATE users
        SET password_hash = ?
        WHERE id = ?
        """,
        (hash_password(new_password), user["id"]),
    )

    execute(
        """
        UPDATE password_reset_otps
        SET is_used = 1
        WHERE id = ?
        """,
        (row["id"],),
    )

    return True, "Password reset successfully."


def logout_user():
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.page = "Dashboard"
