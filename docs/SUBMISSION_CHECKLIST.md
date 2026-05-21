# Competition Submission Checklist

Based on **AI_App_Dev_Instructions.pdf** — verify before final GitHub upload (4:00–5:00 PM).

## Required Deliverables

- [x] **README.md** — project overview, features, setup
- [x] **requirements.txt** — Python dependencies
- [x] **Setup & Run Guide** — in README (venv, pip, python run.py)
- [x] **Clean folder structure** — `app/`, `docs/`, `static/`, `templates/`
- [x] **.env / .env.example** — environment configuration
- [ ] **GitHub repository** — `git init`, commit, push (team action)
- [x] **Documentation** — `docs/ARCHITECTURE.md`
- [x] **GitHub Actions CI** — `.github/workflows/ci.yml` + pytest
- [x] **Docker** — `Dockerfile`, `docker-compose.yml`
- [x] **Portfolio features** — Kanban, activity log, export, team chat, theme toggle, OpenAPI
- [ ] **5-minute screen recording** — voice-over demo (team action)

## Demo Recording Tips

1. Start server: `python run.py`
2. Open http://127.0.0.1:5000
3. Click **Demo Data**
4. Show chat: `add task`, `top priorities`, `dashboard`
5. Show task board + **AI Suggest Deadlines**
6. Open **Dashboard** tab — charts and priority queue
7. Open **Team** tab — add member, show X/8 occupied
8. Briefly explain priority algorithm (deadline + keywords + status)

## Evaluation Points to Highlight

- **Concept understanding:** AI assists PM — not just a todo list
- **Implementation:** Working GUI on localhost, persistent SQLite
- **Approach:** Transparent scoring + optional OpenAI enhancement
- **Teamwork:** Team slots mirror competition constraint (max 8)
