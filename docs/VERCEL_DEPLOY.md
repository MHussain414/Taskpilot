# Deploy TaskPilot to Vercel

## One-click import (recommended)

1. Open [Import TaskPilot on Vercel](https://vercel.com/new/import?s=https://github.com/MHussain414/Taskpilot)
2. Sign in with GitHub and import the repo
3. **Environment variables** (Project → Settings → Environment Variables):

   | Name | Value |
   |------|-------|
   | `FLASK_SECRET_KEY` | Any long random string (e.g. `openssl rand -hex 32`) |
   | `OPENAI_API_KEY` | *(optional)* For GPT-enhanced chat |

4. Click **Deploy**

Your live URL will look like `https://taskpilot-xxx.vercel.app`. Open `/login/` — demo mode accepts any email/password unless `DEMO_EMAIL` / `DEMO_PASSWORD` are set.

## CLI deploy

```powershell
npm install -g vercel
vercel login
vercel --prod
```

## Notes

- Vercel runs Flask as a serverless function; SQLite uses `/tmp` (data may reset on cold starts — fine for demos).
- Static assets are served from `app/static/` via Flask.
- Every push to `main` auto-deploys when the repo is linked in Vercel.
