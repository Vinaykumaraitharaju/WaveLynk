from database import fetch_all, execute


# ---------------- ROLES ----------------

def get_roles():
    rows = fetch_all(
        """
        SELECT id, role_name, is_active
        FROM roles
        ORDER BY role_name
        """
    )
    return [dict(r) for r in rows]


def get_active_roles():
    rows = fetch_all(
        """
        SELECT role_name
        FROM roles
        WHERE is_active = 1
        ORDER BY role_name
        """
    )
    return [dict(r) for r in rows]


def add_role(role_name: str):
    execute(
        """
        INSERT INTO roles (role_name, is_active)
        VALUES (?, 1)
        """,
        (role_name.strip(),),
    )


def remove_role(role_id: int):
    execute("DELETE FROM roles WHERE id = ?", (role_id,))


# ---------------- DEPARTMENTS ----------------

def get_departments():
    rows = fetch_all(
        """
        SELECT id, department_name, is_active
        FROM departments
        ORDER BY department_name
        """
    )
    return [dict(r) for r in rows]


def get_active_departments():
    rows = fetch_all(
        """
        SELECT department_name
        FROM departments
        WHERE is_active = 1
        ORDER BY department_name
        """
    )
    return [dict(r) for r in rows]


def add_department(department_name: str):
    execute(
        """
        INSERT INTO departments (department_name, is_active)
        VALUES (?, 1)
        """,
        (department_name.strip(),),
    )


def remove_department(department_id: int):
    execute("DELETE FROM departments WHERE id = ?", (department_id,))