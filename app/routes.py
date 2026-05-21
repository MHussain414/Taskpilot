import json
import os
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, Response
from app import tasks as task_svc
from app.activity import log_activity, list_activity as list_activity_log
from app.tasks import normalize_deadline
from app.ai_engine import (
    process_chat, build_progress_stats, explain_priority, priority_label,
)
from app.auth import login_required, login_user, logout_user, validate_credentials, current_user
from app.brand import APP_NAME, APP_TAGLINE, APP_SHORT_DESC, APP_COPYRIGHT, APP_VERSION, APP_EVENT

bp = Blueprint("main", __name__)


def _brand_context():
    return {
        "app_name": APP_NAME,
        "app_tagline": APP_TAGLINE,
        "app_short_desc": APP_SHORT_DESC,
        "app_copyright": APP_COPYRIGHT,
        "app_version": APP_VERSION,
        "app_event": APP_EVENT,
    }


def _display_user(email: str) -> str:
    """Show a professional label in the header (not the raw email)."""
    if not email:
        return "Team Member"
    lowered = email.lower()
    if any(x in lowered for x in ("hacker", "overflow", "test@", "demo@")):
        return "Project Manager"
    local = email.split("@")[0].replace(".", " ").replace("_", " ")
    return local.title() if local else "Team Member"


def _welcome_name(email: str) -> str:
    """First name for the welcome banner highlight."""
    label = _display_user(email)
    first = label.split()[0] if label else "there"
    return first if first else "there"

MAX_TEAM = 8


def _actor():
    return _display_user(current_user()), current_user() or ""


@bp.route("/login/", methods=["GET", "POST"])
@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user():
        return redirect(url_for("main.index"))
    error = None
    if request.method == "POST":
        email = request.form.get("email", "")
        password = request.form.get("password", "")
        if validate_credentials(email, password):
            login_user(email)
            return redirect(url_for("main.index"))
        error = "Invalid email or password."
    return render_template("login.html", error=error, **_brand_context())


@bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.login"))


@bp.route("/")
@login_required
def index():
    return render_template(
        "index.html",
        user=_display_user(current_user()),
        welcome_name=_welcome_name(current_user()),
        **_brand_context(),
    )


@bp.route("/api/tasks", methods=["GET"])
@login_required
def api_list_tasks():
    return jsonify({"tasks": task_svc.list_tasks()})


@bp.route("/api/tasks", methods=["POST"])
@login_required
def api_create_task():
    data = request.get_json() or {}
    if not data.get("title", "").strip():
        return jsonify({"error": "Title is required"}), 400
    task = task_svc.create_task(
        title=data["title"],
        description=data.get("description", ""),
        status=data.get("status", "todo"),
        deadline=normalize_deadline(data.get("deadline")),
        effort_hours=data.get("effort_hours", 4),
        tags=data.get("tags", ""),
        assignee=data.get("assignee", ""),
    )
    name, email = _actor()
    log_activity(name, email, "created_task", task["title"], task["id"])
    return jsonify({"task": task}), 201


@bp.route("/api/tasks/<int:task_id>", methods=["GET"])
@login_required
def api_get_task(task_id):
    task = task_svc.get_task(task_id)
    if not task:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"task": task, "explanation": explain_priority(task)})


@bp.route("/api/tasks/<int:task_id>", methods=["PATCH"])
@login_required
def api_update_task(task_id):
    data = request.get_json() or {}
    payload = dict(data)
    if "deadline" in payload:
        payload["deadline"] = normalize_deadline(payload.get("deadline"))
    old = task_svc.get_task(task_id)
    task = task_svc.update_task(task_id, **payload)
    if not task:
        return jsonify({"error": "Not found"}), 404
    name, email = _actor()
    if old and old.get("status") != task.get("status"):
        log_activity(
            name, email, "updated_status",
            f"Task #{task_id} → {task['status'].replace('_', ' ')}", task_id,
        )
    else:
        log_activity(name, email, "updated_task", task["title"], task_id)
    return jsonify({"task": task})


@bp.route("/api/tasks/<int:task_id>", methods=["DELETE"])
@login_required
def api_delete_task(task_id):
    old = task_svc.get_task(task_id)
    task_svc.delete_task(task_id)
    name, email = _actor()
    log_activity(name, email, "deleted_task", old["title"] if old else f"#{task_id}", task_id)
    return jsonify({"ok": True})


@bp.route("/api/tasks/recalculate", methods=["POST"])
@login_required
def api_recalculate():
    return jsonify({"tasks": task_svc.recalculate_all()})


@bp.route("/api/tasks/apply-suggestions", methods=["POST"])
@login_required
def api_apply_suggestions():
    count = task_svc.apply_ai_suggestions()
    return jsonify({"updated": count, "tasks": task_svc.list_tasks()})


@bp.route("/api/dashboard", methods=["GET"])
@login_required
def api_dashboard():
    tasks = task_svc.list_tasks()
    stats = build_progress_stats(tasks)
    by_priority = {
        "critical": [t for t in tasks if t.get("priority_score", 0) >= 75],
        "high": [t for t in tasks if 55 <= t.get("priority_score", 0) < 75],
        "medium": [t for t in tasks if 35 <= t.get("priority_score", 0) < 55],
        "low": [t for t in tasks if t.get("priority_score", 0) < 35],
    }
    return jsonify({
        "stats": stats,
        "by_priority": by_priority,
        "tasks": tasks,
    })


@bp.route("/api/health", methods=["GET"])
def api_health():
    return jsonify({"status": "ok", "app": APP_NAME})


@bp.route("/api/config", methods=["GET"])
@login_required
def api_config():
    key = os.getenv("OPENAI_API_KEY", "").strip()
    return jsonify({
        "app": APP_NAME,
        "openai_configured": bool(key),
        "openai_model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "ai_mode": "gpt" if key else "built-in",
    })


@bp.route("/api/chat", methods=["POST"])
@login_required
def api_chat():
    try:
        data = request.get_json(silent=True) or {}
        message = (data.get("message") or "").strip()
        if not message:
            return jsonify({"error": "Message required"}), 400

        task_svc.save_chat("user", message)
        all_tasks = task_svc.list_tasks()
        team_members = task_svc.list_team()
        reply, action = process_chat(
            message,
            all_tasks,
            team_members=team_members,
            user_name=_display_user(current_user()),
        )

        if action and action.get("type"):
            from app.ai_engine import execute_chat_action
            suffix, all_tasks = execute_chat_action(action, task_svc)
            reply += suffix

        task_svc.save_chat("assistant", reply)
        return jsonify({
            "reply": reply,
            "tasks": all_tasks,
            "stats": build_progress_stats(all_tasks),
            "meta": action,
        })
    except Exception as exc:
        return jsonify({"error": f"Assistant error: {exc}"}), 500


@bp.route("/api/chat/history", methods=["GET"])
@login_required
def api_chat_history():
    return jsonify({"messages": task_svc.get_chat_history()})


@bp.route("/api/team", methods=["GET"])
@login_required
def api_team():
    members = task_svc.list_team()
    return jsonify({
        "members": members,
        "occupied": len(members),
        "max": MAX_TEAM,
    })


@bp.route("/api/team", methods=["POST"])
@login_required
def api_add_team():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Name required"}), 400
    members = task_svc.list_team()
    if len(members) >= MAX_TEAM:
        return jsonify({"error": f"Team full ({MAX_TEAM}/{MAX_TEAM})"}), 400
    ok, err = task_svc.add_team_member(name, data.get("role", "member"))
    if not ok:
        return jsonify({"error": err or "Could not add member"}), 400
    aname, aemail = _actor()
    log_activity(aname, aemail, "team_join", f"{name} joined as {data.get('role', 'member')}")
    return jsonify({"members": task_svc.list_team()}), 201


@bp.route("/api/team/<int:member_id>", methods=["DELETE"])
@login_required
def api_remove_team(member_id):
    members = task_svc.list_team()
    removed = next((m for m in members if m["id"] == member_id), None)
    task_svc.remove_team_member(member_id)
    aname, aemail = _actor()
    log_activity(aname, aemail, "team_leave", removed["name"] if removed else f"member #{member_id}")
    return jsonify({"members": task_svc.list_team()})


@bp.route("/api/team/messages", methods=["GET"])
@login_required
def api_team_messages():
    since = request.args.get("since", type=int) or 0
    messages = task_svc.list_team_messages(since_id=since) if since else task_svc.list_team_messages()
    return jsonify({
        "messages": messages,
        "latest_id": task_svc.latest_team_message_id(),
    })


@bp.route("/api/team/messages", methods=["POST"])
@login_required
def api_team_message_post():
    data = request.get_json() or {}
    content = (data.get("content") or "").strip()
    if not content:
        return jsonify({"error": "Message required"}), 400
    if len(content) > 2000:
        return jsonify({"error": "Message too long (max 2000 characters)"}), 400
    sender = _display_user(current_user())
    email = current_user() or ""
    task_svc.save_team_message(sender, email, content)
    log_activity(sender, email, "team_message", content[:120])
    return jsonify({
        "messages": task_svc.list_team_messages(),
        "latest_id": task_svc.latest_team_message_id(),
    }), 201


@bp.route("/api/seed-demo", methods=["POST"])
@login_required
def api_seed_demo():
    data = request.get_json(silent=True) or {}
    replace = bool(data.get("replace", True))
    existing = task_svc.list_tasks()
    if existing and not replace:
        return jsonify({
            "message": "Tasks already exist. Click Demo Data again to replace with samples.",
            "tasks": existing,
            "replaced": False,
        })
    if existing and replace:
        task_svc.clear_all_tasks()
    samples = [
        ("Design chat UI mockups", "High-fidelity Figma screens for dark theme", "in_progress", 3, "urgent"),
        ("Implement priority scoring engine", "Deadline + keyword + status algorithm", "todo", 5, "critical"),
        ("Write README and documentation", "Setup guide for judges", "todo", 7, ""),
        ("Record 5-minute demo video", "Voice-over walkthrough of features", "todo", 10, ""),
        ("Integrate team slot management", "0/8 occupied display", "done", 2, ""),
    ]
    from datetime import datetime, timedelta
    today = datetime.utcnow().date()
    for title, desc, status, days, _extra in samples:
        dl = (today + timedelta(days=days)).isoformat() if days else None
        task_svc.create_task(title, desc, status=status, deadline=dl,
                             effort_hours=4 if status != "done" else 2)
    task_svc.recalculate_all()
    tasks = task_svc.list_tasks()
    aname, aemail = _actor()
    log_activity(aname, aemail, "demo_data", f"Loaded {len(tasks)} sample tasks")
    return jsonify({
        "message": f"Loaded {len(tasks)} demo tasks. Open the Dashboard tab for charts.",
        "tasks": tasks,
        "replaced": bool(existing),
        "stats": build_progress_stats(tasks),
    })


@bp.route("/api/activity", methods=["GET"])
@login_required
def api_activity():
    return jsonify({"activity": list_activity_log(80)})


@bp.route("/api/tasks/export", methods=["GET"])
@login_required
def api_export_tasks():
    fmt = (request.args.get("format") or "json").lower()
    tasks = task_svc.list_tasks()
    if fmt == "csv":
        body = task_svc.tasks_to_csv(tasks)
        return Response(
            body,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=taskpilot_tasks.csv"},
        )
    return Response(
        json.dumps({"tasks": tasks}, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment; filename=taskpilot_tasks.json"},
    )


@bp.route("/api/openapi.json", methods=["GET"])
def api_openapi():
    spec = {
        "openapi": "3.0.3",
        "info": {"title": APP_NAME, "version": APP_VERSION, "description": APP_TAGLINE},
        "paths": {
            "/api/health": {"get": {"summary": "Health check"}},
            "/api/tasks": {"get": {"summary": "List tasks"}, "post": {"summary": "Create task"}},
            "/api/tasks/{id}": {
                "patch": {"summary": "Update task"},
                "delete": {"summary": "Delete task"},
            },
            "/api/chat": {"post": {"summary": "AI assistant message"}},
            "/api/dashboard": {"get": {"summary": "Dashboard stats"}},
            "/api/team": {"get": {"summary": "Team members"}, "post": {"summary": "Add member"}},
            "/api/team/messages": {"get": {"summary": "Team chat"}, "post": {"summary": "Post message"}},
            "/api/activity": {"get": {"summary": "Activity log"}},
            "/api/tasks/export": {"get": {"summary": "Export tasks JSON/CSV"}},
        },
    }
    return jsonify(spec)


@bp.route("/api/docs")
def api_docs():
    return render_template("api_docs.html", app_name=APP_NAME, **_brand_context())


@bp.route("/api/priority/<int:task_id>", methods=["GET"])
@login_required
def api_priority_explain(task_id):
    task = task_svc.get_task(task_id)
    if not task:
        return jsonify({"error": "Not found"}), 404
    return jsonify({
        "task": task,
        "label": priority_label(task["priority_score"]),
        "explanation": explain_priority(task),
    })
