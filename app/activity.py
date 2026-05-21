"""Project activity audit log."""
from app.database import get_db, row_to_dict, now_iso


def log_activity(actor_name: str, actor_email: str, action: str, detail: str = "", task_id=None):
    db = get_db()
    db.execute(
        """INSERT INTO activity_log (actor_name, actor_email, action, detail, task_id, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            (actor_name or "System").strip(),
            (actor_email or "").strip(),
            action.strip(),
            (detail or "").strip()[:500],
            task_id,
            now_iso(),
        ),
    )
    db.commit()


def list_activity(limit: int = 50):
    db = get_db()
    rows = db.execute(
        "SELECT * FROM activity_log ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    return [row_to_dict(r) for r in reversed(rows)]
