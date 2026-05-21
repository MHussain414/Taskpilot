# How to Send TaskPilot to Someone Else

## Option A — ZIP file (easiest)

1. Run the packaging script (creates a clean zip without secrets or huge folders):

   **Windows PowerShell:**
   ```powershell
   cd "D:\competiton project 2026"
   .\scripts\package-for-sharing.ps1
   ```

2. You will get: **`TaskPilot-share.zip`** in the project folder.

3. Send that zip via:
   - WhatsApp / email (if size allows)
   - Google Drive, OneDrive, Dropbox
   - USB drive

4. Tell the recipient to read **`SETUP-FOR-RECIPIENT.md`** inside the zip.

**Project report (PDF):** `TaskPilot_Report.pdf` — full functionality documentation (also in `docs/report/`).

---

## Option B — GitHub

1. Create a new repo on GitHub (private or public).

2. In the project folder:
   ```powershell
   cd "D:\competiton project 2026"
   git init
   git add .
   git commit -m "TaskPilot - AI Project Management Chat Module"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/taskpilot.git
   git push -u origin main
   ```

3. Share the repo link. They clone and follow `README.md`.

**Never commit `.env`** (API keys). Only `.env.example` is included.

---

## What is NOT included (on purpose)

| Excluded | Why |
|----------|-----|
| `venv/` | They create their own virtual environment |
| `.env` | Your secrets (OpenAI key, etc.) |
| `instance/*.db` | Your local task database |
| `__pycache__/` | Auto-generated Python cache |

---

## What to tell the recipient

> 1. Unzip the folder  
> 2. Install Python 3.10+  
> 3. Open terminal in the folder  
> 4. Run: `python -m venv venv` then activate venv  
> 5. Run: `pip install -r requirements.txt`  
> 6. Copy `.env.example` to `.env`  
> 7. Run: `python run.py`  
> 8. Open: http://127.0.0.1:5000/login/  
> 9. Sign in with any email/password (demo mode)

---

## Before you send — quick checklist

- [ ] Removed or did not include `.env` (no OpenAI key)
- [ ] Zip runs and opens `README.md`
- [ ] You tested on their OS if possible (Windows / Linux)
- [ ] Optional: record a 1-minute demo video link
