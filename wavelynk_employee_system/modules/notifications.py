import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()


def _get_smtp_config():
    return {
        "host": os.getenv("SMTP_HOST", "").strip(),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "username": os.getenv("SMTP_USERNAME", "").strip(),
        "password": os.getenv("SMTP_PASSWORD", "").strip(),
        "from_email": os.getenv("FROM_EMAIL", "").strip(),
    }


def send_email(to_email: str, subject: str, body: str):
    if not to_email:
        return False, "Recipient email is missing."

    config = _get_smtp_config()

    if not config["host"]:
        return False, "SMTP_HOST is missing."
    if not config["username"]:
        return False, "SMTP_USERNAME is missing."
    if not config["password"]:
        return False, "SMTP_PASSWORD is missing."
    if not config["from_email"]:
        return False, "FROM_EMAIL is missing."

    try:
        message = MIMEMultipart()
        message["From"] = config["from_email"]
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(config["host"], config["port"])
        server.starttls()
        server.login(config["username"], config["password"])
        server.sendmail(config["from_email"], to_email, message.as_string())
        server.quit()

        return True, "Email sent successfully."
    except Exception as e:
        return False, str(e)


def send_leave_applied_email(manager_email: str, employee_name: str, leave_type: str, from_date: str, to_date: str, reason: str):
    subject = f"Leave Request Submitted - {employee_name}"
    body = f"""
Hello,

A new leave request has been submitted.

Employee: {employee_name}
Leave Type: {leave_type}
From Date: {from_date}
To Date: {to_date}
Reason: {reason}

Status: Pending

Please review it in the HRMS portal.

Regards,
WaveLynk HRMS
""".strip()

    return send_email(manager_email, subject, body)


def send_leave_status_email(employee_email: str, employee_name: str, leave_type: str, from_date: str, to_date: str, status: str, approved_by: str):
    subject = f"Leave Request {status} - {leave_type}"
    body = f"""
Hello {employee_name},

Your leave request has been updated.

Leave Type: {leave_type}
From Date: {from_date}
To Date: {to_date}
Status: {status}
Updated By: {approved_by}

Please log in to the HRMS portal for more details.

Regards,
WaveLynk HRMS
""".strip()

    return send_email(employee_email, subject, body)


def send_password_reset_otp_email(user_email: str, user_name: str, otp_code: str):
    subject = "WaveLynk HRMS Password Reset OTP"
    body = f"""
Hello {user_name},

You requested to reset your password.

Your OTP is: {otp_code}

This OTP will expire in 10 minutes.

If you did not request this, please ignore this email.

Regards,
WaveLynk HRMS
""".strip()

    return send_email(user_email, subject, body)