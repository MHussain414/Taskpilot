# TaskPilot — Setup Guide (for the person receiving this project)

Thank you for receiving **TaskPilot** (AI Project Management Chat Module).

## Requirements

- **Python 3.10 or newer** — https://www.python.org/downloads/  
  (During install on Windows, check **“Add Python to PATH”**)

## Install & run (Windows)

1. Unzip the folder anywhere (e.g. `C:\Projects\TaskPilot`).

2. Open **PowerShell** in that folder (Shift + right-click → “Open PowerShell window here”).

3. Run these commands one by one:

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python run.py
```

4. Open a browser and go to:

   **http://127.0.0.1:5000/login/**

5. Sign in with **any email and password** (demo mode), for example:
   - Email: `manager@company.com`
   - Password: `demo`

6. Click **Demo Data** to load sample tasks, then try **Workspace**, **Dashboard**, and **Team** tabs.

## Install & run (Linux / Mac)

```bash
cd TaskPilot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python run.py
```

Then open http://127.0.0.1:5000/login/

## Optional: OpenAI for smarter chat

1. Open `.env` in a text editor.
2. Add your key from https://platform.openai.com/api-keys :
   ```
   OPENAI_API_KEY=sk-your-key-here
   ```
3. Restart: `python run.py`
4. The app shows **GPT** badge when connected.

Task commands work **without** OpenAI.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `python` not found | Install Python and add to PATH |
| Port 5000 in use | Change `FLASK_PORT=5001` in `.env` |
| Blank page / buttons dead | Hard refresh: Ctrl+Shift+R |
| Deadline not saving | Use quick buttons (Today, Tomorrow) in task form |

## Project docs

- `README.md` — full documentation  
- `docs/ARCHITECTURE.md` — how AI priority scoring works  

## Contact

Share questions with the person who sent you this zip.
