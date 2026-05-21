from flask import Flask
from dotenv import load_dotenv
import os

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-in-production")
    app.config["DATABASE"] = os.path.join(app.instance_path, "pm_chat.db")
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["PERMANENT_SESSION_LIFETIME"] = 86400 * 7

    os.makedirs(app.instance_path, exist_ok=True)

    from app.database import init_db
    from app.routes import bp

    init_db(app)
    app.register_blueprint(bp)

    return app
