"""
Comprehensive Q&A for TaskPilot assistant (works without OpenAI).
Answers general questions about the app, tasks, team, priorities, and how-to.
"""
import re
from typing import Optional

from app.ai_engine import (
    build_progress_stats,
    explain_priority,
    priority_label,
)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower().strip())


def _word_match(msg: str, *phrases: str) -> bool:
    return any(p in msg for p in phrases)


def _task_by_id(tasks: list, tid: int):
    return next((t for t in tasks if t["id"] == tid), None)


# FAQ: (trigger phrases, answer) — order matters for overlapping topics
FAQ_ENTRIES = [
    (
        ("what is taskpilot", "what is this app", "about taskpilot", "what does this do"),
        "**TaskPilot** is an AI Project Management Chat Module. You manage tasks through "
        "conversation, get automatic **priority scores (0–100)**, view a **progress dashboard**, "
        "and collaborate with your **team** (up to 8 members) including **team chat**.",
    ),
    (
        ("how do i login", "how to login", "sign in", "password"),
        "Open **http://127.0.0.1:5000/login/** — demo mode accepts **any email and password**. "
        "Optional: set `DEMO_EMAIL` and `DEMO_PASSWORD` in `.env` to restrict access.",
    ),
    (
        ("how to add task", "how do i add", "create a task", "new task"),
        "• Chat: `add task Fix login bug urgent due tomorrow`\n"
        "• UI: click **+ New Task** on the task board\n"
        "• API: `POST /api/tasks` with JSON body",
    ),
    (
        ("how to delete", "remove task", "delete task"),
        "• Chat: `delete task 3` (use the task ID number)\n"
        "• UI: open the task card and click **Delete**",
    ),
    (
        ("how to update", "change status", "mark done", "complete task"),
        "• Chat: `mark task 2 as done` · `complete task 1` · `set task 3 in progress`\n"
        "• UI: click **Edit** on a task and change **Status**",
    ),
    (
        ("priority score", "how priority works", "scoring algorithm", "why priority"),
        "Priority uses **deadline proximity**, **urgency keywords** (urgent, critical, blocker), "
        "**status** (blocked > in progress > todo), and **effort hours**. "
        "Score 0–100 → **Critical** (75+), **High** (55–74), **Medium** (35–54), **Low** (<35). "
        "Ask: `why is task 2 high priority` for a specific explanation.",
    ),
    (
        ("demo data", "sample tasks", "load demo"),
        "Click **Demo Data** in the header. It loads 5 sample tasks (replaces existing tasks "
        "after you confirm). Great for judges and first-time demos.",
    ),
    (
        ("dashboard", "progress chart", "completion", "statistics"),
        "Open the **Dashboard** tab for completion %, donut chart, status bars, "
        "priority distribution, and top active tasks. "
        "Or ask in chat: `dashboard` or `progress`.",
    ),
    (
        ("team chat", "team message", "communicate", "talk to team", "message team"),
        "Go to the **Team** tab → **Team Chat** panel. Everyone on the project sees the same "
        "messages in real time (refresh when you open the tab). Add members in **Team Slots** first, "
        "then coordinate tasks and deadlines together.",
    ),
    (
        ("team member", "join team", "add member", "team slots", "how many team"),
        "**Team** tab → enter name + role → **Join Team**. Maximum **8** slots shown as `N / 8 Occupied`. "
        "Roles: Member, Lead, Developer, Designer.",
    ),
    (
        ("openai", "gpt", "api key", "smarter ai"),
        "Add `OPENAI_API_KEY` in `.env` and restart the server. The badge switches to **GPT**. "
        "All task commands still work with the **built-in** engine if you skip OpenAI.",
    ),
    (
        ("deadline", "due date", "suggest deadline"),
        "Set deadlines in the task editor or say `due tomorrow` in chat. "
        "Use **AI Suggest** on the board or `apply suggested deadlines` in chat. "
        "Quick picks: Today, Tomorrow, +7 days.",
    ),
    (
        ("recalculate", "refresh priority"),
        "Click **Recalculate** on the task board or say `recalculate` in chat to re-score all tasks.",
    ),
    (
        ("list tasks", "show tasks", "all tasks", "my tasks"),
        "Say `show tasks` or `list tasks` in chat, or view the **Task Board** in Workspace.",
    ),
    (
        ("top priorit", "what to work", "most urgent"),
        "Say `top priorities` in chat for the top 5 active tasks by AI score.",
    ),
    (
        ("help", "commands", "what can you", "what do you do", "features"),
        None,  # filled by help_text()
    ),
    (
        ("install", "run server", "how to start", "python run"),
        "```\npython -m venv venv\nvenv\\Scripts\\activate   # Windows\npip install -r requirements.txt\ncopy .env.example .env\npython run.py\n```\n"
        "Then open **http://127.0.0.1:5000/login/**",
    ),
    (
        ("port", "5000", "flask port"),
        "Default port is **5000**. Change `FLASK_PORT` in `.env` if the port is busy, then restart.",
    ),
    (
        ("blocked", "stuck task"),
        "**Blocked** status raises priority (+20). Use when a task cannot proceed until something else is resolved.",
    ),
    (
        ("assignee", "who owns", "assigned to"),
        "Set **Assignee** in the task editor or mention a name in the description. "
        "Team chat helps coordinate who is working on what.",
    ),
    (
        ("report", "documentation", "readme"),
        "See `README.md`, `docs/ARCHITECTURE.md`, and **TaskPilot_Report.pdf** in the project folder.",
    ),
    (
        ("competition", "submission", "judge"),
        "Submission includes: localhost GUI, README, requirements.txt, .env.example, "
        "technical report PDF, and optional 5-minute demo video.",
    ),
]


def help_text() -> str:
    return (
        "I'm **TaskPilot AI** — ask me anything about this project:\n\n"
        "**Tasks:** add, list, delete, update status, deadlines, priorities\n"
        "**Analytics:** dashboard, progress %, top priorities\n"
        "**Team:** members, roles, **team chat** (Team tab)\n"
        "**How-to:** login, demo data, OpenAI, install, ports\n"
        "**Explain:** `why is task 3 high priority`\n\n"
        "Example questions:\n"
        "• What is TaskPilot?\n"
        "• How do I add a task?\n"
        "• How does priority scoring work?\n"
        "• How do team members communicate?\n"
        "• Show my tasks / dashboard / top priorities"
    )


def match_faq(message: str) -> Optional[str]:
    msg = _norm(message)
    best_score = 0
    best_answer = None
    for triggers, answer in FAQ_ENTRIES:
        score = sum(1 for t in triggers if t in msg)
        if score > best_score:
            best_score = score
            if answer is None and "help" in str(triggers):
                best_answer = help_text()
            else:
                best_answer = answer
    if best_score >= 1 and best_answer:
        return best_answer
    return None


def contextual_answer(message: str, tasks: list, team_members: list, user_name: str) -> Optional[str]:
    """Answer from live project data when the question mentions counts, IDs, or team."""
    msg = _norm(message)

    if _word_match(msg, "how many task", "number of task", "count task", "total task"):
        s = build_progress_stats(tasks)
        return (
            f"You have **{s['total']}** tasks: **{s['done']}** done, **{s['in_progress']}** in progress, "
            f"**{s['todo']}** todo, **{s['blocked']}** blocked. Completion: **{s['completion_pct']}%**."
        )

    if _word_match(msg, "how many team", "team size", "who is on", "team members", "list team"):
        if not team_members:
            return "No team members yet. Open the **Team** tab and click **Join Team**."
        lines = ["**Team members:**"]
        for m in team_members:
            lines.append(f"• **{m['name']}** — {m['role']}")
        lines.append("\nUse **Team Chat** in the same tab to message everyone.")
        return "\n".join(lines)

    tid_match = re.search(r"task\s*#?(\d+)", msg)
    if tid_match and _word_match(msg, "when", "deadline", "due", "what is task", "tell me about"):
        tid = int(tid_match.group(1))
        task = _task_by_id(tasks, tid)
        if not task:
            return f"Task **#{tid}** was not found."
        dl = task.get("deadline") or task.get("suggested_deadline") or "not set"
        return (
            f"**Task #{tid}:** {task['title']}\n"
            f"• Status: {task['status'].replace('_', ' ')}\n"
            f"• Priority: {priority_label(task['priority_score'])} ({task['priority_score']})\n"
            f"• Deadline: {dl}\n"
            f"• Assignee: {task.get('assignee') or '—'}"
        )

    if _word_match(msg, "who am i", "my name", "logged in"):
        return f"You are signed in as **{user_name or 'Team Member'}**. Messages in team chat use this name."

    if _word_match(msg, "thank", "thanks"):
        return "You're welcome! Ask anytime — tasks, dashboard, team chat, or how-to questions."

    if _word_match(msg, "hi", "hello", "hey", "good morning", "good afternoon"):
        return (
            f"Hello **{user_name or 'there'}**! I'm your TaskPilot assistant. "
            "Ask me anything — type **help** for a full topic list."
        )

    # Question words without a match — give guided answer
    if re.match(r"^(what|how|why|when|where|who|can|does|is|are|will)\b", msg):
        return (
            "Here's what I can tell you about:\n"
            "• **TaskPilot** features and login\n"
            "• **Creating and managing** tasks & deadlines\n"
            "• **Priority scores** and dashboard\n"
            "• **Team slots** and **team chat**\n"
            "• **Demo data**, OpenAI, and running the server\n\n"
            "Try a specific question, e.g. *How does priority scoring work?* or type **help**."
        )

    return None


def answer_general_question(
    message: str,
    tasks: list,
    team_members: Optional[list] = None,
    user_name: str = "",
) -> Optional[str]:
    """Try FAQ then contextual answers."""
    team_members = team_members or []
    hit = match_faq(message)
    if hit:
        return hit
    return contextual_answer(message, tasks, team_members, user_name)


def smart_fallback(message: str, tasks: list, team_members: list) -> str:
    """Last resort without OpenAI — still helpful, not a dead end."""
    msg = _norm(message)
    hints = []
    if "task" in msg:
        hints.append("`show tasks` · `add task …` · `top priorities`")
    if "team" in msg:
        hints.append("**Team** tab for members + **Team Chat**")
    if "chart" in msg or "graph" in msg:
        hints.append("**Dashboard** tab for charts")
    extra = "\n".join(f"• {h}" for h in hints) if hints else help_text()
    return (
        f"I understood your question about: *{message.strip()[:120]}*\n\n"
        "I don't have a exact canned answer for that phrase, but try:\n"
        f"{extra}\n\n"
        "For open-ended answers, add **OPENAI_API_KEY** in `.env` (optional)."
    )
