import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Cartly")


def send_email(to_email: str, subject: str, html_body: str) -> None:
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"{SMTP_FROM_NAME} <{SMTP_USER}>"
    message["To"] = to_email

    message.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, to_email, message.as_string())


def send_password_reset_email(to_email: str, reset_link: str) -> None:
    subject = "Reset your password"
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto;">
        <h2>Password Reset Request</h2>
        <p>We received a request to reset your password. Click the button below to choose a new one:</p>
        <p>
            <a href="{reset_link}"
               style="display:inline-block;padding:12px 24px;background:#4f46e5;color:#fff;
                      text-decoration:none;border-radius:6px;">
                Reset Password
            </a>
        </p>
        <p>If you didn't request this, you can safely ignore this email. This link expires in 1 hour.</p>
    </div>
    """
    send_email(to_email, subject, html_body)