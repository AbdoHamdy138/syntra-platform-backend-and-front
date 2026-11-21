import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.config import settings

logger = logging.getLogger("syntra.email")

class EmailService:
    @staticmethod
    def send_otp_email(to_email: str, code: str) -> bool:
        """
        Sends a 6-digit OTP verification code via SMTP.
        If SMTP credentials are not configured, it logs the code to the console for testing.
        """
        clean_email = to_email.strip().lower()

        # Check if SMTP is configured
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            print("\n" + "=" * 60)
            print(f"📧 [EMAIL SIMULATOR] Outbound Verification Email")
            print(f"To: {clean_email}")
            print(f"Verification Code: {code}")
            print(f"Note: To send REAL emails via Gmail/SendGrid, configure SMTP_USER & SMTP_PASSWORD in backend/.env")
            print("=" * 60 + "\n")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"Your SYNTRA Security Verification Code: {code}"
            from_addr = settings.SMTP_FROM_EMAIL or settings.SMTP_USER
            msg["From"] = f"{settings.SMTP_FROM_NAME} <{from_addr}>"
            msg["To"] = clean_email

            # Plain text fallback
            text_body = f"""Hello Analyst,

Your SYNTRA Threat Intelligence verification code is:

    {code}

This code will expire in 10 minutes. If you did not request this verification, please ignore this email.

— SYNTRA Security Operations
"""

            # HTML formatted email
            html_body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0b0f17; color: #e2e8f0; margin: 0; padding: 20px; }}
    .container {{ max-width: 480px; margin: 0 auto; background-color: #121824; border: 1px solid #1e293b; border-radius: 8px; padding: 32px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }}
    .logo {{ color: #ff6b00; font-weight: 800; font-size: 20px; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 24px; }}
    .title {{ font-size: 18px; font-weight: 600; color: #f8fafc; margin-bottom: 12px; }}
    .desc {{ font-size: 14px; color: #94a3b8; line-height: 1.5; margin-bottom: 24px; }}
    .code-box {{ background-color: #1a2234; border: 1px solid #ff6b00; border-radius: 6px; padding: 16px; text-align: center; margin-bottom: 24px; }}
    .code {{ font-family: monospace; font-size: 32px; font-weight: 700; letter-spacing: 8px; color: #ff6b00; }}
    .footer {{ font-size: 12px; color: #64748b; border-top: 1px solid #1e293b; padding-top: 16px; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="logo">🛡️ SYNTRA</div>
    <div class="title">Verification Code</div>
    <div class="desc">Enter the 6-digit one-time code below to verify your identity and activate your SYNTRA Threat Intelligence session:</div>
    <div class="code-box">
      <div class="code">{code}</div>
    </div>
    <div class="desc" style="font-size: 12px;">This code will expire in <strong>10 minutes</strong>. Do not share this code with anyone.</div>
    <div class="footer">
      If you did not initiate this request, you can safely disregard this email.
    </div>
  </div>
</body>
</html>"""

            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)

            print(f"✅ Real email successfully sent to {clean_email} via {settings.SMTP_HOST}!")
            return True

        except Exception as exc:
            print(f"⚠️ SMTP error while sending email to {clean_email}: {str(exc)}")
            logger.error(f"Failed to send email to {clean_email}: {exc}")
            return False

