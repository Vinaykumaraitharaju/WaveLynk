from database import fetch_all, fetch_one, execute
from utils import today_str
import holidays


def list_holidays():
    rows = fetch_all(
        """
        SELECT id, holiday_name, holiday_date, country_code, optional_flag
        FROM holidays
        ORDER BY holiday_date, country_code, holiday_name
        """
    )
    return [dict(r) for r in rows]


def add_holiday(name: str, holiday_date: str, country_code: str = "MANUAL", optional_flag: int = 0):
    existing = fetch_one(
        """
        SELECT id
        FROM holidays
        WHERE holiday_name = ? AND holiday_date = ? AND country_code = ?
        """,
        (name, holiday_date, country_code),
    )
    if existing:
        return False

    execute(
        """
        INSERT INTO holidays (holiday_name, holiday_date, country_code, optional_flag)
        VALUES (?, ?, ?, ?)
        """,
        (name, holiday_date, country_code, optional_flag),
    )
    return True


def delete_holiday(holiday_id: int):
    execute("DELETE FROM holidays WHERE id = ?", (holiday_id,))


def update_holiday_optional_flag(holiday_id: int, optional_flag: int):
    execute(
        "UPDATE holidays SET optional_flag = ? WHERE id = ?",
        (optional_flag, holiday_id),
    )


def import_country_holidays(country_code: str, year: int):
    country_code = country_code.upper().strip()
    holiday_map = holidays.country_holidays(country_code, years=[year])

    inserted = 0
    skipped = 0

    for h_date, h_name in holiday_map.items():
        existing = fetch_one(
            """
            SELECT id
            FROM holidays
            WHERE holiday_name = ? AND holiday_date = ? AND country_code = ?
            """,
            (str(h_name), str(h_date), country_code),
        )
        if existing:
            skipped += 1
            continue

        execute(
            """
            INSERT INTO holidays (holiday_name, holiday_date, country_code, optional_flag)
            VALUES (?, ?, ?, 0)
            """,
            (str(h_name), str(h_date), country_code),
        )
        inserted += 1

    return {"inserted": inserted, "skipped": skipped}


def clear_country_holidays(country_code: str, year: int):
    execute(
        """
        DELETE FROM holidays
        WHERE country_code = ?
          AND substr(holiday_date, 1, 4) = ?
        """,
        (country_code.upper().strip(), str(year)),
    )


def is_today_holiday():
    row = fetch_one(
        """
        SELECT holiday_name, country_code, optional_flag
        FROM holidays
        WHERE holiday_date = ?
        LIMIT 1
        """,
        (today_str(),),
    )
    return dict(row) if row else None