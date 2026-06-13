from app import DEFAULT_USER


def get_daily_limit_for_user(user):
    return 99999


def reset_daily_usage_if_needed(user, daily_limit):
    return user


def can_use_feature(user):
    return True, user, None
