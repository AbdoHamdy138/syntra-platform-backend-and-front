import re
import httpx
from app.config import settings

class SmsService:
    @staticmethod
    def clean_phone(phone: str) -> str:
        """Strip formatting, keep leading plus and digits."""
        stripped = re.sub(r"[^\d+]", "", phone.strip())
        return stripped

    @staticmethod
    def send_otp_sms(to_phone: str, code: str) -> bool:
        """
        Sends a 6-digit OTP verification code to a phone number via SMS.
        Supports Twilio if configured, otherwise logs clearly for development/testing.
        """
        phone = SmsService.clean_phone(to_phone)
        message = f"Your SYNTRA verification code is: {code}. Valid for 10 minutes."

        # If Twilio credentials are configured
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_PHONE_NUMBER:
            try:
                from_phone = SmsService.clean_phone(settings.TWILIO_PHONE_NUMBER)
                url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"
                resp = httpx.post(
                    url,
                    data={
                        "From": from_phone,
                        "To": phone,
                        "Body": message
                    },
                    auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
                    timeout=10.0
                )
                if resp.status_code in (200, 201):
                    print(f"✅ Real SMS successfully dispatched to {phone} via Twilio!")
                    return True
                else:
                    print(f"⚠️ Twilio API returned error {resp.status_code}: {resp.text}")
                    return False
            except Exception as exc:
                print(f"⚠️ Failed to send SMS via Twilio: {str(exc)}")
                return False

        # Fallback simulator log
        print("\n" + "=" * 60)
        print(f"📱 [SMS SIMULATOR] Outbound Verification SMS")
        print(f"To Phone: {phone}")
        print(f"Verification Code: {code}")
        print(f"Message: {message}")
        print(f"Note: To send REAL SMS, configure TWILIO_ACCOUNT_SID & TWILIO_AUTH_TOKEN in backend/.env")
        print("=" * 60 + "\n")
        return False

