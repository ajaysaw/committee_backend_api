import secrets
from datetime import datetime, timedelta, timezone
from app.config.settings import settings


def generate_otp() -> str:
    return "".join([str(secrets.randbelow(10)) for _ in range(settings.OTP_LENGTH)])


def get_otp_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
