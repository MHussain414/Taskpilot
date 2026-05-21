# TaskPilot — AI Project Management Chat Module

![TaskPilot](https://img.shields.io/badge/TaskPilot-AI%20PM%20Chat-7c5cff?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=flat-square&logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Persistence-003B57?style=flat-square)
![CI](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)

> **Enterprise-style AI project management** — conversational task control, explainable priority scoring, Kanban board, team chat, activity audit log, and live analytics dashboard.

**Competition:** AI App Development Event 2026 · **Author:** [MHussain414](https://github.com/MHussain414)

[Features](#-features) • [Quick Start](#-quick-start) • [Demo](#-5-minute-demo-script) • [Architecture](#-architecture) • [Documentation](#-documentation) • [Report](#-technical-report)

---

## 🎯 Project Overview

**TaskPilot** is a full-stack **AI Project Management Chat Module** built for team-based coordination on **localhost**. It combines a natural-language AI assistant, structured task management, a transparent **0–100 priority engine**, visual progress dashboards, and **team collaboration** (8 slots + real-time team chat).

This project demonstrates:

- ✅ **Chat-first workflow** — create, prioritize, and track work through conversation  
- ✅ **Explainable AI scoring** — deadline, keywords, status, and effort drive priority  
- ✅ **Production-quality GUI** — dark/light theme, Kanban, export, professional footer  
- ✅ **Team operations** — roster, `@mentions`, activity log, message polling  
- ✅ **DevOps readiness** — pytest, GitHub Actions CI, Docker, OpenAPI  

📄 **Full technical report:** [docs/TaskPilot_Report.pdf](docs/TaskPilot_Report.pdf) · [FINAL_REPORT.md](FINAL_REPORT.md)

---

## ✨ Features

### AI & Task Management

| Feature | Description |
|---------|-------------|
| ✅ **AI Chat Assistant** | Rule-based commands + optional OpenAI GPT; full Q&A knowledge base |
| ✅ **Task CRUD** | List/board views, search, filters, modal editor, deadline quick-picks |
| ✅ **Priority Engine** | Multi-factor score → Critical / High / Medium / Low + explain API |
| ✅ **Kanban Board** | Drag-and-drop columns: Todo · In Progress · Blocked · Done |
| ✅ **Progress Dashboard** | Completion %, donut chart, status bars, priority queue |
| ✅ **Demo Data** | One-click sample tasks for judges and demos |

### Team & Collaboration

| Feature | Description |
|---------|-------------|
| ✅ **Team Slots (0/8)** | Roles: Member, Lead, Developer, Designer |
| ✅ **Team Chat** | Shared channel with `@mentions` and live toast notifications |
| ✅ **Activity Log** | Audit trail: task changes, demo load, team events |
| ✅ **Export** | Download tasks as **JSON** or **CSV** |

### Developer Experience

| Feature | Description |
|---------|-------------|
| ✅ **REST API** | JSON endpoints for tasks, chat, dashboard, team |
| ✅ **OpenAPI** | `/api/openapi.json` + `/api/docs` |
| ✅ **pytest** | Automated API tests |
| ✅ **Docker** | `docker compose up --build` |

---

## 🚀 Quick Start

### Prerequisites

- Python **3.10+**
- pip

### Windows

```powershell
git clone https://github.com/MHussain414/TaskPilot.git
cd TaskPilot
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python run.py
```

Open **http://127.0.0.1:5000/login/** — demo mode accepts any email/password.

### Docker

```bash
docker compose up --build
```

### Tests

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/ -v
```

---

## 🎬 5-Minute Demo Script

1. **Login** → click **Demo Data**  
2. **Workspace** — chat: `top priorities`, `help`, `add task … urgent due tomorrow`  
3. **Kanban** — drag a task to *In Progress*  
4. **Dashboard** — charts + **Activity Log**  
5. **Team** — add member, post `@Name` message, show **Export** / **API**  

> Add your screen recording URL here: `https://youtu.be/YOUR_VIDEO_ID`

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              Client (Browser — TaskPilot GUI)                    │
│     Workspace │ Dashboard │ Team + Chat │ Kanban │ Theme        │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP + Session cookies
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Flask Application Layer                       │
│  routes.py │ auth.py │ ai_engine.py │ chat_knowledge.py          │
│  tasks.py  │ activity.py │ brand.py                              │
└────────────────────────────┬────────────────────────────────────┘
                             │ SQL
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     SQLite (instance/pm_chat.db)                   │
│   tasks │ chat_messages │ team_members │ team_messages │ activity  │
└─────────────────────────────────────────────────────────────────┘

Optional: OPENAI_API_KEY → GPT-enhanced chat replies
```

**AI message flow:** User message → rule-based parser (actions) → knowledge base Q&A → optional OpenAI → GUI refresh.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for algorithm details.

---

## 📁 Repository Structure

```
TaskPilot/
├── .github/workflows/     # CI (pytest)
├── app/                   # Flask backend + static GUI
│   ├── ai_engine.py       # Priority scoring + chat
│   ├── chat_knowledge.py  # Full Q&A without OpenAI
│   ├── activity.py        # Audit log
│   ├── routes.py          # REST API
│   └── static/            # CSS, JS, templates
├── docs/
│   ├── ARCHITECTURE.md
│   ├── TaskPilot_Report.pdf   # Competition technical report
│   └── SUBMISSION_CHECKLIST.md
├── tests/                 # pytest suite
├── scripts/               # test_api, package, build PDF
├── FINAL_REPORT.md
├── Dockerfile
├── docker-compose.yml
├── Makefile
└── run.py
```

---

## 📡 API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET/POST | `/api/tasks` | List / create tasks |
| GET | `/api/tasks/export?format=json\|csv` | Export |
| POST | `/api/chat` | AI assistant |
| GET | `/api/dashboard` | Analytics |
| GET | `/api/activity` | Activity log |
| GET/POST | `/api/team/messages` | Team chat (`?since=id`) |
| GET | `/api/openapi.json` | OpenAPI 3 spec |
| GET | `/api/docs` | API documentation page |

---

## ⚙ Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_PORT` | `5000` | Server port |
| `FLASK_SECRET_KEY` | dev | Session secret |
| `OPENAI_API_KEY` | _(empty)_ | Optional GPT chat |
| `DEMO_EMAIL` / `DEMO_PASSWORD` | _(empty)_ | Restrict login |

Copy `.env.example` → `.env`.

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design & priority algorithm |
| [docs/TaskPilot_Report.pdf](docs/TaskPilot_Report.pdf) | Full competition technical report (PDF) |
| [FINAL_REPORT.md](FINAL_REPORT.md) | Report summary & submission notes |
| [SETUP-FOR-RECIPIENT.md](SETUP-FOR-RECIPIENT.md) | Setup for new machines |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guidelines |

---

## 📋 Technical Report

The complete **TaskPilot Technical Report** (competition submission) is included as:

- **PDF:** [docs/TaskPilot_Report.pdf](docs/TaskPilot_Report.pdf)  
- **Summary:** [FINAL_REPORT.md](FINAL_REPORT.md)  
- **LaTeX source:** `docs/report/TaskPilot_Report.tex`

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

## 📄 License

MIT License — see [LICENSE](LICENSE). Built for educational / competition use.

---

<p align="center">
  <strong>TaskPilot</strong> — Plan smarter. Ship faster.<br>
  <sub>AI App Development Competition 2026</sub>
</p>
