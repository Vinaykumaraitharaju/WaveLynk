import streamlit as st
from auth import create_password_reset_otp, reset_password_with_otp


def show():
    st.markdown("<div class='page-title'>Forgot Password</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='page-subtitle'>Reset your account password using OTP sent to your registered email.</div>",
        unsafe_allow_html=True,
    )

    st.info(
        "Use your username or registered email. OTP is valid for 10 minutes. New password must be strong."
    )

    tab1, tab2 = st.tabs(["Send OTP", "Reset Password"])

    with tab1:
        with st.form("send_otp_form"):
            identifier = st.text_input("Username or Email")
            send_otp = st.form_submit_button("Send OTP", use_container_width=True)

            if send_otp:
                ok, msg = create_password_reset_otp(identifier.strip())
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

    with tab2:
        with st.form("reset_password_form"):
            identifier = st.text_input("Username or Email", key="reset_identifier")
            otp_code = st.text_input("OTP Code")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")

            reset_btn = st.form_submit_button("Reset Password", use_container_width=True)

            if reset_btn:
                ok, msg = reset_password_with_otp(
                    identifier.strip(),
                    otp_code.strip(),
                    new_password.strip(),
                    confirm_password.strip(),
                )
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)