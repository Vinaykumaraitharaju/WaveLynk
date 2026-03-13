import streamlit as st
import pandas as pd
from modules.live_status import get_live_status


def show(user):
    if user["role"] not in ["Admin", "Manager"]:
        st.warning("You do not have access to this page.")
        return

    st.markdown("<div class='page-title'>Live Status Dashboard</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-subtitle'>See working, break, leave, holiday and offline states live.</div>", unsafe_allow_html=True)

    st.dataframe(pd.DataFrame(get_live_status()), use_container_width=True)