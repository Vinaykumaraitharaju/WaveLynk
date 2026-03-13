import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import os


SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USERNAME)
FROM_NAME = os.getenv("FROM_NAME", "WaveLynk HR")


def send_email(to_email: str, subject: str, body: str):
    try:
        if not SMTP_USERNAME or not SMTP_PASSWORD:
            return (
                False,
                "SMTP credentials are missing. Set SMTP_USERNAME and SMTP_PASSWORD.",
            )

        msg = MIMEMultipart()
        msg["From"] = formataddr((FROM_NAME, FROM_EMAIL))
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(FROM_EMAIL, [to_email], msg.as_string())
        server.quit()

        return True, "Email sent successfully."
    except Exception as e:
        return False, str(e)


def send_leave_submitted_email(
    to_email: str,
    employee_name: str,
    employee_id: str,
    leave_type: str,
    from_date: str,
    to_date: str,
    reason: str,
    leave_id: int,
):
    subject = f"New Leave Request - {employee_name} ({employee_id})"

    body = f"""
Dear Manager,

A new leave request has been submitted.

Leave Request ID: {leave_id}
Employee Name: {employee_name}
Employee ID: {employee_id}
Leave Type: {leave_type}
From Date: {from_date}
To Date: {to_date}
Reason: {reason}

Please review the request in the WaveLynk system.

Regards,
WaveLynk Employee System
""".strip()

    return send_email(to_email, subject, body)


def send_leave_status_email(
    to_email: str,
    employee_name: str,
    leave_type: str,
    from_date: str,
    to_date: str,
    status: str,
    approved_by: str,
    leave_id: int,
):
    subject = f"Leave Request {status} - Request ID {leave_id}"

    body = f"""
Dear {employee_name},

Your leave request has been updated.

Leave Request ID: {leave_id}
Leave Type: {leave_type}
From Date: {from_date}
To Date: {to_date}
Status: {status}
Approved / Rejected By: {approved_by}

Please log in to the WaveLynk system for more details.

Regards,
WaveLynk Employee System
""".strip()

    return send_email(to_email, subject, body)


def send_new_employee_welcome_email(
    to_email: str,
    employee_name: str,
    employee_id: str,
    username: str,
    temporary_password: str,
    role: str,
    department: str,
    joining_date: str,
    manager_name=None,
):
    subject = "Welcome to WaveLynk - Your Account Details"

    body = f"""
Dear {employee_name},

Welcome to WaveLynk.

Your employee account has been created successfully. Please find your login details below:

Employee ID: {employee_id}
Username: {username}
Temporary Password: {temporary_password}
Role: {role}
Department: {department}
Joining Date: {joining_date}
Manager: {manager_name or 'Not Assigned'}

Please log in and change your password after your first login.

Regards,
WaveLynk HR / Admin Team
""".strip()

    return send_email(to_email, subject, body)
