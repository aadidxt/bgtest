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
    SESSION_COOKIE_SECURE = False
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    USER_DAILY_USAGE_LIMIT = int(os.getenv("USER_DAILY_USAGE_LIMIT", os.getenv("DAILY_USAGE_LIMIT", "20")))
    ADMIN_DAILY_USAGE_LIMIT = int(os.getenv("ADMIN_DAILY_USAGE_LIMIT", "50"))
    FAILED_ATTEMPTS_THRESHOLD = int(os.getenv("FAILED_ATTEMPTS_THRESHOLD", "5"))
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))

    # Image Tiling
    TILE_SIZE = int(os.getenv("TILE_SIZE", "1024"))
    TILE_OVERLAP = int(os.getenv("TILE_OVERLAP", "64"))

    # OCR
    OCR_ENABLED = os.getenv("OCR_ENABLED", "true")
    OCR_CONFIDENCE_THRESHOLD = float(os.getenv("OCR_CONFIDENCE_THRESHOLD", "0.5"))

    # Mask Fusion
    MASK_FUSION_STRATEGY = os.getenv("MASK_FUSION_STRATEGY", "or")

    # Performance
    PARALLEL_TILE_PROCESSING = os.getenv("PARALLEL_TILE_PROCESSING", "false")
    MAX_IMAGE_RESOLUTION = int(os.getenv("MAX_IMAGE_RESOLUTION", "4096"))
