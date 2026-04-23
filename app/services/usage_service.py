from datetime import datetime, timezone

from flask import current_app
from pymongo import ReturnDocument

from app import get_db


def get_daily_limit_for_user(user):
    if user.get("role") == "admin":
        return current_app.config["ADMIN_DAILY_USAGE_LIMIT"]
    return current_app.config["USER_DAILY_USAGE_LIMIT"]


def reset_daily_usage_if_needed(user, daily_limit):
    today = datetime.now(timezone.utc).date().isoformat()
    if user.get("usage_date") == today:
        return user

    return get_db().users.find_one_and_update(
        {"_id": user["_id"]},
        {"$set": {"today_usage": 0, "remaining_usage": daily_limit, "usage_date": today}},
        return_document=ReturnDocument.AFTER,
    )


def can_use_feature(user):
    daily_limit = get_daily_limit_for_user(user)
    user = reset_daily_usage_if_needed(user, daily_limit)

    if user.get("is_blocked"):
        return False, user, "Account is blocked. Contact admin."
    if user.get("remaining_usage", 0) <= 0:
        return False, user, "Daily usage limit exceeded."
    return True, user, None


def increment_failed_attempts(user):
    threshold = current_app.config["FAILED_ATTEMPTS_THRESHOLD"]
    failed_attempts = int(user.get("failed_attempts", 0)) + 1
    blocked = failed_attempts >= threshold

    return get_db().users.find_one_and_update(
        {"_id": user["_id"]},
        {"$set": {"failed_attempts": failed_attempts, "is_blocked": blocked}},
        return_document=ReturnDocument.AFTER,
    )


def clear_failed_attempts(user_id):
    get_db().users.update_one({"_id": user_id}, {"$set": {"failed_attempts": 0}})
