from flask import Flask
from dotenv import load_dotenv
import os

load_dotenv()


def _database_path(app):
    """Use /tmp on Vercel serverless (writable); instance/ locally."""
    override = os.getenv("DATABASE_PATH", "").strip()
    if override:
        return override
    if os.getenv("VERCEL"):
        return "/tmp/pm_chat.db"
    return os.path.join(app.instance_path, "pm_chat.db")


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-in-production")
    app.config["DATABASE"] = _database_path(app)
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["PERMANENT_SESSION_LIFETIME"] = 86400 * 7
    on_vercel = bool(os.getenv("VERCEL"))
    app.config["SESSION_COOKIE_SECURE"] = on_vercel or os.getenv("FLASK_ENV") == "production"

    db_dir = os.path.dirname(app.config["DATABASE"])
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    os.makedirs(app.instance_path, exist_ok=True)

    from app.database import init_db
    from app.routes import bp

    init_db(app)
    app.register_blueprint(bp)

    return app
