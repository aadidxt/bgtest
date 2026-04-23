from flask import current_app

from app.models.user_model import create_user, get_user_by_username, verify_user_password
from app.utils.security import generate_api_key


def register_user(username, password, role="user"):
    api_key = generate_api_key()
    return create_user(
        username=username,
        password=password,
        api_key=api_key,
        role=role,
        daily_limit=current_app.config["USER_DAILY_USAGE_LIMIT"],
    )


def authenticate_user(username, password):
    user = get_user_by_username(username)
    if not verify_user_password(user, password):
        return None
    return user
