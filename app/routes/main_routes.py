from flask import Blueprint, g, jsonify, redirect, render_template, url_for
from app.utils.decorators import auth_required

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    return redirect(url_for("main.index"))


@main_bp.route("/app")
@auth_required(api_mode=False, enforce_usage=False)
def index():
    return render_template("index.html", user=g.current_user)


@main_bp.route("/me")
@auth_required(api_mode=True, enforce_usage=False)
def me():
    user = g.current_user
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
