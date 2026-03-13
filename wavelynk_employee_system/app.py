import os
import time
import html
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from st_cookies_manager import EncryptedCookieManager

from auth import authenticate_user, logout_user
from database import init_db, fetch_one
from app_pages import (
    admin_panel,
    apply_leave,
    change_password,
    forgot_password,
    leave_balance,
    live_status_dashboard,
    my_attendance,
    reports_page,
    team_attendance,
    team_dashboard,
    team_leave_approvals,
)

load_dotenv()

st.set_page_config(
    page_title="WaveLynk HRMS",
    page_icon="🟦",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR / "assets" / "logo.png"
CSS_PATH = BASE_DIR / "assets" / "styles.css"

cookies = EncryptedCookieManager(
    prefix="wavelynk/hrms/",
    password=os.getenv("COOKIES_PASSWORD", "wavelynk_local_cookie_secret_2026"),
)

if not cookies.ready():
    st.stop()

init_db()

SESSION_TIMEOUT_SECONDS = 600  # 10 minutes


def load_css():
    """
    Load CSS using a project-safe absolute path.
    Works on local machine and Streamlit Cloud.
    """
    if CSS_PATH.exists():
        css_content = CSS_PATH.read_text(encoding="utf-8")
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
        return True
    return False


def debug_asset_paths():
    """
    Optional debug helper. Enable temporarily when checking deployment issues.
    """
    st.write("BASE_DIR:", str(BASE_DIR))
    st.write("CSS_PATH:", str(CSS_PATH))
    st.write("CSS exists:", CSS_PATH.exists())
    st.write("LOGO_PATH:", str(LOGO_PATH))
    st.write("Logo exists:", LOGO_PATH.exists())


load_css()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = None

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

if "logout_message" not in st.session_state:
    st.session_state.logout_message = False

if "cookie_restore_done" not in st.session_state:
    st.session_state.cookie_restore_done = False

if "login_mode" not in st.session_state:
    st.session_state.login_mode = "login"

if "last_activity" not in st.session_state:
    st.session_state.last_activity = time.time()


def build_user_dict(row):
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
    }


def get_user_by_id(user_id: int):
    row = fetch_one(
        """
        SELECT id, employee_id, username, full_name, role, department, phone, email,
               joining_date, employment_status, manager_name, is_active
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    )

    if not row or not row["is_active"]:
        return None

    return build_user_dict(row)


def set_logged_in_user(user: dict):
    st.session_state.logged_in = True
    st.session_state.user = user
    st.session_state.page = "Dashboard"
    st.session_state.logout_message = False
    st.session_state.last_activity = time.time()


def clear_logged_in_user():
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.page = "Dashboard"


def save_login_cookie(user: dict):
    cookies["user_id"] = str(user["id"])
    cookies["logout_flag"] = "0"
    cookies.save()


def clear_login_cookie():
    cookies["user_id"] = ""
    cookies["logout_flag"] = "1"
    cookies.save()


def restore_login_from_cookie():
    if st.session_state.logged_in:
        return

    if st.session_state.cookie_restore_done:
        return

    st.session_state.cookie_restore_done = True

    logout_flag = cookies.get("logout_flag")
    if logout_flag == "1":
        return

    user_id = cookies.get("user_id")
    if not user_id:
        return

    try:
        user = get_user_by_id(int(user_id))
    except (TypeError, ValueError):
        user = None

    if user:
        set_logged_in_user(user)
    else:
        clear_login_cookie()


def render_top_banner():
    col1, col2 = st.columns([8, 1])

    with col1:
        st.markdown(
            """
            <div class="top-banner">
                <div class="top-banner-title">WaveLynk Employee Monitoring & Attendance System</div>
                <div class="top-banner-subtitle">
                    Attendance, leave, live status, reports and team management
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        if st.session_state.logged_in:
            st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            if st.button("Logout", use_container_width=True):
                logout_user()
                clear_logged_in_user()
                clear_login_cookie()
                st.session_state.logout_message = True
                st.session_state.cookie_restore_done = True
                st.rerun()


def login_page():
    render_top_banner()

    if st.session_state.logout_message:
        st.markdown(
            """
            <div class="custom-info-box">Logged out successfully.</div>
            """,
            unsafe_allow_html=True,
        )
        st.session_state.logout_message = False

    if not CSS_PATH.exists():
        st.warning("CSS file not found: assets/styles.css")

    left, right = st.columns([1.25, 1], gap="large")

    with left:
        logo_col1, logo_col2, logo_col3 = st.columns([1, 2, 1])

        with logo_col2:
            if LOGO_PATH.exists():
                st.markdown(
                    """
                    <div style="
                        background: white;
                        padding: 18px;
                        border-radius: 14px;
                        text-align: center;
                        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
                        margin-bottom: 20px;
                    ">
                    """,
                    unsafe_allow_html=True,
                )
                st.image(str(LOGO_PATH), width=220)
                st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            """
            <div class="hero-card">
                <div class="hero-title">WaveLynk HRMS Portal</div>
                <div class="hero-subtitle">
                    Manage attendance, leave, team visibility and live employee activity in one place.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        if st.session_state.login_mode == "login":
            st.markdown(
                """
                <div class="login-card-title">Sign in to continue</div>
                <div class="login-card-subtitle">
                    Secure access for employees, managers, HR and administrators
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Login", use_container_width=True)

                if submit:
                    user = authenticate_user(username.strip(), password.strip())

                    if user:
                        clear_logged_in_user()
                        set_logged_in_user(user)
                        save_login_cookie(user)
                        st.session_state.cookie_restore_done = True

                        st.success("Login successful. Redirecting...")
                        time.sleep(0.6)
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")

            c1, c2 = st.columns([1, 1])
            with c1:
                if st.button("Forgot Password?", use_container_width=True):
                    st.session_state.login_mode = "forgot_password"
                    st.rerun()
        else:
            forgot_password.show()
            if st.button("Back to Login", use_container_width=True):
                st.session_state.login_mode = "login"
                st.rerun()


def sidebar_navigation():
    user = st.session_state.user
    role = user["role"]

    with st.sidebar:
        if LOGO_PATH.exists():
            st.markdown(
                """
                <div style="
                    background: white;
                    padding: 12px;
                    border-radius: 12px;
                    text-align: center;
                    margin-bottom: 14px;
                ">
                """,
                unsafe_allow_html=True,
            )
            st.image(str(LOGO_PATH), width=160)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            f"""
            <div class="sidebar-user-box">
                <div class="sidebar-user-title">Welcome</div>
                <div class="sidebar-user-name">{html.escape(str(user['full_name']))}</div>
                <div class="sidebar-user-role">{html.escape(str(user['role']))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if role == "Employee":
            allowed = [
                "Dashboard",
                "My Attendance",
                "Apply Leave",
                "Leave Balance",
                "Reports Page",
                "Change Password",
            ]
        elif role in ["Manager", "Team Lead", "HOD"]:
            allowed = [
                "Dashboard",
                "My Attendance",
                "Apply Leave",
                "Leave Balance",
                "Team Attendance",
                "Team Dashboard",
                "Team Leave Approvals",
                "Reports Page",
                "Change Password",
            ]
        else:
            allowed = [
                "Dashboard",
                "My Attendance",
                "Apply Leave",
                "Leave Balance",
                "Live Status Dashboard",
                "Team Attendance",
                "Team Dashboard",
                "Reports Page",
                "Admin Panel",
                "Change Password",
            ]

        current_page = (
            st.session_state.page if st.session_state.page in allowed else allowed[0]
        )
        st.session_state.page = st.radio(
            "Navigation", allowed, index=allowed.index(current_page)
        )


def dashboard_page():
    from modules.attendance import (
        get_today_attendance_summary,
        start_work,
        start_break,
        end_work,
    )
    from modules.breaks import end_break_by_user, get_break_timer
    from modules.live_status import get_live_status_counts
    from modules.employee import get_all_subordinates
    from modules.leave import get_leave_requests_for_manager
    from modules.holidays import is_today_holiday

    user = st.session_state.user
    today_data = get_today_attendance_summary(user["id"]) or {}
    holiday = is_today_holiday()

    if "dashboard_action_message" not in st.session_state:
        st.session_state.dashboard_action_message = None

    if "dashboard_action_type" not in st.session_state:
        st.session_state.dashboard_action_type = None

    def sanitize_text(value, default="-"):
        if value in [None, "", "None"]:
            return default
        value = (
            str(value)
            .replace("<br />", " ")
            .replace("<br/>", " ")
            .replace("<br>", " ")
            .replace("\n", " ")
        )
        value = " ".join(value.split())
        return html.escape(value)

    def metric_card(label, value):
        st.markdown(
            f"""
            <div class='metric-card'>
                <div class='metric-label'>{html.escape(str(label))}</div>
                <div class='metric-value'>{sanitize_text(value)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    def info_card(title, lines):
        body = "".join(
            [
                f"<div style='margin-bottom:6px;'>{html.escape(str(line))}</div>"
                for line in lines
            ]
        )
        st.markdown(
            f"""
            <div class='metric-card'>
                <div class='metric-label' style='margin-bottom:10px;'>{html.escape(str(title))}</div>
                <div style='font-size:14px; line-height:1.5;'>{body}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    status_label = today_data.get("status", "Not Started")
    attendance_id = today_data.get("attendance_id")
    break_timer = get_break_timer(attendance_id) if attendance_id else None

    st.markdown("<div class='page-title'>Dashboard</div>", unsafe_allow_html=True)

    if user["role"] == "Employee":
        st.markdown(
            "<div class='page-subtitle'>Your daily attendance, live work status and quick actions.</div>",
            unsafe_allow_html=True,
        )
    elif user["role"] in ["Manager", "Team Lead", "HOD"]:
        st.markdown(
            "<div class='page-subtitle'>Your daily status and team overview with quick actions.</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div class='page-subtitle'>Corporate live overview, attendance and activity summary.</div>",
            unsafe_allow_html=True,
        )

    if holiday:
        st.info(f"Today is a holiday: {holiday['holiday_name']}")

    if st.session_state.dashboard_action_message:
        msg = st.session_state.dashboard_action_message
        msg_type = st.session_state.dashboard_action_type

        if msg_type == "success":
            st.success(msg)
        elif msg_type == "warning":
            st.warning(msg)
        else:
            st.info(msg)

        st.session_state.dashboard_action_message = None
        st.session_state.dashboard_action_type = None

    st.subheader("Current Status")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Current Status", status_label)
    with c2:
        metric_card("Login Time", today_data.get("login_time", "-"))
    with c3:
        metric_card("Logout Time", today_data.get("logout_time", "-"))
    with c4:
        metric_card("Work Hours", today_data.get("work_hours", "0h 0m"))

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        metric_card("Break Minutes", today_data.get("break_minutes", 0))
    with c6:
        metric_card("Late Login", today_data.get("late_login", "No"))
    with c7:
        metric_card("Early Logout", today_data.get("early_logout", "No"))
    with c8:
        metric_card("Overtime", today_data.get("overtime", "0m"))

    if break_timer:
        st.subheader("Active Break")
        b1, b2, b3, b4 = st.columns(4)
        with b1:
            metric_card("Break Type", break_timer.get("break_type", "-"))
        with b2:
            metric_card("Used", f"{break_timer.get('used_minutes', 0)} min")
        with b3:
            metric_card("Allowed", f"{break_timer.get('allowed_minutes', 0)} min")
        with b4:
            if break_timer.get("is_exceeded"):
                metric_card("Exceeded By", f"{break_timer.get('exceeded', 0)} min")
            else:
                metric_card(
                    "Remaining",
                    f"{max(break_timer.get('remaining_minutes', 0), 0)} min",
                )

    st.subheader("Quick Actions")
    q1, q2, q3, q4, q5, q6 = st.columns(6)

    with q1:
        if st.button("Start Work", use_container_width=True):
            ok, msg = start_work(user["id"])
            st.session_state.dashboard_action_message = msg
            st.session_state.dashboard_action_type = "success" if ok else "warning"
            st.rerun()

    with q2:
        if st.button("Tea Break", use_container_width=True):
            ok, msg = start_break(user["id"], "Tea Break")
            st.session_state.dashboard_action_message = msg
            st.session_state.dashboard_action_type = "success" if ok else "warning"
            st.rerun()

    with q3:
        if st.button("Lunch Break", use_container_width=True):
            ok, msg = start_break(user["id"], "Lunch Break")
            st.session_state.dashboard_action_message = msg
            st.session_state.dashboard_action_type = "success" if ok else "warning"
            st.rerun()

    with q4:
        if st.button("Personal Break", use_container_width=True):
            ok, msg = start_break(user["id"], "Personal Break")
            st.session_state.dashboard_action_message = msg
            st.session_state.dashboard_action_type = "success" if ok else "warning"
            st.rerun()

    with q5:
        if st.button("End Break", use_container_width=True):
            ok, msg = end_break_by_user(user["id"])
            st.session_state.dashboard_action_message = msg
            st.session_state.dashboard_action_type = "success" if ok else "warning"
            st.rerun()

    with q6:
        if st.button("End Work", use_container_width=True):
            ok, msg = end_work(user["id"])
            st.session_state.dashboard_action_message = msg
            st.session_state.dashboard_action_type = "success" if ok else "warning"
            st.rerun()

    st.markdown("---")

    if user["role"] == "Employee":
        st.subheader("Today at a Glance")
        x1, x2 = st.columns(2)

        with x1:
            info_card(
                "Session Summary",
                [
                    f"Status: {today_data.get('status', 'Not Started')}",
                    f"Work Hours: {today_data.get('work_hours', '0h 0m')}",
                    f"Break Minutes: {today_data.get('break_minutes', 0)}",
                    f"Late Login: {today_data.get('late_login', 'No')}",
                ],
            )

        with x2:
            lines = [
                "Use My Attendance for detailed history.",
                "Use Apply Leave to submit a leave request.",
                "Use Leave Balance to see your full leave balances.",
            ]
            if break_timer:
                lines.insert(0, f"Active Break: {break_timer.get('break_type', '-')}")
            info_card("Helpful Shortcuts", lines)

    elif user["role"] in ["Manager", "Team Lead", "HOD"]:
        team_members = get_all_subordinates(user["id"]) or []
        total_team = len(team_members)
        present_team = 0
        working_team = 0
        on_break_team = 0

        for member in team_members:
            member_summary = get_today_attendance_summary(member["id"]) or {}
            status = str(member_summary.get("status", "")).strip().lower()

            if member_summary.get("login_time") not in [None, "", "-", "N/A"]:
                present_team += 1

            if status == "working":
                working_team += 1
            elif status == "on break":
                on_break_team += 1

        pending_approvals = 0
        try:
            leave_rows = get_leave_requests_for_manager(user["id"]) or []
            pending_approvals = len(
                [
                    row
                    for row in leave_rows
                    if str(row.get("status", "")).strip().lower() == "pending"
                ]
            )
        except Exception:
            pending_approvals = 0

        st.subheader("Team Snapshot")
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            metric_card("Team Members", total_team)
        with m2:
            metric_card("Present Today", present_team)
        with m3:
            metric_card("Working Now", working_team)
        with m4:
            metric_card("On Break", on_break_team)

        m5, m6 = st.columns(2)
        with m5:
            metric_card("Pending Leave Approvals", pending_approvals)
        with m6:
            info_card(
                "Manager Shortcuts",
                [
                    "Use Team Attendance for detailed attendance.",
                    "Use Team Dashboard for team summary.",
                    "Use Team Leave Approvals to approve or reject leave.",
                ],
            )

    else:
        counts = get_live_status_counts() or {}

        st.subheader("Company Snapshot")
        a1, a2, a3, a4, a5 = st.columns(5)
        with a1:
            metric_card("Present Today", counts.get("present", 0))
        with a2:
            metric_card("On Leave", counts.get("on_leave", 0))
        with a3:
            metric_card("Working", counts.get("working", 0))
        with a4:
            metric_card("On Break", counts.get("on_break", 0))
        with a5:
            metric_card("Completed", counts.get("completed", 0))

        a6, a7 = st.columns(2)
        with a6:
            metric_card("Not Started", counts.get("not_started", 0))
        with a7:
            info_card(
                "Admin / HR Shortcuts",
                [
                    "Use Live Status Dashboard for detailed live monitoring.",
                    "Use Team Attendance for attendance review.",
                    "Use Reports Page for detailed reports.",
                    "Use Admin Panel for employee and leave administration.",
                ],
            )


def main():
    restore_login_from_cookie()

    if not st.session_state.logged_in:
        login_page()
        return

    current_time = time.time()
    inactive_time = current_time - st.session_state.last_activity

    if inactive_time > SESSION_TIMEOUT_SECONDS:
        logout_user()
        clear_logged_in_user()
        clear_login_cookie()
        st.session_state.logout_message = True
        st.warning("Session expired due to inactivity. Please login again.")
        st.rerun()

    st.session_state.last_activity = current_time

    render_top_banner()
    sidebar_navigation()

    user = st.session_state.user
    role = user["role"]
    page = st.session_state.page

    if page == "Dashboard":
        dashboard_page()
    elif page == "My Attendance":
        my_attendance.show(user)
    elif page == "Apply Leave":
        apply_leave.show(user)
    elif page == "Leave Balance":
        leave_balance.show(user)
    elif page == "Team Leave Approvals":
        team_leave_approvals.show(user)
    elif page == "Live Status Dashboard":
        if role not in ["Admin", "HR"]:
            st.error("Access denied. You are not authorized to view this page.")
            return
        live_status_dashboard.show(user)
    elif page == "Team Attendance":
        if role not in ["Admin", "HR", "Manager", "Team Lead", "HOD"]:
            st.error("Access denied. You are not authorized to view this page.")
            return
        team_attendance.show(user)
    elif page == "Team Dashboard":
        if role not in ["Admin", "HR", "Manager", "Team Lead", "HOD"]:
            st.error("Access denied. You are not authorized to view this page.")
            return
        team_dashboard.show(user)
    elif page == "Reports Page":
        reports_page.show(user)
    elif page == "Admin Panel":
        if role not in ["Admin", "HR"]:
            st.error("Access denied. You are not authorized to view this page.")
            return
        admin_panel.show(user)
    elif page == "Change Password":
        change_password.show(user)


if __name__ == "__main__":
    main()
