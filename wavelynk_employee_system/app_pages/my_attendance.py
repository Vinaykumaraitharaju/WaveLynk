import streamlit as st
import pandas as pd
from modules.attendance import get_user_attendance_history


def show(user):
    st.markdown("<div class='page-title'>My Attendance</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='page-subtitle'>View your login, logout, break minutes, late login and overtime history.</div>",
        unsafe_allow_html=True,
    )

    data = get_user_attendance_history(user["id"])
    df = pd.DataFrame(data)

    if df.empty:
        st.info("No attendance records found.")
        return

    st.dataframe(df, use_container_width=True)