import io

from flask import Blueprint, g, jsonify, send_file

from app.models.user_model import update_usage
from app.services.bg_remove import remove_background
from app.services.usage_service import get_daily_limit_for_user
from app.utils.decorators import auth_required, rate_limit_per_user

api_bp = Blueprint("api", __name__)


@api_bp.route("/v1/remove-bg", methods=["POST"])
@auth_required(api_mode=True, enforce_usage=True)
@rate_limit_per_user
def remove_bg():
    from flask import request

    if "image" not in request.files:
        return jsonify({"error": "No image file provided."}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "Empty filename."}), 400

    try:
        output = remove_background(file.read())
    except Exception as exc:
        return jsonify({"error": f"Background removal failed: {exc}"}), 500

    updated = update_usage(user_id=g.current_user["_id"])
    daily_limit = get_daily_limit_for_user(g.current_user)

    response = send_file(io.BytesIO(output), mimetype="image/png")
    response.headers["X-Usage-Used"] = str(updated.get("today_usage", 0))
    response.headers["X-Usage-Limit"] = str(daily_limit)
    response.headers["X-Remaining-Usage"] = str(updated.get("remaining_usage", 0))
    return response
