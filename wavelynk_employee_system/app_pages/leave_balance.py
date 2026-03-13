import streamlit as st
import pandas as pd
from modules.leave import get_user_leave_balances


def show(user):
    st.markdown("<div class='page-title'>Leave Balance</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='page-subtitle'>Your available leave balances by leave type.</div>",
        unsafe_allow_html=True,
    )

    balances = get_user_leave_balances(user["id"])

    if not balances:
        st.info("No leave balances available.")
        return

    df = pd.DataFrame(balances)

    if df.empty:
        st.info("No leave balances available.")
        return

    rename_map = {
        "leave_type": "Leave Type",
        "available": "Available",
        "used": "Used",
    }
    df = df.rename(columns=rename_map)

    desired_order = ["Leave Type", "Available", "Used"]
    df = df[[col for col in desired_order if col in df.columns]]

    st.dataframe(df, use_container_width=True, hide_index=True)