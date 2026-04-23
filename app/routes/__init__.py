from .admin_routes import admin_bp
from .api_routes import api_bp
from .auth_routes import auth_bp
from .main_routes import main_bp

__all__ = ["auth_bp", "main_bp", "api_bp", "admin_bp"]
