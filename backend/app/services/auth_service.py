import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
import bcrypt
import jwt
from fastapi import Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings
from app.database import query_one, execute
from app.middleware import (
    raise_invalid_input,
    raise_unauthorized,
    raise_not_found,
    raise_forbidden,
)
from app.models.api_models import AuthUser
from app.services.otp_service import OtpService
from app.services.sms_service import SmsService

security = HTTPBearer(auto_error=False)

class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except Exception:
            return False

    @staticmethod
    def create_jwt_token(user: Dict[str, Any]) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user["id"],
            "email": user.get("email"),
            "phone": user.get("phone"),
            "name": user.get("name"),
            "role": user.get("role", "analyst"),
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=settings.JWT_EXPIRES_IN)).timestamp())
        }
        return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def decode_jwt_token(token: str) -> Dict[str, Any]:
        try:
            return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise_unauthorized("Token has expired")
        except jwt.PyJWTError:
            raise_unauthorized("Invalid token")

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        return query_one(
            "SELECT id, email, phone, name, role, avatar_url, is_verified, created_at FROM users WHERE id = %s",
            (user_id,)
        )

    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        return query_one(
            "SELECT id, email, phone, password_hash, name, role, avatar_url, is_verified, created_at FROM users WHERE email = %s",
            (email.strip().lower(),)
        )

    @staticmethod
    def get_user_by_phone(phone: str) -> Optional[Dict[str, Any]]:
        clean_phone = SmsService.clean_phone(phone)
        return query_one(
            "SELECT id, email, phone, password_hash, name, role, avatar_url, is_verified, created_at FROM users WHERE phone = %s",
            (clean_phone,)
        )

    @staticmethod
    def get_user_by_identifier(email: Optional[str] = None, phone: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if email:
            return AuthService.get_user_by_email(email)
        if phone:
            return AuthService.get_user_by_phone(phone)
        return None

    @staticmethod
    def user_dict_to_auth_user(user: Dict[str, Any]) -> AuthUser:
        created_at_val = user.get("created_at")
        if isinstance(created_at_val, datetime):
            created_at_str = created_at_val.isoformat()
        else:
            created_at_str = str(created_at_val) if created_at_val else None

        return AuthUser(
            id=user["id"],
            email=user.get("email"),
            phone=user.get("phone"),
            name=user.get("name"),
            role=user.get("role", "analyst"),
            avatar_url=user.get("avatar_url"),
            created_at=created_at_str,
            is_verified=bool(user.get("is_verified", False))
        )

    @staticmethod
    def signup(
        email: str,
        phone: Optional[str] = None,
        password: Optional[str] = None,
        name: Optional[str] = None,
        otp_channel: str = "email"
    ) -> Dict[str, Any]:
        clean_email = email.strip().lower() if email else ""
        clean_phone = SmsService.clean_phone(phone) if phone else None

        if not clean_email or "@" not in clean_email:
            raise_invalid_input("A valid email address is required for registration.")

        if otp_channel == "sms":
            if not clean_phone or len(clean_phone) < 7:
                raise_invalid_input("Please provide a valid phone number (e.g. +1... or +20...) to receive the code via SMS.")

        existing = AuthService.get_user_by_email(clean_email)
        now = datetime.now(timezone.utc)
        default_name = clean_email.split("@")[0] if not name else name.strip()

        if existing:
            if existing.get("is_verified"):
                raise_invalid_input("An account with this email already exists. Please log in.")
            user_id = existing["id"]
            pwd_hash = AuthService.hash_password(password) if password else existing.get("password_hash")
            execute(
                """
                UPDATE users
                SET password_hash = %s, name = %s, updated_at = %s, phone = COALESCE(%s, phone)
                WHERE id = %s
                """,
                (pwd_hash, default_name, now, clean_phone, user_id)
            )
        else:
            user_id = f"usr_{uuid.uuid4().hex[:12]}"
            pwd_hash = AuthService.hash_password(password) if password else None
            execute(
                """
                INSERT INTO users (id, email, phone, password_hash, name, role, is_verified, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, 'analyst', FALSE, %s, %s)
                """,
                (user_id, clean_email, clean_phone, pwd_hash, default_name, now, now)
            )

        # Generate and dispatch OTP via selected channel (Email or SMS)
        code, expires_in = OtpService.create_otp(
            email=clean_email,
            phone=clean_phone,
            flow="signup",
            otp_channel=otp_channel
        )
        demo_code = code if settings.DEMO_OTP_IN_RESPONSE else None

        if otp_channel == "sms":
            msg = f"Verification code sent via SMS to {clean_phone}"
        else:
            msg = f"Verification code sent via email to {clean_email}"

        return {
            "status": "pending_verification",
            "message": msg,
            "email": clean_email,
            "phone": clean_phone,
            "otp_channel": otp_channel,
            "expires_in_seconds": expires_in,
            "demo_code": demo_code
        }

    @staticmethod
    def verify_otp(
        email: Optional[str] = None,
        phone: Optional[str] = None,
        code: str = "",
        flow: str = "signup"
    ) -> Dict[str, Any]:
        clean_email = email.strip().lower() if email else None
        clean_phone = SmsService.clean_phone(phone) if phone else None

        OtpService.verify_otp(email=clean_email, phone=clean_phone, code=code, flow=flow)

        user = AuthService.get_user_by_identifier(email=clean_email, phone=clean_phone)
        if not user:
            raise_not_found("User account not found.")

        # Mark user verified
        execute("UPDATE users SET is_verified = TRUE, updated_at = NOW() WHERE id = %s", (user["id"],))
        user["is_verified"] = True

        token = AuthService.create_jwt_token(user)
        return {
            "status": "verified",
            "message": "Verification successful",
            "token": token,
            "refresh_token": f"ref_{uuid.uuid4().hex[:16]}",
            "user": AuthService.user_dict_to_auth_user(user),
            "expires_in_seconds": settings.JWT_EXPIRES_IN
        }

    @staticmethod
    def resend_otp(
        email: str,
        phone: Optional[str] = None,
        flow: str = "signup",
        otp_channel: str = "email"
    ) -> Dict[str, Any]:
        clean_email = email.strip().lower() if email else ""
        clean_phone = SmsService.clean_phone(phone) if phone else None

        user = AuthService.get_user_by_email(clean_email)
        if not user:
            raise_not_found(f"No account found with email '{clean_email}'.")

        active_phone = clean_phone or user.get("phone")
        if otp_channel == "sms" and not active_phone:
            raise_invalid_input("No phone number associated with this account. Please provide a phone number.")

        code, expires_in = OtpService.create_otp(
            email=clean_email,
            phone=active_phone,
            flow=flow,
            otp_channel=otp_channel
        )
        demo_code = code if settings.DEMO_OTP_IN_RESPONSE else None

        if otp_channel == "sms":
            msg = f"Fresh verification code sent via SMS to {active_phone}"
        else:
            msg = f"Fresh verification code sent via email to {clean_email}"

        return {
            "status": "sent",
            "message": msg,
            "email": clean_email,
            "phone": active_phone,
            "otp_channel": otp_channel,
            "expires_in_seconds": expires_in,
            "demo_code": demo_code
        }

    @staticmethod
    def login(
        email: Optional[str] = None,
        phone: Optional[str] = None,
        password: Optional[str] = None
    ) -> Dict[str, Any]:
        clean_email = email.strip().lower() if email else None
        clean_phone = SmsService.clean_phone(phone) if phone else None

        user = AuthService.get_user_by_identifier(email=clean_email, phone=clean_phone)
        if not user:
            raise_invalid_input("Invalid email/phone or password.")

        if user.get("password_hash") and password:
            if not AuthService.verify_password(password, user["password_hash"]):
                raise_invalid_input("Invalid email/phone or password.")
        elif user.get("password_hash") and not password:
            raise_invalid_input("Password is required.")

        # If user is not verified, require OTP verification flow
        if not user.get("is_verified"):
            code, expires_in = OtpService.create_otp(email=clean_email, phone=clean_phone, flow="login")
            dest = clean_email or clean_phone
            raise_invalid_input(f"Account is not verified. A verification code has been sent to {dest}.")

        token = AuthService.create_jwt_token(user)
        return {
            "status": "authenticated",
            "message": "Authentication successful",
            "token": token,
            "refresh_token": f"ref_{uuid.uuid4().hex[:16]}",
            "user": AuthService.user_dict_to_auth_user(user),
            "expires_in_seconds": settings.JWT_EXPIRES_IN
        }

    @staticmethod
    def create_anonymous() -> Dict[str, Any]:
        guest_id = f"guest_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        user_dict = {
            "id": guest_id,
            "email": None,
            "phone": None,
            "name": "Guest Analyst",
            "role": "guest",
            "avatar_url": None,
            "is_verified": False,
            "created_at": now
        }
        execute(
            """
            INSERT INTO users (id, email, phone, name, role, is_verified, created_at, updated_at)
            VALUES (%s, NULL, NULL, %s, 'guest', FALSE, %s, %s)
            """,
            (guest_id, "Guest Analyst", now, now)
        )
        token = AuthService.create_jwt_token(user_dict)
        return {
            "status": "authenticated",
            "token": token,
            "user": AuthService.user_dict_to_auth_user(user_dict),
            "expires_in_seconds": settings.JWT_EXPIRES_IN
        }

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> AuthUser:
    if not credentials or not credentials.credentials:
        raise_unauthorized("Authentication required. Please provide a valid Bearer token.")
    token = credentials.credentials
    payload = AuthService.decode_jwt_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise_unauthorized("Invalid token payload")
    user = AuthService.get_user_by_id(user_id)
    if not user:
        raise_unauthorized("User not found")
    return AuthService.user_dict_to_auth_user(user)

def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[AuthUser]:
    if not credentials or not credentials.credentials:
        return None
    try:
        token = credentials.credentials
        payload = AuthService.decode_jwt_token(token)
        user_id = payload.get("sub")
        if not user_id:
            return None
        user = AuthService.get_user_by_id(user_id)
        if not user:
            return None
        return AuthService.user_dict_to_auth_user(user)
    except Exception:
        return None
