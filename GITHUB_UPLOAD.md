# Upload TaskPilot to GitHub (MHussain414)

Your project is **ready locally** — git initialized, professional README, report, CI, and Docker included.

## Step 1 — Create empty repo on GitHub

1. Open https://github.com/new  
2. **Repository name:** `TaskPilot`  
3. **Description:** `AI Project Management Chat Module — Flask, AI priority engine, Kanban, team chat`  
4. Choose **Public**  
5. **Do NOT** add README, .gitignore, or license (already in project)  
6. Click **Create repository**

## Step 2 — Push from your PC

Open **PowerShell** in the project folder:

```powershell
cd "D:\competiton project 2026"

git remote add origin https://github.com/MHussain414/Taskpilot.git
git push -u origin main
```

If `origin` already exists:

```powershell
git remote set-url origin https://github.com/MHussain414/Taskpilot.git
git push -u origin main
```

Sign in with GitHub when prompted (browser or token).

## Step 3 — Verify on GitHub

Your repo should show the same structure as ThreatGuard:

| Item | In repo |
|------|---------|
| `.github/workflows/` | CI tests |
| `app/` | Flask + GUI |
| `docs/` | Architecture + **TaskPilot_Report.pdf** |
| `tests/` | pytest |
| `FINAL_REPORT.md` | Report summary |
| `README.md` | Professional landing page |
| `CONTRIBUTING.md` | ✓ |
| `LICENSE` | MIT |
| `Makefile` | ✓ |
| `Dockerfile` | ✓ |

## Optional — Pin repository

GitHub profile → **Customize your pins** → pin **TaskPilot**.

## Optional — Enable Actions

After push, open **Actions** tab — CI should run automatically on `main`.

## Demo video

Edit `README.md` and `FINAL_REPORT.md` — replace:

`https://youtu.be/YOUR_VIDEO_ID`

with your real YouTube link after recording.

---

**Already committed locally:** branch `main`, 46+ files, report PDF in `docs/TaskPilot_Report.pdf`.
