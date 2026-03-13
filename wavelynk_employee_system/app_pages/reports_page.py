import streamlit as st
import pandas as pd

from modules.reports import attendance_report_df, leave_report_df, payroll_summary_df
from modules.employee import get_team_members_by_manager
from utils import export_dataframe_to_excel


def _normalize_series(series):
    return series.astype(str).str.strip().str.lower()


def _filter_df_for_employee(df: pd.DataFrame, user: dict) -> pd.DataFrame:
    if df is None or df.empty:
        return df

    filtered = df.copy()

    match_map = {
        "id": str(user.get("id", "")).strip(),
        "employee_id": str(user.get("employee_id", "")).strip(),
        "username": str(user.get("username", "")).strip(),
        "full_name": str(user.get("full_name", "")).strip(),
        "email": str(user.get("email", "")).strip(),
    }

    for col, value in match_map.items():
        if col in filtered.columns and value:
            return filtered[_normalize_series(filtered[col]) == value.lower()]

    return filtered.iloc[0:0]


def _filter_df_for_manager(df: pd.DataFrame, user: dict) -> pd.DataFrame:
    if df is None or df.empty:
        return df

    filtered = df.copy()
    team_members = get_team_members_by_manager(user["full_name"])

    team_ids = {str(m.get("id", "")).strip().lower() for m in team_members if m.get("id") is not None}
    team_employee_ids = {
        str(m.get("employee_id", "")).strip().lower()
        for m in team_members
        if m.get("employee_id")
    }
    team_usernames = {
        str(m.get("username", "")).strip().lower()
        for m in team_members
        if m.get("username")
    }
    team_names = {
        str(m.get("full_name", "")).strip().lower()
        for m in team_members
        if m.get("full_name")
    }
    team_emails = {
        str(m.get("email", "")).strip().lower()
        for m in team_members
        if m.get("email")
    }

    matched_parts = []

    if "id" in filtered.columns and team_ids:
        matched_parts.append(filtered[_normalize_series(filtered["id"]).isin(team_ids)])

    if "employee_id" in filtered.columns and team_employee_ids:
        matched_parts.append(filtered[_normalize_series(filtered["employee_id"]).isin(team_employee_ids)])

    if "username" in filtered.columns and team_usernames:
        matched_parts.append(filtered[_normalize_series(filtered["username"]).isin(team_usernames)])

    if "full_name" in filtered.columns and team_names:
        matched_parts.append(filtered[_normalize_series(filtered["full_name"]).isin(team_names)])

    if "email" in filtered.columns and team_emails:
        matched_parts.append(filtered[_normalize_series(filtered["email"]).isin(team_emails)])

    if "manager_name" in filtered.columns and user.get("full_name"):
        matched_parts.append(
            filtered[
                _normalize_series(filtered["manager_name"])
                == str(user["full_name"]).strip().lower()
            ]
        )

    if matched_parts:
        combined = pd.concat(matched_parts, ignore_index=False)
        combined = combined.loc[~combined.index.duplicated(keep="first")]
        return combined

    return filtered.iloc[0:0]


def _apply_role_filter(df: pd.DataFrame, user: dict) -> pd.DataFrame:
    role = str(user.get("role", "")).strip()

    if role in ["Admin", "HR"]:
        return df

    if role in ["Manager", "Team Lead", "HOD"]:
        return _filter_df_for_manager(df, user)

    return _filter_df_for_employee(df, user)


def _load_report_df(report_type: str) -> tuple[pd.DataFrame, str]:
    if report_type == "Attendance Report":
        return attendance_report_df(), "attendance_report.xlsx"
    if report_type == "Leave Report":
        return leave_report_df(), "leave_report.xlsx"
    return payroll_summary_df(), "payroll_summary.xlsx"


def _get_scope_text(user: dict) -> str:
    role = str(user.get("role", "")).strip()

    if role in ["Admin", "HR"]:
        return "Showing organization-wide records based on your access."
    if role in ["Manager", "Team Lead", "HOD"]:
        return "Showing only records for employees reporting under you."
    return "Showing only your personal records."


def show(user):
    st.markdown("<div class='page-title'>Reports Page</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='page-subtitle'>Attendance, leave and payroll summary reports.</div>",
        unsafe_allow_html=True,
    )

    st.info(_get_scope_text(user))

    report_type = st.selectbox(
        "Select Report Type",
        ["Attendance Report", "Leave Report", "Payroll Summary"],
    )

    raw_df, filename = _load_report_df(report_type)
    df = _apply_role_filter(raw_df, user)

    if df is None or df.empty:
        st.warning("No report data available for your access level.")
        return

    st.dataframe(df, use_container_width=True)

    st.caption(f"Rows visible: {len(df)}")

    if st.button("Export to Excel", use_container_width=True):
        path = export_dataframe_to_excel(df, filename)
        st.success(f"Report exported: {path}")