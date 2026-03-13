import re

from database import fetch_all, fetch_one, execute
from utils import hash_password, now_str


EMPLOYEE_ID_START = 200000


def generate_employee_id():
    row = fetch_one(
        """
        SELECT employee_id
        FROM users
        WHERE employee_id IS NOT NULL
          AND TRIM(employee_id) != ''
        ORDER BY CAST(employee_id AS INTEGER) DESC
        LIMIT 1
        """
    )

    if not row or not row["employee_id"]:
        return str(EMPLOYEE_ID_START)

    try:
        current_max = int(str(row["employee_id"]).strip())
        if current_max < EMPLOYEE_ID_START:
            return str(EMPLOYEE_ID_START)
        return str(current_max + 1)
    except Exception:
        return str(EMPLOYEE_ID_START)


def is_valid_email(email: str) -> bool:
    if not email:
        return False
    email = email.strip().lower()
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return re.match(pattern, email) is not None


def normalize_phone(phone: str) -> str:
    if phone is None:
        return ""
    phone = str(phone).strip().replace(" ", "").replace("-", "")
    return phone


def is_valid_phone(phone: str) -> bool:
    phone = normalize_phone(phone)
    pattern = r"^\+[1-9]\d{7,14}$"
    return re.match(pattern, phone) is not None


def email_exists(email: str, exclude_user_id=None) -> bool:
    if not email:
        return False

    email = email.strip().lower()

    if exclude_user_id is None:
        row = fetch_one(
            """
            SELECT id
            FROM users
            WHERE LOWER(TRIM(COALESCE(email, ''))) = ?
            LIMIT 1
            """,
            (email,),
        )
    else:
        row = fetch_one(
            """
            SELECT id
            FROM users
            WHERE LOWER(TRIM(COALESCE(email, ''))) = ?
              AND id != ?
            LIMIT 1
            """,
            (email, exclude_user_id),
        )

    return row is not None


def phone_exists(phone: str, exclude_user_id=None) -> bool:
    clean_phone = normalize_phone(phone)
    if not clean_phone:
        return False

    rows = fetch_all(
        """
        SELECT id, phone
        FROM users
        WHERE phone IS NOT NULL
          AND TRIM(phone) != ''
        """
    )

    for row in rows:
        if exclude_user_id is not None and row["id"] == exclude_user_id:
            continue
        if normalize_phone(row["phone"]) == clean_phone:
            return True

    return False


def get_all_employees():
    rows = fetch_all(
        """
        SELECT id, employee_id, username, full_name, role, department, phone, email,
               joining_date, employment_status, manager_id, manager_name, is_active
        FROM users
        ORDER BY CAST(employee_id AS INTEGER)
        """
    )
    return [dict(r) for r in rows]


def get_employee_by_id(user_id: int):
    row = fetch_one(
        """
        SELECT id, employee_id, username, full_name, role, department, phone, email,
               joining_date, employment_status, manager_id, manager_name, is_active
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    )
    return dict(row) if row else None


def create_employee(
    username,
    full_name,
    role,
    department,
    phone,
    email,
    joining_date,
    manager_id,
    password,
):
    employee_id = generate_employee_id()
    username = employee_id

    clean_full_name = full_name.strip()
    clean_role = role.strip() if role else "Employee"
    clean_department = department.strip() if department else ""
    clean_email = email.strip().lower() if email else ""
    clean_phone = normalize_phone(phone)

    if not clean_full_name:
        raise ValueError("Full Name is required.")

    if not clean_email:
        raise ValueError("Email is required.")

    if not is_valid_email(clean_email):
        raise ValueError("Enter a valid email address.")

    if email_exists(clean_email):
        raise ValueError("This email is already registered.")

    if not clean_phone:
        raise ValueError("Phone number is required.")

    if not is_valid_phone(clean_phone):
        raise ValueError("Enter phone number with country code, like +919876543210.")

    if phone_exists(clean_phone):
        raise ValueError("This phone number is already registered.")

    manager_name = None
    manager_id_value = None

    if manager_id:
        manager_row = fetch_one(
            """
            SELECT id, full_name
            FROM users
            WHERE id = ?
            """,
            (manager_id,),
        )
        if manager_row:
            manager_id_value = manager_row["id"]
            manager_name = manager_row["full_name"]

    execute(
        """
        INSERT INTO users (
            employee_id, username, full_name, role, department, phone, email,
            joining_date, employment_status, manager_id, manager_name, password_hash, is_active, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Active', ?, ?, ?, 1, ?)
        """,
        (
            employee_id,
            username,
            clean_full_name,
            clean_role,
            clean_department,
            clean_phone,
            clean_email,
            joining_date,
            manager_id_value,
            manager_name,
            hash_password(password),
            now_str(),
        ),
    )

    return employee_id


def update_employee_status(user_id: int, employment_status: str, is_active: int):
    execute(
        """
        UPDATE users
        SET employment_status = ?, is_active = ?
        WHERE id = ?
        """,
        (employment_status, is_active, user_id),
    )


def reset_employee_password(user_id: int, new_password: str):
    execute(
        """
        UPDATE users
        SET password_hash = ?
        WHERE id = ?
        """,
        (hash_password(new_password), user_id),
    )


def update_employee_contact(user_id: int, phone: str, email: str):
    clean_email = email.strip().lower() if email else ""
    clean_phone = normalize_phone(phone)

    if not clean_email:
        raise ValueError("Email is required.")

    if not is_valid_email(clean_email):
        raise ValueError("Enter a valid email address.")

    if email_exists(clean_email, exclude_user_id=user_id):
        raise ValueError("This email is already registered.")

    if not clean_phone:
        raise ValueError("Phone number is required.")

    if not is_valid_phone(clean_phone):
        raise ValueError("Enter phone number with country code, like +919876543210.")

    if phone_exists(clean_phone, exclude_user_id=user_id):
        raise ValueError("This phone number is already registered.")

    execute(
        """
        UPDATE users
        SET phone = ?, email = ?
        WHERE id = ?
        """,
        (clean_phone, clean_email, user_id),
    )


def update_employee_role(user_id: int, role: str):
    clean_role = role.strip() if role else ""
    if not clean_role:
        raise ValueError("Role is required.")

    execute(
        """
        UPDATE users
        SET role = ?
        WHERE id = ?
        """,
        (clean_role, user_id),
    )


def update_employee_department(user_id: int, department: str):
    clean_department = department.strip() if department else ""
    if not clean_department:
        raise ValueError("Department is required.")

    execute(
        """
        UPDATE users
        SET department = ?
        WHERE id = ?
        """,
        (clean_department, user_id),
    )


def update_employee_role_department(user_id: int, role: str, department: str):
    clean_role = role.strip() if role else ""
    clean_department = department.strip() if department else ""

    if not clean_role:
        raise ValueError("Role is required.")
    if not clean_department:
        raise ValueError("Department is required.")

    execute(
        """
        UPDATE users
        SET role = ?, department = ?
        WHERE id = ?
        """,
        (clean_role, clean_department, user_id),
    )


def get_direct_team_members(manager_user_id: int):
    manager_row = fetch_one(
        """
        SELECT id, full_name
        FROM users
        WHERE id = ?
        """,
        (manager_user_id,),
    )

    if not manager_row:
        return []

    rows = fetch_all(
        """
        SELECT id, employee_id, username, full_name, role, department, phone, email,
               joining_date, employment_status, manager_id, manager_name, is_active
        FROM users
        WHERE is_active = 1
          AND (
                manager_id = ?
                OR manager_name = ?
          )
        ORDER BY full_name
        """,
        (manager_user_id, manager_row["full_name"]),
    )
    return [dict(r) for r in rows]


def get_all_subordinates(manager_user_id: int):
    visited = set()
    result = []

    def collect(parent_id: int):
        children = get_direct_team_members(parent_id)
        for child in children:
            child_id = child["id"]
            if child_id in visited:
                continue
            visited.add(child_id)
            result.append(child)
            collect(child_id)

    collect(manager_user_id)
    return result


def get_subordinate_user_ids(manager_user_id: int):
    return [row["id"] for row in get_all_subordinates(manager_user_id)]


def get_team_members_by_manager(manager_value):
    try:
        manager_id = int(manager_value)
        return get_direct_team_members(manager_id)
    except Exception:
        pass

    rows = fetch_all(
        """
        SELECT id, employee_id, username, full_name, role, department, phone, email,
               joining_date, employment_status, manager_id, manager_name, is_active
        FROM users
        WHERE manager_name = ?
        ORDER BY full_name
        """,
        (str(manager_value).strip(),),
    )
    return [dict(r) for r in rows]


def reassign_team_members(old_manager_id: int, new_manager_id):
    old_manager_row = fetch_one(
        """
        SELECT id, full_name
        FROM users
        WHERE id = ?
        """,
        (old_manager_id,),
    )

    old_manager_name = old_manager_row["full_name"] if old_manager_row else None

    new_manager_name = None
    new_manager_id_value = None

    if new_manager_id:
        new_manager_row = fetch_one(
            """
            SELECT id, full_name
            FROM users
            WHERE id = ?
            """,
            (new_manager_id,),
        )
        if new_manager_row:
            new_manager_id_value = new_manager_row["id"]
            new_manager_name = new_manager_row["full_name"]

    if old_manager_row:
        execute(
            """
            UPDATE users
            SET manager_id = ?, manager_name = ?
            WHERE manager_id = ? OR manager_name = ?
            """,
            (new_manager_id_value, new_manager_name, old_manager_id, old_manager_name),
        )


def get_managers():
    rows = fetch_all(
        """
        SELECT id, employee_id, full_name, role
        FROM users
        WHERE role IN ('Manager', 'Team Lead', 'HOD')
          AND is_active = 1
        ORDER BY full_name
        """
    )
    return [dict(r) for r in rows]


def update_employee_manager(user_id: int, manager_id):
    manager_name = None
    manager_id_value = None

    if manager_id:
        manager_row = fetch_one(
            """
            SELECT id, full_name
            FROM users
            WHERE id = ?
            """,
            (manager_id,),
        )
        if manager_row:
            manager_id_value = manager_row["id"]
            manager_name = manager_row["full_name"]

    execute(
        """
        UPDATE users
        SET manager_id = ?, manager_name = ?
        WHERE id = ?
        """,
        (manager_id_value, manager_name, user_id),
    )
