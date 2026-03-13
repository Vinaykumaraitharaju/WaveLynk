import sqlite3
from config import DB_PATH, DB_DIR, SCHEMA_FILE, SEED_FILE


def get_connection():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def execute(query, params=()):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    lastrowid = cur.lastrowid
    conn.close()
    return lastrowid


def execute_many(query, params_list):
    conn = get_connection()
    cur = conn.cursor()
    cur.executemany(query, params_list)
    conn.commit()
    conn.close()


def fetch_one(query, params=()):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, params)
    row = cur.fetchone()
    conn.close()
    return row


def fetch_all(query, params=()):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows


def table_exists(conn, table_name):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table' AND name=?
        """,
        (table_name,),
    )
    return cur.fetchone() is not None


def column_exists(conn, table_name, column_name):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cur.fetchall()]
    return column_name in columns


def safe_add_column(conn, table_name, column_def):
    column_name = column_def.split()[0]
    if not column_exists(conn, table_name, column_name):
        conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_def}")
        conn.commit()


def migrate_db(conn):
    cur = conn.cursor()

    # =========================================================
    # USERS
    # =========================================================
    if not table_exists(conn, "users"):
        cur.execute(
            """
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT UNIQUE,
                username TEXT NOT NULL UNIQUE,
                full_name TEXT,
                role TEXT,
                department TEXT,
                phone TEXT,
                email TEXT,
                joining_date TEXT,
                employment_status TEXT DEFAULT 'Active',
                manager_id INTEGER,
                manager_name TEXT,
                password_hash TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT
            )
            """
        )
        conn.commit()
    else:
        safe_add_column(conn, "users", "employee_id TEXT")
        safe_add_column(conn, "users", "full_name TEXT")
        safe_add_column(conn, "users", "role TEXT")
        safe_add_column(conn, "users", "department TEXT")
        safe_add_column(conn, "users", "phone TEXT")
        safe_add_column(conn, "users", "email TEXT")
        safe_add_column(conn, "users", "joining_date TEXT")
        safe_add_column(conn, "users", "employment_status TEXT DEFAULT 'Active'")
        safe_add_column(conn, "users", "manager_id INTEGER")
        safe_add_column(conn, "users", "manager_name TEXT")
        safe_add_column(conn, "users", "password_hash TEXT")
        safe_add_column(conn, "users", "is_active INTEGER DEFAULT 1")
        safe_add_column(conn, "users", "created_at TEXT")

    # =========================================================
    # ROLES
    # =========================================================
    if not table_exists(conn, "roles"):
        cur.execute(
            """
            CREATE TABLE roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_name TEXT NOT NULL UNIQUE,
                is_active INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        conn.commit()
    else:
        safe_add_column(conn, "roles", "is_active INTEGER DEFAULT 1")

    # =========================================================
    # DEPARTMENTS
    # =========================================================
    if not table_exists(conn, "departments"):
        cur.execute(
            """
            CREATE TABLE departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                department_name TEXT NOT NULL UNIQUE,
                is_active INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        conn.commit()
    else:
        safe_add_column(conn, "departments", "is_active INTEGER DEFAULT 1")

    # =========================================================
    # COMPANY POLICY
    # =========================================================
    if not table_exists(conn, "company_policy"):
        cur.execute(
            """
            CREATE TABLE company_policy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                login_time TEXT NOT NULL DEFAULT '09:00',
                logout_time TEXT NOT NULL DEFAULT '18:00',
                login_grace_minutes INTEGER NOT NULL DEFAULT 30,
                logout_grace_minutes INTEGER NOT NULL DEFAULT 30,
                tea_break_minutes INTEGER NOT NULL DEFAULT 10,
                lunch_break_minutes INTEGER NOT NULL DEFAULT 45,
                personal_break_minutes INTEGER NOT NULL DEFAULT 15
            )
            """
        )
        conn.commit()

    # =========================================================
    # LEAVE TYPES
    # =========================================================
    if not table_exists(conn, "leave_types"):
        cur.execute(
            """
            CREATE TABLE leave_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                leave_name TEXT NOT NULL UNIQUE,
                yearly_quota INTEGER NOT NULL DEFAULT 0,
                is_active INTEGER NOT NULL DEFAULT 1
            )
            """
        )
        conn.commit()

    # =========================================================
    # ATTENDANCE
    # =========================================================
    if not table_exists(conn, "attendance"):
        cur.execute(
            """
            CREATE TABLE attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                attendance_date TEXT NOT NULL,
                login_time TEXT,
                logout_time TEXT,
                status TEXT NOT NULL DEFAULT 'Not Started',
                break_minutes INTEGER NOT NULL DEFAULT 0,
                late_login INTEGER NOT NULL DEFAULT 0,
                early_logout INTEGER NOT NULL DEFAULT 0,
                overtime_minutes INTEGER NOT NULL DEFAULT 0,
                work_minutes INTEGER NOT NULL DEFAULT 0,
                remarks TEXT,
                UNIQUE(user_id, attendance_date)
            )
            """
        )
        conn.commit()
    else:
        safe_add_column(conn, "attendance", "late_login INTEGER DEFAULT 0")
        safe_add_column(conn, "attendance", "early_logout INTEGER DEFAULT 0")
        safe_add_column(conn, "attendance", "overtime_minutes INTEGER DEFAULT 0")
        safe_add_column(conn, "attendance", "work_minutes INTEGER DEFAULT 0")
        safe_add_column(conn, "attendance", "remarks TEXT")

    # =========================================================
    # BREAKS
    # =========================================================
    if not table_exists(conn, "breaks"):
        cur.execute(
            """
            CREATE TABLE breaks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attendance_id INTEGER NOT NULL,
                break_type TEXT NOT NULL,
                break_start TEXT NOT NULL,
                break_end TEXT,
                allowed_minutes INTEGER NOT NULL DEFAULT 0,
                actual_minutes INTEGER NOT NULL DEFAULT 0,
                exceeded_minutes INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'Active'
            )
            """
        )
        conn.commit()
    else:
        safe_add_column(conn, "breaks", "break_type TEXT DEFAULT 'General Break'")
        safe_add_column(conn, "breaks", "allowed_minutes INTEGER DEFAULT 0")
        safe_add_column(conn, "breaks", "actual_minutes INTEGER DEFAULT 0")
        safe_add_column(conn, "breaks", "exceeded_minutes INTEGER DEFAULT 0")
        safe_add_column(conn, "breaks", "status TEXT DEFAULT 'Active'")

    # =========================================================
    # LEAVE REQUESTS
    # =========================================================
    if not table_exists(conn, "leave_requests"):
        cur.execute(
            """
            CREATE TABLE leave_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                leave_type TEXT NOT NULL,
                from_date TEXT NOT NULL,
                to_date TEXT NOT NULL,
                reason TEXT,
                status TEXT NOT NULL DEFAULT 'Pending',
                created_at TEXT NOT NULL,
                approved_by TEXT
            )
            """
        )
        conn.commit()
    else:
        safe_add_column(conn, "leave_requests", "approved_by TEXT")

    # =========================================================
    # LEAVE BALANCES
    # =========================================================
    if not table_exists(conn, "leave_balances"):
        cur.execute(
            """
            CREATE TABLE leave_balances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                leave_type TEXT NOT NULL,
                available INTEGER NOT NULL DEFAULT 0,
                used INTEGER NOT NULL DEFAULT 0,
                UNIQUE(user_id, leave_type)
            )
            """
        )
        conn.commit()

    # =========================================================
    # HOLIDAYS
    # =========================================================
    if not table_exists(conn, "holidays"):
        cur.execute(
            """
            CREATE TABLE holidays (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                holiday_name TEXT NOT NULL,
                holiday_date TEXT NOT NULL,
                country_code TEXT NOT NULL DEFAULT 'MANUAL',
                optional_flag INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.commit()
    else:
        safe_add_column(conn, "holidays", "country_code TEXT DEFAULT 'MANUAL'")
        safe_add_column(conn, "holidays", "optional_flag INTEGER DEFAULT 0")

    # =========================================================
    # PASSWORD RESET OTPS
    # =========================================================
    if not table_exists(conn, "password_reset_otps"):
        cur.execute(
            """
            CREATE TABLE password_reset_otps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                otp_code TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                is_used INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()

    # =========================================================
    # AUDIT LOGS
    # =========================================================
    if not table_exists(conn, "audit_logs"):
        cur.execute(
            """
            CREATE TABLE audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                actor_name TEXT,
                target_name TEXT,
                details TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()

    # =========================================================
    # DEFAULT MASTER DATA
    # =========================================================
    roles_count = cur.execute("SELECT COUNT(*) FROM roles").fetchone()[0]
    if roles_count == 0:
        cur.executemany(
            """
            INSERT INTO roles (role_name, is_active)
            VALUES (?, 1)
            """,
            [
                ("Admin",),
                ("HR",),
                ("Manager",),
                ("Team Lead",),
                ("HOD",),
                ("Employee",),
            ],
        )
        conn.commit()

    departments_count = cur.execute("SELECT COUNT(*) FROM departments").fetchone()[0]
    if departments_count == 0:
        cur.executemany(
            """
            INSERT INTO departments (department_name, is_active)
            VALUES (?, 1)
            """,
            [
                ("HR",),
                ("Operations",),
                ("IT",),
                ("Finance",),
                ("Admin",),
            ],
        )
        conn.commit()

    # =========================================================
    # DEFAULT POLICY
    # =========================================================
    policy_count = cur.execute("SELECT COUNT(*) FROM company_policy").fetchone()[0]
    if policy_count == 0:
        cur.execute(
            """
            INSERT INTO company_policy (
                login_time, logout_time, login_grace_minutes, logout_grace_minutes,
                tea_break_minutes, lunch_break_minutes, personal_break_minutes
            ) VALUES ('09:00', '18:00', 30, 30, 10, 45, 15)
            """
        )
        conn.commit()

    # =========================================================
    # DEFAULT LEAVE TYPES
    # =========================================================
    leave_type_count = cur.execute("SELECT COUNT(*) FROM leave_types").fetchone()[0]
    if leave_type_count == 0:
        cur.executemany(
            """
            INSERT INTO leave_types (leave_name, yearly_quota, is_active)
            VALUES (?, ?, 1)
            """,
            [
                ("Casual Leave", 8),
                ("Sick Leave", 8),
                ("Earned Leave", 12),
                ("Maternity Leave", 90),
                ("Paternity Leave", 15),
                ("Bereavement Leave", 5),
                ("Comp Off", 5),
                ("Loss Of Pay", 0),
                ("Work From Home", 24),
            ],
        )
        conn.commit()

    # =========================================================
    # BACKFILL manager_id FROM manager_name
    # =========================================================
    cur.execute(
        """
        UPDATE users
        SET manager_id = (
            SELECT m.id
            FROM users m
            WHERE m.full_name = users.manager_name
            LIMIT 1
        )
        WHERE manager_id IS NULL
          AND manager_name IS NOT NULL
          AND TRIM(manager_name) != ''
        """
    )
    conn.commit()


def init_db():
    conn = get_connection()

    if not table_exists(conn, "users"):
        conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
        conn.commit()
        conn.executescript(SEED_FILE.read_text(encoding="utf-8"))
        conn.commit()

    migrate_db(conn)
    conn.close()
