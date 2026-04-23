import secrets

import bcrypt


def hash_password(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def generate_api_key():
    return f"bg_{secrets.token_urlsafe(24)}"
