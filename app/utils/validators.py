import re


def valid_username(username):
    if not username:
        return False
    return bool(re.fullmatch(r"[A-Za-z0-9_]{3,30}", username))


def valid_password(password):
    if not password:
        return False
    return len(password) >= 6
