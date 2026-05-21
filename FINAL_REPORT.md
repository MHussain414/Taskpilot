# TaskPilot — Final Technical Report (Submission)

**Project:** TaskPilot — AI Project Management Chat Module  
**Event:** AI App Development Competition 2026  
**Repository:** [github.com/MHussain414/Taskpilot](https://github.com/MHussain414/Taskpilot)

---

## Executive Summary

TaskPilot delivers a **complete localhost web application** that satisfies the competition brief: chat-based interface, task management, AI priority scoring, progress dashboard, and team collaboration (max 8 members). The system uses **Python 3**, **Flask 3**, **SQLite**, and a modern browser GUI with optional **OpenAI** enhancement.

---

## Deliverables Checklist

| Item | Location |
|------|----------|
| Source code | `app/`, `run.py` |
| README & setup | `README.md`, `.env.example`, `requirements.txt` |
| Technical report (PDF) | **[docs/TaskPilot_Report.pdf](docs/TaskPilot_Report.pdf)** |
| Architecture | `docs/ARCHITECTURE.md` |
| API documentation | `/api/docs`, `/api/openapi.json` |
| Automated tests | `tests/test_app.py`, `.github/workflows/ci.yml` |
| Docker deployment | `Dockerfile`, `docker-compose.yml` |

---

## Core Requirements Mapping

| Requirement | Implementation |
|-------------|----------------|
| Chat-based interface | AI Assistant panel + REST `/api/chat` |
| Task management | CRUD, search, Kanban, list view |
| Priority scoring (AI) | `ai_engine.py` — 0–100 score, explainable |
| Progress dashboard | Charts, stats, priority queue |
| Team collaboration | 8 slots, team chat, activity log |
| Localhost GUI | `http://127.0.0.1:5000` |

---

## Extended Features (Portfolio)

- Kanban drag-and-drop board  
- Activity audit log  
- Team chat with `@mentions` and polling notifications  
- Export tasks (JSON/CSV)  
- Dark/light theme  
- Full Q&A chatbot knowledge base  
- GitHub Actions CI + pytest + Docker  

---

## How to Run

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python run.py
```

Open **http://127.0.0.1:5000/login/**

---

## Demo Video

_Add your 5-minute screen recording link here after upload:_

`https://youtu.be/________________`

---

## Full Report

The detailed 13+ page report with diagrams, API tables, and installation guide is in:

**[docs/TaskPilot_Report.pdf](docs/TaskPilot_Report.pdf)**

LaTeX source for regeneration: `docs/report/TaskPilot_Report.tex`  
Build: `bash scripts/build-report-pdf.sh` (requires TeX Live / WSL)

---

*© 2026 TaskPilot — AI App Development Competition submission.*
