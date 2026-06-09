from collections import defaultdict, deque
from datetime import datetime, timezone
from functools import wraps
from threading import Lock

from flask import current_app, g, jsonify, redirect, request, session, url_for

from app.models.user_model import get_user_by_api, get_user_by_username
from app.services.usage_service import can_use_feature, increment_failed_attempts

_rate_limit_data = defaultdict(deque)
_rate_lock = Lock()


def _resolve_user():
    print("SESSION:", dict(session))
    username = session.get("username")
    if username:
        print("USERNAME:", username)
        return get_user_by_username(username)

    api_key = request.headers.get("x-api-key", "").strip()
    if not api_key:
        return None
    return get_user_by_api(api_key)


def auth_required(api_mode=False, enforce_usage=True):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user = _resolve_user()
            if not user:
                if api_mode:
                    return jsonify({"error": "Authentication required"}), 401
                return redirect(url_for("auth.login"))

            # If session-authenticated user also sends a wrong API key, treat it as a failed attempt.
            provided_key = request.headers.get("x-api-key", "").strip()
            if session.get("username") and provided_key and provided_key != user.get("api_key"):
                user = increment_failed_attempts(user)
                return jsonify({"error": "Invalid API key"}), 401

            if user.get("is_blocked"):
                if api_mode:
                    return jsonify({"error": "User is blocked"}), 403
                session.clear()
                return redirect(url_for("auth.login"))

            # Admins bypass usage limits
            if enforce_usage and user.get("role") != "admin":
                allowed, refreshed_user, error = can_use_feature(user)
                if not allowed:
                    if api_mode:
                        return jsonify({"error": error}), 429
                    return redirect(url_for("auth.login"))
                user = refreshed_user

            g.current_user = user
            return func(*args, **kwargs)

        return wrapper

    return decorator


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = _resolve_user()
        if not user:
            return redirect(url_for("auth.login"))
        if user.get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        g.current_user = user
        return func(*args, **kwargs)

    return wrapper


def rate_limit_per_user(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = getattr(g, "current_user", None)
        if not user:
            return jsonify({"error": "Authentication required"}), 401

        # Admins bypass rate limits
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
