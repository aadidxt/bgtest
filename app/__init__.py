import os

from flask import Flask, current_app
from flask_cors import CORS
from flask_pymongo import PyMongo

from config import Config

import certifi
mongo = PyMongo(tlsCAFile=certifi.where(), tlsAllowInvalidCertificates=True)


def get_db():
    return mongo.cx[current_app.config["MONGO_DB_NAME"]]


def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
        static_url_path="/static",
    )
    app.config.from_object(Config)
    print("SECURE COOKIE:", app.config["SESSION_COOKIE_SECURE"])
    print("TYPE:", type(app.config["SESSION_COOKIE_SECURE"]))
    print("REPR:", repr(app.config["SESSION_COOKIE_SECURE"]))
    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY is required.")
    if not app.config.get("MONGO_URI"):
        raise RuntimeError("MONGO_URI is required.")

    mongo.init_app(app)
    CORS(app)

    from app.models.user_model import ensure_admin_user, ensure_indexes
    from app.utils.security import generate_api_key
    from app.routes.admin_routes import admin_bp
    from app.routes.api_routes import api_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.main_routes import main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(admin_bp)

    with app.app_context():
        ensure_indexes()
        admin_username = os.getenv("ADMIN_USERNAME")
        admin_password = os.getenv("ADMIN_PASSWORD")
        if admin_username and admin_password:
            ensure_admin_user(
                username=admin_username,
                password=admin_password,
                api_key=generate_api_key(),
                daily_limit=app.config["ADMIN_DAILY_USAGE_LIMIT"],
            )

    return app
