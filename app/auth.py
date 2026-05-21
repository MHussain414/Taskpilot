from functools import wraps
from flask import session, redirect, url_for, request, jsonify
import os


def login_user(email: str):
    session["user"] = email
    session.permanent = True


def logout_user():
    session.pop("user", None)


def current_user():
    return session.get("user")


def validate_credentials(email: str, password: str) -> bool:
    """Demo auth: any non-empty login, or match .env defaults."""
    if not email.strip() or not password:
        return False
    demo_email = os.getenv("DEMO_EMAIL", "").strip()
    demo_pass = os.getenv("DEMO_PASSWORD", "").strip()
    if demo_email and demo_pass:
        return email.strip().lower() == demo_email.lower() and password == demo_pass
    return True


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user():
            return view(*args, **kwargs)
        if request.path.startswith("/api/"):
            return jsonify({"error": "Unauthorized"}), 401
        return redirect(url_for("main.login"))
    return wrapped
