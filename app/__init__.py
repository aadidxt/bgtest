from flask import Flask
from flask_cors import CORS

from config import Config


DEFAULT_USER = {
    "_id": "local",
    "username": "User",
    "api_key": "local",
    "role": "user",
    "today_usage": 0,
    "total_usage": 0,
    "remaining_usage": 99999,
    "is_blocked": False,
    "usage_date": "",
}


def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
        static_url_path="/static",
    )
    app.config.from_object(Config)
    CORS(app)

    from app.routes.api_routes import api_bp
    from app.routes.main_routes import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    return app
