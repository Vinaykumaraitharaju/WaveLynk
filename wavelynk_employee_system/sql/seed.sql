INSERT INTO company_policy (
    login_time, logout_time, login_grace_minutes, logout_grace_minutes,
    tea_break_minutes, lunch_break_minutes, personal_break_minutes
) VALUES (
    '09:00', '18:00', 30, 30, 10, 45, 15
);

INSERT INTO users (
    employee_id, username, full_name, role, department, phone, email,
    joining_date, employment_status, manager_name, password_hash, is_active, created_at
) VALUES
('2286405', 'admin', 'Admin User', 'Admin', 'HR', '9999999991', 'admin@wavelynk.com', '2026-01-01', 'Active', '', '240be518fabd2724ddb6f04eebf2e877803b1208b0015c9937ce76f4d6f4a5e0', 1, '2026-01-01 09:00:00'),
('2286406', 'employee', 'Employee User', 'Employee', 'Operations', '9999999992', 'employee@wavelynk.com', '2026-01-10', 'Active', 'Manager User', 'f08bd2b638fd4811dfc7d649571ddf3155d4f80987bc15a4194dd14906225672', 1, '2026-01-10 09:00:00'),
('2286407', 'manager', 'Manager User', 'Manager', 'Operations', '9999999993', 'manager@wavelynk.com', '2026-01-05', 'Active', '', '86648579612ddcd47edc7898d82fd7df07da12c1798db842ec5373f89c53f7ba', 1, '2026-01-05 09:00:00');

INSERT INTO leave_types (leave_name, yearly_quota, is_active) VALUES
('Casual Leave', 8, 1),
('Sick Leave', 8, 1),
('Earned Leave', 12, 1),
('Maternity Leave', 90, 1),
('Paternity Leave', 15, 1),
('Bereavement Leave', 5, 1),
('Comp Off', 5, 1),
('Loss Of Pay', 0, 1),
('Work From Home', 24, 1);

INSERT INTO leave_balances (user_id, leave_type, available, used) VALUES
(1, 'Casual Leave', 8, 0),
(1, 'Sick Leave', 8, 0),
(1, 'Earned Leave', 12, 0),
(1, 'Work From Home', 24, 0),

(2, 'Casual Leave', 8, 2),
(2, 'Sick Leave', 8, 1),
(2, 'Earned Leave', 12, 0),
(2, 'Comp Off', 2, 0),
(2, 'Work From Home', 24, 3),

(3, 'Casual Leave', 8, 1),
(3, 'Sick Leave', 8, 0),
(3, 'Earned Leave', 12, 1),
(3, 'Work From Home', 24, 0);

INSERT INTO holidays (holiday_name, holiday_date) VALUES
('New Year', '2026-01-01'),
('Republic Day', '2026-01-26'),
('Independence Day', '2026-08-15');