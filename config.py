import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "")
    MONGO_URI = os.getenv("MONGO_URI", "")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "bg_saas")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "true").lower() == "true"
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    USER_DAILY_USAGE_LIMIT = int(os.getenv("USER_DAILY_USAGE_LIMIT", os.getenv("DAILY_USAGE_LIMIT", "20")))
    ADMIN_DAILY_USAGE_LIMIT = int(os.getenv("ADMIN_DAILY_USAGE_LIMIT", "50"))
    FAILED_ATTEMPTS_THRESHOLD = int(os.getenv("FAILED_ATTEMPTS_THRESHOLD", "5"))
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))
