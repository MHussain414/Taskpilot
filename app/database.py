import sqlite3
from datetime import datetime
from flask import g, current_app


def get_db():
    if "db" not in g:
        path = current_app.config["DATABASE"]
        if path.startswith("file:"):
            g.db = sqlite3.connect(path, uri=True, check_same_thread=False)
        else:
            g.db = sqlite3.connect(path, check_same_thread=False)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        db = get_db()
        db.executescript("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                status TEXT DEFAULT 'todo' CHECK(status IN ('todo', 'in_progress', 'done', 'blocked')),
                priority_score REAL DEFAULT 50.0,
                suggested_deadline TEXT,
                deadline TEXT,
                effort_hours REAL DEFAULT 4.0,
                tags TEXT DEFAULT '',
                assignee TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS team_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                role TEXT DEFAULT 'member',
                joined_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS team_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_name TEXT NOT NULL,
                sender_email TEXT DEFAULT '',
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                actor_name TEXT NOT NULL,
                actor_email TEXT DEFAULT '',
                action TEXT NOT NULL,
                detail TEXT DEFAULT '',
                task_id INTEGER,
                created_at TEXT NOT NULL
            );
        """)
        db.commit()


def row_to_dict(row):
    if row is None:
        return None
    return dict(row)


def now_iso():
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
