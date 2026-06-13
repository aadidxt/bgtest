from collections import defaultdict, deque
from datetime import datetime, timezone
from functools import wraps
from threading import Lock

from flask import current_app, g, jsonify

from app import DEFAULT_USER

_rate_limit_data = defaultdict(deque)
_rate_lock = Lock()


def auth_required(api_mode=False, enforce_usage=True):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            g.current_user = DEFAULT_USER
            return func(*args, **kwargs)
        return wrapper
    return decorator


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        g.current_user = DEFAULT_USER
        return func(*args, **kwargs)
    return wrapper


def rate_limit_per_user(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = getattr(g, "current_user", None)
        if not user:
            return jsonify({"error": "Authentication required"}), 401

        if user.get("role") == "admin":
            return func(*args, **kwargs)

        max_calls = current_app.config["RATE_LIMIT_PER_MINUTE"]
        now = datetime.now(timezone.utc).timestamp()
        window_start = now - 60
        key = str(user["_id"])

        with _rate_lock:
            calls = _rate_limit_data[key]
            while calls and calls[0] < window_start:
                calls.popleft()
            if len(calls) >= max_calls:
                return jsonify({"error": "Rate limit exceeded"}), 429
            calls.append(now)

        return func(*args, **kwargs)

    return wrapper
