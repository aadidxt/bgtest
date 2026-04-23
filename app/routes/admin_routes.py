from flask import Blueprint, redirect, render_template, request, url_for

from app import get_db
from app.models.user_model import block_user
from app.utils.decorators import admin_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin", methods=["GET"])
@admin_required
def admin_dashboard():
    users = list(get_db().users.find({}).sort("created_at", -1))
    return render_template("admin.html", users=users)


@admin_bp.route("/admin/toggle-block/<username>", methods=["POST"])
@admin_required
def toggle_block(username):
    user = get_db().users.find_one({"username": username})
    if user:
        block_user(username, block=not user.get("is_blocked", False))
    return redirect(url_for("admin.admin_dashboard"))
