from datetime import datetime
from app.database import get_db, row_to_dict, now_iso
from app.ai_engine import calculate_priority_score, suggest_deadline


def normalize_deadline(value) -> str | None:
    """Normalize to YYYY-MM-DD for HTML date input and SQLite."""
    if value is None or value == "":
        return None
    text = str(value).strip()[:10]
    try:
        datetime.strptime(text, "%Y-%m-%d")
        return text
    except ValueError:
        return None


def list_tasks():
    db = get_db()
    rows = db.execute(
        "SELECT * FROM tasks ORDER BY priority_score DESC, created_at DESC"
    ).fetchall()
    return [row_to_dict(r) for r in rows]


def get_task(task_id: int):
    db = get_db()
    row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return row_to_dict(row)


def _apply_scores(data: dict) -> dict:
    score = calculate_priority_score(data)
    data["priority_score"] = score
    if not data.get("suggested_deadline") and data.get("status") != "done":
        data["suggested_deadline"] = suggest_deadline(data)
    return data


def create_task(title, description="", status="todo", deadline=None,
                effort_hours=4.0, tags="", assignee=""):
    ts = now_iso()
    data = {
        "title": title.strip(),
        "description": description.strip(),
        "status": status,
        "deadline": normalize_deadline(deadline),
        "effort_hours": float(effort_hours),
        "tags": tags,
        "assignee": assignee,
        "suggested_deadline": None,
        "created_at": ts,
        "updated_at": ts,
    }
    data = _apply_scores(data)
    db = get_db()
    cur = db.execute(
        """INSERT INTO tasks (
            title, description, status, priority_score, suggested_deadline,
            deadline, effort_hours, tags, assignee, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            data["title"], data["description"], data["status"],
            data["priority_score"], data["suggested_deadline"],
            data["deadline"], data["effort_hours"], data["tags"],
            data["assignee"], data["created_at"], data["updated_at"],
        ),
    )
    db.commit()
    return get_task(cur.lastrowid)


def update_task(task_id: int, **kwargs):
    task = get_task(task_id)
    if not task:
        return None
    allowed = {"title", "description", "status", "deadline", "effort_hours",
               "tags", "assignee", "suggested_deadline"}
    for key, value in kwargs.items():
        if key not in allowed:
            continue
        if key == "deadline":
            task[key] = normalize_deadline(value)
        elif value is not None:
            task[key] = value
    task["updated_at"] = now_iso()
    task = _apply_scores(task)
    db = get_db()
    db.execute(
        """UPDATE tasks SET
            title=?, description=?, status=?, priority_score=?,
            suggested_deadline=?, deadline=?, effort_hours=?, tags=?,
            assignee=?, updated_at=?
        WHERE id=?""",
        (
            task["title"], task["description"], task["status"],
            task["priority_score"], task["suggested_deadline"],
            task["deadline"], task["effort_hours"], task["tags"],
            task["assignee"], task["updated_at"], task_id,
        ),
    )
    db.commit()
    return get_task(task_id)


def delete_task(task_id: int):
    db = get_db()
    db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    db.commit()
    return True


def clear_all_tasks():
    db = get_db()
    db.execute("DELETE FROM tasks")
    db.commit()


def recalculate_all():
    tasks = list_tasks()
    for t in tasks:
        update_task(t["id"])
    return list_tasks()


def apply_ai_suggestions():
    """Apply suggested deadlines to tasks missing deadlines."""
    updated = 0
    for t in list_tasks():
        if t["status"] != "done" and not t.get("deadline") and t.get("suggested_deadline"):
            update_task(t["id"], deadline=t["suggested_deadline"])
            updated += 1
    return updated


def save_chat(role: str, content: str):
    db = get_db()
    db.execute(
        "INSERT INTO chat_messages (role, content, created_at) VALUES (?, ?, ?)",
        (role, content, now_iso()),
    )
    db.commit()


def get_chat_history(limit=50):
    db = get_db()
    rows = db.execute(
        "SELECT * FROM chat_messages ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    return [row_to_dict(r) for r in reversed(rows)]


def list_team():
    db = get_db()
    rows = db.execute("SELECT * FROM team_members ORDER BY joined_at").fetchall()
    return [row_to_dict(r) for r in rows]


def add_team_member(name: str, role: str = "member"):
    db = get_db()
    try:
        db.execute(
            "INSERT INTO team_members (name, role, joined_at) VALUES (?, ?, ?)",
            (name.strip(), role, now_iso()),
        )
        db.commit()
        return True, None
    except Exception as e:
        return False, str(e)


def remove_team_member(member_id: int):
    db = get_db()
    db.execute("DELETE FROM team_members WHERE id = ?", (member_id,))
    db.commit()


def list_team_messages(limit: int = 100, since_id: int = 0):
    db = get_db()
    if since_id:
        rows = db.execute(
            "SELECT * FROM team_messages WHERE id > ? ORDER BY id ASC LIMIT ?",
            (since_id, limit),
        ).fetchall()
        return [row_to_dict(r) for r in rows]
    rows = db.execute(
        "SELECT * FROM team_messages ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    return [row_to_dict(r) for r in reversed(rows)]


def latest_team_message_id() -> int:
    db = get_db()
    row = db.execute("SELECT MAX(id) AS mid FROM team_messages").fetchone()
    return int(row["mid"] or 0) if row else 0


def tasks_to_csv(tasks: list) -> str:
    import csv
    import io
    buf = io.StringIO()
    fields = [
        "id", "title", "description", "status", "priority_score",
        "deadline", "suggested_deadline", "effort_hours", "assignee", "tags",
    ]
    writer = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for t in tasks:
        writer.writerow({k: t.get(k, "") for k in fields})
    return buf.getvalue()


def save_team_message(sender_name: str, sender_email: str, content: str):
    db = get_db()
    db.execute(
        "INSERT INTO team_messages (sender_name, sender_email, content, created_at) "
        "VALUES (?, ?, ?, ?)",
        (sender_name.strip(), (sender_email or "").strip(), content.strip(), now_iso()),
    )
    db.commit()
