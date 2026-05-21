# Architecture — AI Project Management Chat Module

## Overview

A three-layer web application:

```
┌─────────────────────────────────────────┐
│  Browser GUI (HTML/CSS/JS)              │
│  Chat · Task Board · Dashboard · Team   │
└─────────────────┬───────────────────────┘
                  │ REST JSON
┌─────────────────▼───────────────────────┐
│  Flask API (routes.py)                  │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│  Services: tasks.py                     │
│  AI Engine: ai_engine.py                │
│  SQLite: instance/pm_chat.db            │
└─────────────────────────────────────────┘
```

## Priority Scoring Algorithm

Each task receives a score from **0 to 100** (higher = more urgent). The algorithm is transparent and explainable for judges.

### Factors

1. **Base score** — 40 points starting value  
2. **Keyword analysis** — `urgent`, `critical`, `blocker` increase score; `low`, `optional` decrease  
3. **Deadline proximity** — Overdue (+35), due today (+30), ≤2 days (+25), ≤7 days (+15)  
4. **Status** — `blocked` (+20), `in_progress` (+10), `done` (reduced)  
5. **Effort** — Small tasks (+5), very large tasks (−5)  

### AI Suggestions

- **Suggested deadline** — Derived from priority score and effort hours  
- **Apply suggestions** — One-click to set deadlines on tasks missing them  

### Labels

| Score | Label |
|-------|-------|
| ≥ 75 | Critical |
| ≥ 55 | High |
| ≥ 35 | Medium |
| < 35 | Low |

## Chat Processing

1. User message saved to `chat_messages`  
2. If `OPENAI_API_KEY` is set → GPT response with task context  
3. Else → rule-based parser handles create/update/list/priority commands  
4. Actions (create task, update status) executed automatically  
5. Assistant reply saved and returned with updated tasks/stats  

## Data Model

### tasks

- id, title, description, status, priority_score  
- suggested_deadline, deadline, effort_hours  
- tags, assignee, timestamps  

### chat_messages

- role (user/assistant), content, timestamp  

### team_members

- name (unique), role, joined_at — max 8 per competition constraint  

## Security Notes

- Change `FLASK_SECRET_KEY` before production  
- Do not commit `.env` with real API keys  
- App binds to localhost by default  
