import streamlit as st
import pandas as pd
from modules.leave import apply_leave, get_user_leave_requests, get_leave_types


def show(user):
    st.markdown("<div class='page-title'>Apply Leave</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='page-subtitle'>Submit your leave request with corporate leave types.</div>",
        unsafe_allow_html=True,
    )

    leave_types = get_leave_types()
    leave_names = [
        x["leave_name"] for x in leave_types if int(x.get("is_active", 1)) == 1
    ]
    if not leave_names:
        st.warning("No active leave types available.")
        return
    with st.form("leave_form"):
        leave_type = st.selectbox("Leave Type", leave_names)
        from_date = st.date_input("From Date")
        to_date = st.date_input("To Date")
        reason = st.text_area("Reason")
        submit = st.form_submit_button("Submit Leave Request", use_container_width=True)

        if submit:
            if from_date > to_date:
                st.error("From Date cannot be greater than To Date.")
            elif not reason.strip():
                st.error("Please enter a reason.")
            else:
                apply_leave(
                    user["id"], leave_type, str(from_date), str(to_date), reason.strip()
                )
                st.success("Leave request submitted successfully.")
                st.rerun()

    st.subheader("My Leave Requests")
    st.dataframe(
        pd.DataFrame(get_user_leave_requests(user["id"])), use_container_width=True
    )
