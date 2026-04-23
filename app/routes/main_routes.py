from flask import Blueprint, g, jsonify, redirect, render_template, session, url_for
from app.services.usage_service import get_daily_limit_for_user, reset_daily_usage_if_needed
from app.utils.decorators import auth_required

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    if session.get("username"):
        return redirect(url_for("main.index"))
    return redirect(url_for("auth.login"))


@main_bp.route("/app")
@auth_required(api_mode=False, enforce_usage=False)
def index():
    user = g.current_user
    user = reset_daily_usage_if_needed(user, daily_limit=get_daily_limit_for_user(user))
    return render_template("index.html", user=user)


@main_bp.route("/me")
@auth_required(api_mode=True, enforce_usage=False)
def me():
    user = g.current_user
    user = reset_daily_usage_if_needed(user, daily_limit=get_daily_limit_for_user(user))
    return jsonify(
        {
            "username": user["username"],
            "api_key": user["api_key"],
            "today_usage": user.get("today_usage", 0),
            "total_usage": user.get("total_usage", 0),
            "remaining_usage": user.get("remaining_usage", 0),
            "role": user.get("role", "user"),
            "is_blocked": user.get("is_blocked", False),
        }
    )
