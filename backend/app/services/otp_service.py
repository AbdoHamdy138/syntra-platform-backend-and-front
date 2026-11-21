import secrets
import hmac
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from app.config import settings
from app.database import query_one, execute
from app.middleware import raise_invalid_input, raise_rate_limited
from app.services.email_service import EmailService
from app.services.sms_service import SmsService

class OtpService:
    @staticmethod
    def generate_code() -> str:
        """Generate a cryptographically random 6-digit numeric OTP code."""
        return f"{secrets.randbelow(900000) + 100000:06d}"

    @staticmethod
    def create_otp(
        email: str,
        phone: Optional[str] = None,
        flow: str = "signup",
        otp_channel: str = "email"
    ) -> Tuple[str, int]:
        """
        Creates a new OTP for the account.
        Dispatches via Email (SMTP) or Phone (SMS) based on user's selection (otp_channel).
        Checks resend cooldown (60s).
        Returns (code, expires_in_seconds).
        """
        clean_email = email.strip().lower() if email else ""
        clean_phone = SmsService.clean_phone(phone) if phone else None

        if otp_channel == "sms":
            if not clean_phone:
                raise_invalid_input("Please provide a valid phone number to receive the verification code via SMS.")
        else:
            if not clean_email or "@" not in clean_email:
                raise_invalid_input("A valid email address is required.")

        now = datetime.now(timezone.utc)

        # Check resend cooldown
        last_otp = query_one(
            """
            SELECT created_at FROM otp_codes
            WHERE (email = %s OR (phone = %s AND phone != '')) AND flow = %s AND used_at IS NULL
            ORDER BY created_at DESC LIMIT 1
            """,
            (clean_email, clean_phone or "", flow)
        )

        if last_otp and last_otp.get("created_at"):
            created_at = last_otp["created_at"]
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            elapsed = (now - created_at).total_seconds()
            cooldown = settings.OTP_RESEND_COOLDOWN_SECONDS
            if elapsed < cooldown:
                remaining = int(cooldown - elapsed)
                raise_rate_limited(f"Please wait {remaining} seconds before requesting another verification code.")

        # Invalidate previous unconsumed codes
        execute(
            """
            UPDATE otp_codes SET used_at = NOW() 
            WHERE (email = %s OR (phone = %s AND phone != '')) AND flow = %s AND used_at IS NULL
            """,
            (clean_email, clean_phone or "", flow)
        )

        code = OtpService.generate_code()
        expires_at = now + timedelta(seconds=settings.OTP_EXPIRES_IN_SECONDS)

        execute(
            """
            INSERT INTO otp_codes (email, phone, code, flow, attempts, max_attempts, expires_at, created_at)
            VALUES (%s, %s, %s, %s, 0, %s, %s, %s)
            """,
            (clean_email, clean_phone or "", code, flow, settings.OTP_MAX_ATTEMPTS, expires_at, now)
        )

        # Dispatch code based on user's choice: Email or SMS
        if otp_channel == "sms" and clean_phone:
            SmsService.send_otp_sms(clean_phone, code)
        else:
            EmailService.send_otp_email(clean_email, code)

        return code, settings.OTP_EXPIRES_IN_SECONDS

    @staticmethod
    def verify_otp(
        email: Optional[str] = None,
        phone: Optional[str] = None,
        code: str = "",
        flow: str = "signup"
    ) -> bool:
        """
        Verifies the OTP code for the given email or phone and flow.
        Enforces expiration, attempt limits, and single-use invalidation.
        """
        clean_email = email.strip().lower() if email else None
        clean_phone = SmsService.clean_phone(phone) if phone else None
        clean_code = code.strip()

        if not clean_email and not clean_phone:
            raise_invalid_input("An email address or phone number is required to verify.")

        now = datetime.now(timezone.utc)

        # Look for the latest unused OTP code matching email or phone
        if clean_email:
            record = query_one(
                """
                SELECT id, code, attempts, max_attempts, expires_at, used_at
                FROM otp_codes
                WHERE email = %s AND flow = %s
                ORDER BY created_at DESC LIMIT 1
                """,
                (clean_email, flow)
            )
        else:
            record = query_one(
                """
                SELECT id, code, attempts, max_attempts, expires_at, used_at
                FROM otp_codes
                WHERE phone = %s AND flow = %s
                ORDER BY created_at DESC LIMIT 1
                """,
                (clean_phone, flow)
            )

        target = clean_email or clean_phone
        if not record:
            raise_invalid_input(f"No pending verification request found for {target}.")

        if record.get("used_at") is not None:
            raise_invalid_input("This verification code has already been used. Please request a new one.")

        expires_at = record["expires_at"]
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if now > expires_at:
            raise_invalid_input("Verification code has expired. Please request a new code.")

        attempts = record.get("attempts", 0) + 1
        max_attempts = record.get("max_attempts", settings.OTP_MAX_ATTEMPTS)

        # Update attempt count
        execute(
            "UPDATE otp_codes SET attempts = %s WHERE id = %s",
            (attempts, record["id"])
        )

        if attempts > max_attempts:
            execute("UPDATE otp_codes SET used_at = NOW() WHERE id = %s", (record["id"],))
            raise_invalid_input("Maximum verification attempts exceeded. Please request a new code.")

        stored_code = record["code"]
        matches = hmac.compare_digest(stored_code, clean_code)
        
        # In development/demo, also accept 123456 as backup if configured
        if not matches and settings.DEMO_OTP_IN_RESPONSE and clean_code == "123456":
            matches = True

        if not matches:
            remaining_attempts = max(0, max_attempts - attempts)
            raise_invalid_input(f"Invalid verification code. {remaining_attempts} attempts remaining.")

        # Mark code as successfully used
        execute("UPDATE otp_codes SET used_at = NOW() WHERE id = %s", (record["id"],))
        return True
