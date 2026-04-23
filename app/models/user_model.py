from datetime import datetime, timezone

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from app import get_db
from app.utils.security import hash_password, verify_password


def _users():
    return get_db().users


def ensure_indexes():
    _users().create_index("username", unique=True)
    _users().create_index("api_key", unique=True)


def create_user(username, password, api_key, role="user", daily_limit=20):
    now = datetime.now(timezone.utc)
    doc = {
        "username": username,
        "password": hash_password(password),
        "api_key": api_key,
        "created_at": now,
        "last_used": None,
        "today_usage": 0,
        "usage_date": now.date().isoformat(),
        "total_usage": 0,
        "remaining_usage": daily_limit,
        "is_blocked": False,
        "failed_attempts": 0,
        "role": role,
    }
    try:
        _users().insert_one(doc)
        return doc
    except DuplicateKeyError:
        return None


def get_user_by_username(username):
    return _users().find_one({"username": username})


def get_user_by_api(api_key):
    return _users().find_one({"api_key": api_key})


def get_user_by_id(user_id):
    return _users().find_one({"_id": user_id})


def verify_user_password(user, password):
    if not user:
        return False
    return verify_password(password, user["password"])


def update_usage(user_id):
    from app.services.usage_service import get_daily_limit_for_user, reset_daily_usage_if_needed

    user = _users().find_one({"_id": user_id})
    if not user:
        return None

    daily_limit = get_daily_limit_for_user(user)
    user = reset_daily_usage_if_needed(user, daily_limit)

    updated = _users().find_one_and_update(
        {"_id": user_id},
        {
            "$inc": {"today_usage": 1, "total_usage": 1},
            "$set": {
                "last_used": datetime.now(timezone.utc),
                "remaining_usage": max(0, daily_limit - (user["today_usage"] + 1)),
            },
        },
        return_document=ReturnDocument.AFTER,
    )
    return updated


def block_user(username, block=True):
    return _users().find_one_and_update(
        {"username": username},
        {"$set": {"is_blocked": bool(block)}},
        return_document=ReturnDocument.AFTER,
    )


def ensure_admin_user(username, password, api_key, daily_limit=50):
    existing = get_user_by_username(username)
    if existing:
        if existing.get("role") != "admin":
            _users().update_one({"_id": existing["_id"]}, {"$set": {"role": "admin"}})
        return get_user_by_username(username)

    return create_user(
        username=username,
        password=password,
        api_key=api_key,
        role="admin",
        daily_limit=daily_limit,
    )
