import os
import resend

# تهيئة مفتاح الـ API من متغيرات البيئة
resend.api_key = os.getenv("RESEND_API_KEY")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Cartly")

# ⚠️ ملاحظة هامة: في الباقة المجانية بدون توثيق دومين، يجب أن تستخدم هذا الإيميل كمرسِل
FROM_EMAIL = "onboarding@resend.dev"

def send_email(to_email: str, subject: str, html_body: str) -> None:
    try:
        params = {
            "from": f"{SMTP_FROM_NAME} <{FROM_EMAIL}>",
            "to": [to_email],
            "subject": subject,
            "html": html_body,
        }
        
        # إرسال الإيميل عبر واجهة برمجة التطبيقات (API)
        email = resend.Emails.send(params)
        print(f"Email sent successfully: {email}")
        
    except Exception as e:
        print(f"Failed to send email: {e}")

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