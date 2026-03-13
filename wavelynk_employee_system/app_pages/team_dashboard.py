import pandas as pd
import streamlit as st

from modules.employee import get_all_subordinates
from modules.attendance import get_today_attendance_summary


def show(user):
    if user["role"] not in ["Admin", "HR", "Manager", "Team Lead", "HOD"]:
        st.warning("You do not have access to this page.")
        return

    st.markdown("<div class='page-title'>Team Dashboard</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='page-subtitle'>Manager summary of employees and today's work status.</div>",
        unsafe_allow_html=True,
    )

    if user["role"] in ["Admin", "HR"]:
        st.info(
            "Admin/HR can use Team Attendance and other admin pages for company-wide monitoring."
        )
        team_members = []
    else:
        team_members = get_all_subordinates(user["id"]) or []

    if not team_members:
        st.info("No team members found under your hierarchy.")
        return

    # =========================================================
    # ROLE SUMMARY
    # =========================================================
    role_counts = {}
    for member in team_members:
        role_name = member.get("role") or "Unknown"
        role_counts[role_name] = role_counts.get(role_name, 0) + 1

    summary_rows = [
        {"Role": role_name, "Employee Count": count}
        for role_name, count in sorted(role_counts.items())
    ]
    summary_df = pd.DataFrame(summary_rows)

    # =========================================================
    # TODAY TEAM STATUS
    # =========================================================
    today_rows = []

    for member in team_members:
        att = get_today_attendance_summary(member["id"]) or {}

        today_rows.append(
            {
                "Employee ID": member.get("employee_id"),
                "Full Name": member.get("full_name"),
                "Role": member.get("role"),
                "Department": member.get("department"),
                "Status": att.get("status", "-"),
                "Login Time": att.get("login_time", "-"),
                "Logout Time": att.get("logout_time", "-"),
                "Work Hours": att.get("work_hours", "0h"),
                "Break Minutes": att.get("break_minutes", 0),
                "Late Login": att.get("late_login", "No"),
                "Early Logout": att.get("early_logout", "No"),
                "Overtime": att.get("overtime", "0m"),
            }
        )

    today_df = pd.DataFrame(today_rows)

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Role Summary")
        st.dataframe(summary_df, use_container_width=True)

    with c2:
        st.subheader("Today's Team Status")
        st.dataframe(today_df, use_container_width=True)
