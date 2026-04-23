from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.services.auth_service import authenticate_user, register_user
from app.services.usage_service import clear_failed_attempts
from app.utils.validators import valid_password, valid_username

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not valid_username(username):
            flash("Username must be 3-30 chars: letters, numbers, underscore.")
            return render_template("signup.html")
        if not valid_password(password):
            flash("Password must be at least 6 characters.")
            return render_template("signup.html")

        user = register_user(username, password)
        if not user:
            flash("Username already exists.")
            return render_template("signup.html")

        session["username"] = user["username"]
        return redirect(url_for("main.index"))

    return render_template("signup.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = authenticate_user(username, password)
        if not user:
            flash("Invalid username or password.")
            return render_template("login.html")
        if user.get("is_blocked"):
            flash("Your account is blocked.")
            return render_template("login.html")

        session["username"] = user["username"]
        clear_failed_attempts(user["_id"])
        return redirect(url_for("main.index"))

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
