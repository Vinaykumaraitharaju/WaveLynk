CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id TEXT NOT NULL UNIQUE,
    username TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL,
    department TEXT,
    phone TEXT,
    email TEXT,
    joining_date TEXT,
    employment_status TEXT NOT NULL DEFAULT 'Active',
    manager_id INTEGER,
    manager_name TEXT,
    password_hash TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS company_policy (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    login_time TEXT NOT NULL DEFAULT '09:00',
    logout_time TEXT NOT NULL DEFAULT '18:00',
    login_grace_minutes INTEGER NOT NULL DEFAULT 30,
    logout_grace_minutes INTEGER NOT NULL DEFAULT 30,
    tea_break_minutes INTEGER NOT NULL DEFAULT 10,
    lunch_break_minutes INTEGER NOT NULL DEFAULT 45,
    personal_break_minutes INTEGER NOT NULL DEFAULT 15
);

CREATE TABLE IF NOT EXISTS leave_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    leave_name TEXT NOT NULL UNIQUE,
    yearly_quota INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS attendance (
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
    FOREIGN KEY(user_id) REFERENCES users(id),
    UNIQUE(user_id, attendance_date)
);

CREATE TABLE IF NOT EXISTS breaks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attendance_id INTEGER NOT NULL,
    break_type TEXT NOT NULL,
    break_start TEXT NOT NULL,
    break_end TEXT,
    allowed_minutes INTEGER NOT NULL DEFAULT 0,
    actual_minutes INTEGER NOT NULL DEFAULT 0,
    exceeded_minutes INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'Active',
    FOREIGN KEY(attendance_id) REFERENCES attendance(id)
);

CREATE TABLE IF NOT EXISTS leave_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    leave_type TEXT NOT NULL,
    from_date TEXT NOT NULL,
    to_date TEXT NOT NULL,
    reason TEXT,
    status TEXT NOT NULL DEFAULT 'Pending',
    created_at TEXT NOT NULL,
    approved_by TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS leave_balances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    leave_type TEXT NOT NULL,
    available INTEGER NOT NULL DEFAULT 0,
    used INTEGER NOT NULL DEFAULT 0,
    UNIQUE(user_id, leave_type),
    FOREIGN KEY(user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS holidays (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    holiday_name TEXT NOT NULL,
    holiday_date TEXT NOT NULL,
    country_code TEXT NOT NULL DEFAULT 'MANUAL',
    UNIQUE(holiday_name, holiday_date, country_code)
);