import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Application
    APP_NAME: str = "Committee Management Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # Database
    # DB_HOST: str = os.getenv("DB_HOST", "localhost")  # Commented out for live database
    # DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    # DB_USER: str = os.getenv("DB_USER", "root")
    # DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    # DB_NAME: str = os.getenv("DB_NAME", "committee")
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:nmxqodIjrPyTGajKWFzPNRIEnAvLtwHP@shortline.proxy.rlwy.net:17199/railway",
    )

    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-this-secret-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

    # OTP
    OTP_EXPIRY_MINUTES: int = int(os.getenv("OTP_EXPIRY_MINUTES", "5"))
    OTP_LENGTH: int = 6

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100


settings = Settings()
