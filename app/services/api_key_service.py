from app.models.user_model import get_user_by_api


def resolve_user_by_api_key(api_key):
    if not api_key:
        return None
    return get_user_by_api(api_key)
