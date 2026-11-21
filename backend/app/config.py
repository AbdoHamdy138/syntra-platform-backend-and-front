import os
from pathlib import Path
from dotenv import load_dotenv

# Explicitly load backend/.env regardless of current working directory
backend_dir = Path(__file__).resolve().parent.parent
env_path = backend_dir / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

class Settings:
    PORT: int = int(os.getenv("PORT", "4000"))
    NODE_ENV: str = os.getenv("NODE_ENV", "development")
    CLIENT_ORIGIN: str = os.getenv("CLIENT_ORIGIN", "http://localhost:5173")

    # PostgreSQL Database
    DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "Mobarak1972$")
    DB_NAME: str = os.getenv("DB_NAME", "syntra_db")

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # JWT Settings
    JWT_SECRET: str = os.getenv("JWT_SECRET", "syntra_super_secure_jwt_secret_key_2026_xyz987654321")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRES_IN: int = int(os.getenv("JWT_EXPIRES_IN", "604800"))  # 7 days

    # OTP Settings
    OTP_EXPIRES_IN_SECONDS: int = int(os.getenv("OTP_EXPIRES_IN_SECONDS", "600"))  # 10 min
    OTP_RESEND_COOLDOWN_SECONDS: int = int(os.getenv("OTP_RESEND_COOLDOWN_SECONDS", "60"))
    OTP_MAX_ATTEMPTS: int = int(os.getenv("OTP_MAX_ATTEMPTS", "5"))
    DEMO_OTP_IN_RESPONSE: bool = os.getenv("DEMO_OTP_IN_RESPONSE", "true").lower() == "true"

    # SMTP / Real Email Delivery Settings
    SMTP_ENABLED: bool = os.getenv("SMTP_ENABLED", "false").lower() == "true"
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "")
    SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "SYNTRA Security")

    # SMS Delivery Settings (Twilio)
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")

settings = Settings()

