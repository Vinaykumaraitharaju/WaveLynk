import hashlib
import re
from datetime import datetime
import pandas as pd
from config import EXCEL_EXPORT_DIR


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def is_strong_password(password: str):
    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must include at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        errors.append("Password must include at least one lowercase letter.")
    if not re.search(r"\d", password):
        errors.append("Password must include at least one number.")
    if not re.search(r"[!@#$%^&*()_\-+=\[\]{};:,.<>?/\\|~`]", password):
        errors.append("Password must include at least one special character.")

    return len(errors) == 0, errors


def now_dt():
    return datetime.now()


def now_str():
    return now_dt().strftime("%Y-%m-%d %H:%M:%S")


def today_str():
    return now_dt().strftime("%Y-%m-%d")


def parse_dt(value: str):
    if not value:
        return None
    return datetime.fromisoformat(value)


def parse_date(value: str):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_hhmm(value: str):
    return datetime.strptime(value, "%H:%M").time()


def combine_date_time(date_str: str, hhmm: str):
    d = parse_date(date_str)
    t = parse_hhmm(hhmm)
    return datetime.combine(d, t)


def minutes_between(start_dt, end_dt):
    if not start_dt or not end_dt:
        return 0
    mins = int((end_dt - start_dt).total_seconds() // 60)
    return max(mins, 0)


def format_dt(value):
    if not value:
        return "-"
    try:
        return datetime.fromisoformat(value).strftime("%d-%m-%Y %I:%M %p")
    except Exception:
        return value


def export_dataframe_to_excel(df: pd.DataFrame, filename: str) -> str:
    EXCEL_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    file_path = EXCEL_EXPORT_DIR / filename
    df.to_excel(file_path, index=False)
    return str(file_path)