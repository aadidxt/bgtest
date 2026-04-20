from flask import Blueprint, request, send_file, jsonify
import io
from app.services.bg_remove import remove_background
from app.auth import validate_api_key

api = Blueprint("api", __name__)


def require_api_key():
    api_key = request.headers.get("x-api-key")
    if not api_key or not validate_api_key(api_key):
        return jsonify({"error": "Invalid API Key"}), 401
    return None


@api.route("/v1/remove-bg", methods=["POST"])
def remove_bg():
    auth_error = require_api_key()
    if auth_error:
        return auth_error

    if "image" not in request.files:
        return jsonify({"error": "No file"}), 400

    file = request.files["image"]
    input_bytes = file.read()

    try:
        output = remove_background(input_bytes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    response = send_file(io.BytesIO(output), mimetype="image/png")
    return response
