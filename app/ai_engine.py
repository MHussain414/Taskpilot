"""
AI Priority Scoring & Chat Assistant Engine.

Priority algorithm considers: deadline proximity, status, effort, keywords,
and workload balance. Rule-based commands run first so actions always work;
optional OpenAI handles open-ended conversation.
"""
import json
import os
import re
from datetime import datetime, timedelta
from typing import Optional

URGENCY_KEYWORDS = {
    "critical": 30, "urgent": 25, "asap": 25, "blocker": 28,
    "high": 15, "important": 12, "soon": 10,
    "low": -10, "minor": -12, "optional": -15,
}


def parse_deadline(text: str) -> Optional[str]:
    text = text.lower()
    today = datetime.utcnow().date()
    if "today" in text:
        return today.isoformat()
    if "tomorrow" in text:
        return (today + timedelta(days=1)).isoformat()
    if "next week" in text:
        return (today + timedelta(days=7)).isoformat()
    if "friday" in text:
        days = (4 - today.weekday()) % 7 or 7
        return (today + timedelta(days=days)).isoformat()
    match = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    match = re.search(r"(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?", text)
    if match:
        d, m = int(match.group(1)), int(match.group(2))
        y = int(match.group(3)) if match.group(3) else today.year
        if y < 100:
            y += 2000
        try:
            return datetime(y, m, d).date().isoformat()
        except ValueError:
            pass
    return None


def keyword_boost(text: str) -> float:
    text = text.lower()
    return sum(v for word, v in URGENCY_KEYWORDS.items() if word in text)


def days_until(deadline_str: Optional[str]) -> Optional[float]:
    if not deadline_str:
        return None
    try:
        deadline = datetime.fromisoformat(deadline_str.replace("Z", "")).date()
        return (deadline - datetime.utcnow().date()).days
    except ValueError:
        return None


def calculate_priority_score(task: dict) -> float:
    score = 40.0
    combined = f"{task.get('title', '')} {task.get('description', '')}"
    score += keyword_boost(combined)

    deadline = task.get("deadline") or task.get("suggested_deadline")
    days = days_until(deadline)
    if days is not None:
        if days < 0:
            score += 35
        elif days == 0:
            score += 30
        elif days <= 2:
            score += 25
        elif days <= 7:
            score += 15
        elif days <= 14:
            score += 8
        else:
            score -= 5

    status = task.get("status", "todo")
    if status == "blocked":
        score += 20
    elif status == "in_progress":
        score += 10
    elif status == "done":
        score = max(5, score - 40)

    effort = float(task.get("effort_hours") or 4)
    if effort <= 2:
        score += 5
    elif effort >= 16:
        score -= 5

    return round(min(100, max(0, score)), 1)


def suggest_deadline(task: dict) -> str:
    score = task.get("priority_score", 50)
    if score >= 75:
        days = 2
    elif score >= 55:
        days = 5
    elif score >= 35:
        days = 10
    else:
        days = 14
    effort = float(task.get("effort_hours") or 4)
    days = min(21, days + int(effort // 8))
    return (datetime.utcnow().date() + timedelta(days=days)).isoformat()


def priority_label(score: float) -> str:
    if score >= 75:
        return "Critical"
    if score >= 55:
        return "High"
    if score >= 35:
        return "Medium"
    return "Low"


def explain_priority(task: dict) -> str:
    score = task.get("priority_score", 0)
    label = priority_label(score)
    parts = [f"**{label}** priority (score {score}/100)."]
    deadline = task.get("deadline") or task.get("suggested_deadline")
    days = days_until(deadline)
    if days is not None:
        if days < 0:
            parts.append(f"Deadline was {abs(days)} day(s) ago — overdue.")
        elif days == 0:
            parts.append("Due today.")
        else:
            parts.append(f"Due in {days} day(s).")
    if keyword_boost(f"{task.get('title', '')} {task.get('description', '')}") > 0:
        parts.append("Urgency keywords detected in title/description.")
    if task.get("status") == "blocked":
        parts.append("Task is blocked — escalated priority.")
    suggested = task.get("suggested_deadline")
    if suggested and not task.get("deadline"):
        parts.append(f"Suggested deadline: {suggested}.")
    return " ".join(parts)


def build_progress_stats(tasks: list) -> dict:
    total = len(tasks)
    if total == 0:
        return {
            "total": 0, "done": 0, "in_progress": 0, "todo": 0, "blocked": 0,
            "completion_pct": 0, "avg_priority": 0,
            "critical_count": 0, "high_count": 0,
        }
    done = sum(1 for t in tasks if t["status"] == "done")
    in_prog = sum(1 for t in tasks if t["status"] == "in_progress")
    todo = sum(1 for t in tasks if t["status"] == "todo")
    blocked = sum(1 for t in tasks if t["status"] == "blocked")
    scores = [t.get("priority_score", 0) for t in tasks if t["status"] != "done"]
    avg = round(sum(scores) / len(scores), 1) if scores else 0
    return {
        "total": total,
        "done": done,
        "in_progress": in_prog,
        "todo": todo,
        "blocked": blocked,
        "completion_pct": round(100 * done / total, 1),
        "avg_priority": avg,
        "critical_count": sum(1 for t in tasks if t.get("priority_score", 0) >= 75),
        "high_count": sum(1 for t in tasks if 55 <= t.get("priority_score", 0) < 75),
    }


def _clean_task_title(raw: str) -> str:
    title = raw.strip()
    for phrase in [
        " urgent", " critical", " high priority", " low priority",
        " due tomorrow", " due today", " due next week", " due friday",
    ]:
        title = re.sub(re.escape(phrase), "", title, flags=re.I).strip()
    title = re.sub(r"\bdue\s+\d{1,2}[/-]\d{1,2}.*$", "", title, flags=re.I).strip()
    return title[:200] or "New task"


def _parse_create_task(message: str, msg_lower: str) -> Optional[dict]:
    patterns = [
        r"(?:add|create|new)\s+task\s*[:\-]?\s*(.+)",
        r"(?:add|create)\s+(.+)",
    ]
    raw = None
    for pat in patterns:
        m = re.search(pat, message, re.I)
        if m:
            raw = m.group(1).strip()
            break
    if not raw or len(raw) < 2:
        return None
    if raw.lower() in ("task", "a task", "new task"):
        return None
    title = _clean_task_title(raw)
    deadline = parse_deadline(raw)
    effort = 8.0 if any(w in msg_lower for w in ("large", "big", "major")) else (
        2.0 if any(w in msg_lower for w in ("quick", "small", "minor")) else 4.0
    )
    return {
        "type": "create_task",
        "title": title,
        "description": raw,
        "deadline": deadline,
        "effort_hours": effort,
    }


def _parse_status_update(msg_lower: str) -> Optional[dict]:
    status_map = {
        "done": "done", "complete": "done", "completed": "done", "finish": "done",
        "todo": "todo", "pending": "todo",
        "in progress": "in_progress", "in_progress": "in_progress", "progress": "in_progress",
        "blocked": "blocked", "block": "blocked",
    }
    patterns = [
        r"(?:mark|set|update|change)\s+task\s*#?(\d+)\s+(?:as\s+|to\s+)?([a-z_\s]+)",
        r"(?:mark|set|update|change)\s+task\s*#?(\d+)\s+(done|todo|blocked)",
        r"(?:complete|finish|close)\s+task\s*#?(\d+)",
        r"task\s*#?(\d+)\s+(?:is\s+)?(done|complete|completed|in progress|blocked|todo)",
    ]
    for pat in patterns:
        m = re.search(pat, msg_lower)
        if not m:
            continue
        tid = int(m.group(1))
        if len(m.groups()) >= 2:
            status_raw = m.group(2).strip().replace(" ", "_")
            status = status_map.get(status_raw.replace("_", " "), status_map.get(status_raw, status_raw))
        else:
            status = "done"
        if status in ("done", "todo", "in_progress", "blocked"):
            return {"type": "update_status", "task_id": tid, "status": status}
    return None


def rule_based_chat(message: str, tasks: list) -> tuple[str, Optional[dict]]:
    msg = message.strip().lower()
    action = None

    if "dashboard" in msg or msg in ("progress", "stats", "status report"):
        stats = build_progress_stats(tasks)
        return (
            f"**Project Progress**\n"
            f"• Completion: **{stats['completion_pct']}%** ({stats['done']}/{stats['total']} done)\n"
            f"• In progress: {stats['in_progress']} | Todo: {stats['todo']} | Blocked: {stats['blocked']}\n"
            f"• Avg active priority: {stats['avg_priority']}\n"
            f"• Critical: {stats['critical_count']} | High: {stats['high_count']}",
            {"highlight": "dashboard"},
        )

    if any(p in msg for p in ("top priorit", "most urgent", "what should i work", "what to do first")):
        active = [t for t in tasks if t["status"] != "done"]
        active.sort(key=lambda x: x.get("priority_score", 0), reverse=True)
        if not active:
            return "No active tasks. Say: `add task Your first task urgent`", None
        lines = ["**Top priorities:**"]
        for i, t in enumerate(active[:5], 1):
            lines.append(
                f"{i}. [{t['id']}] {t['title']} — {priority_label(t['priority_score'])} "
                f"({t['priority_score']})"
            )
        return "\n".join(lines), {"highlight": "tasks"}

    if any(p in msg for p in ("apply suggest", "apply deadline", "suggest deadline", "auto deadline")):
        count = sum(1 for t in tasks if t["status"] != "done" and not t.get("deadline"))
        if count == 0:
            return "All active tasks already have deadlines.", None
        return f"Applying AI-suggested deadlines to **{count}** task(s)...", {"type": "apply_suggestions"}

    delete_match = re.search(r"(?:delete|remove)\s+task\s*#?(\d+)", msg)
    if delete_match:
        tid = int(delete_match.group(1))
        return f"Deleting task **#{tid}**...", {"type": "delete_task", "task_id": tid}

    status_action = _parse_status_update(msg)
    if status_action:
        tid = status_action["task_id"]
        st = status_action["status"].replace("_", " ")
        return f"Updating task #{tid} to **{st}**.", status_action

    why_match = re.search(r"(?:why|explain).*(?:task\s*)?#?(\d+)", msg)
    if why_match:
        tid = int(why_match.group(1))
        task = next((t for t in tasks if t["id"] == tid), None)
        if task:
            return explain_priority(task), {"task_id": tid}
        return f"Task #{tid} not found.", None

    create_action = _parse_create_task(message, msg)
    if create_action:
        title = create_action["title"]
        reply = f"Creating task **{title}**"
        if create_action.get("deadline"):
            reply += f" (deadline: {create_action['deadline']})"
        reply += "."
        return reply, create_action

    if any(p in msg for p in ("show task", "list task", "all task", "my task")) or msg in ("tasks", "list"):
        if not tasks:
            return "No tasks yet. Try: `add task Design homepage due next week`", None
        lines = ["**All tasks:**"]
        for t in sorted(tasks, key=lambda x: -x.get("priority_score", 0)):
            st = t["status"].replace("_", " ")
            lines.append(
                f"• [{t['id']}] {t['title']} — {priority_label(t['priority_score'])} | {st}"
            )
        return "\n".join(lines), {"highlight": "tasks"}

    recalc_match = msg in ("recalculate", "recalculate priorities", "refresh priorities")
    if recalc_match:
        return "Recalculating priority scores for all tasks...", {"type": "recalculate"}

    return None, None


def try_openai_chat(message: str, tasks: list, system_context: str) -> Optional[str]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        task_summary = json.dumps(
            [
                {
                    "id": t["id"],
                    "title": t["title"],
                    "status": t["status"],
                    "priority": t.get("priority_score"),
                    "deadline": t.get("deadline") or t.get("suggested_deadline"),
                }
                for t in tasks[:25]
            ],
            indent=2,
        )
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        system_context
                        + "\n\nCurrent tasks JSON:\n"
                        + task_summary
                        + "\n\nFor actionable requests (create/update tasks), tell the user "
                        "the exact command syntax they can type."
                    ),
                },
                {"role": "user", "content": message},
            ],
            max_tokens=600,
            temperature=0.5,
        )
        return response.choices[0].message.content
    except Exception:
        return None


def process_chat(
    message: str,
    tasks: list,
    team_members: Optional[list] = None,
    user_name: str = "",
) -> tuple[str, Optional[dict]]:
    """Commands first, then full Q&A knowledge base, then optional OpenAI."""
    from app.chat_knowledge import answer_general_question, smart_fallback

    reply, action = rule_based_chat(message, tasks)
    if action:
        return reply, action

    if reply:
        return reply, action

    qa = answer_general_question(message, tasks, team_members, user_name)
    if qa:
        return qa, None

    system = (
        "You are TaskPilot, an AI project management assistant. Answer ANY question clearly "
        "and completely: product features, tasks, priorities, deadlines, dashboard, team "
        "collaboration, team chat, installation, and competition demo. Be friendly and thorough. "
        "If the user wants to change tasks, include the exact chat command syntax."
    )
    ai_reply = try_openai_chat(message, tasks, system)
    if ai_reply:
        return ai_reply, None

    return smart_fallback(message, tasks, team_members or []), None


def execute_chat_action(action: dict, task_svc) -> tuple[str, list]:
    """Run action from chat parser; returns extra message suffix and updated task list."""
    extra = ""
    if action["type"] == "create_task":
        task_svc.create_task(
            title=action["title"],
            description=action.get("description", ""),
            deadline=action.get("deadline"),
            effort_hours=action.get("effort_hours", 4),
        )
        extra = "\n\n✓ Task created and prioritized."
    elif action["type"] == "update_status":
        updated = task_svc.update_task(action["task_id"], status=action["status"])
        if updated:
            extra = f"\n\n✓ Task #{action['task_id']} is now **{action['status'].replace('_', ' ')}**."
        else:
            extra = f"\n\n✗ Task #{action['task_id']} not found."
    elif action["type"] == "delete_task":
        task_svc.delete_task(action["task_id"])
        extra = f"\n\n✓ Task #{action['task_id']} deleted."
    elif action["type"] == "apply_suggestions":
        n = task_svc.apply_ai_suggestions()
        task_svc.recalculate_all()
        extra = f"\n\n✓ Applied suggested deadlines to **{n}** task(s)."
    elif action["type"] == "recalculate":
        task_svc.recalculate_all()
        extra = "\n\n✓ Priority scores recalculated."
    return extra, task_svc.list_tasks()
