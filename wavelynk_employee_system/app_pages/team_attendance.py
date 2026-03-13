import streamlit as st
import pandas as pd
from modules.team import today_team_attendance


def show(user):
    if user["role"] not in ["Admin", "Manager"]:
        st.warning("You do not have access to this page.")
        return

    st.markdown("<div class='page-title'>Team Attendance</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>Today's team attendance status.</div>", unsafe_allow_html=True)

    st.dataframe(pd.DataFrame(today_team_attendance()), use_container_width=True)