import streamlit as st
from auth import change_user_password


def show(user):
    st.markdown("<div class='page-title'>Change Password</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='page-subtitle'>Update your account password using strong security rules.</div>",
        unsafe_allow_html=True,
    )

    st.info(
        "Password must be at least 8 characters long and include uppercase, lowercase, number, and special character."
    )

    with st.form("change_password_form"):
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")

        submit = st.form_submit_button("Update Password", use_container_width=True)

        if submit:
            ok, msg = change_user_password(
                user["id"],
                current_password.strip(),
                new_password.strip(),
                confirm_password.strip(),
            )

            if ok:
                st.success(msg)
            else:
                st.error(msg)