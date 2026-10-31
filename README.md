# Aliasgar AI

A personal AI agent MVP built with FastAPI, Gemini/OpenAI-compatible tool calling, PostgreSQL or SQLite, GitHub read tools, approval-gated GitHub file changes, LinkedIn draft storage, WhatsApp Cloud API webhook, and a web dashboard.

## Local setup (Python 3.11+)
```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```
Set `AI_PROVIDER=gemini`, `GEMINI_API_KEY`, and a strong `APP_API_TOKEN`, then run:
```powershell
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000.

## Environment
- `AI_PROVIDER=gemini` uses Gemini's OpenAI-compatible API endpoint. Set `GEMINI_API_KEY` and a model enabled for your account.
- `AI_PROVIDER=openai` uses `OPENAI_API_KEY`.
- `APP_API_TOKEN` protects dashboard and API routes.
- `DATABASE_URL` accepts SQLite locally or PostgreSQL in cloud.
- `GITHUB_TOKEN` is optional. Start with a fine-grained, read-only token; enable write permissions only after reviewing approval flow.
- WhatsApp requires Meta Cloud API credentials and an allowlisted sender. LinkedIn is draft-only; publishing is not implemented.

## Zero-budget cloud deployment
See [CLOUD_DEPLOYMENT.md](CLOUD_DEPLOYMENT.md). Render Free sleeps when idle and has ephemeral local storage. Use Supabase PostgreSQL for persistence. Free quotas and provider policies can change; keep backups and do not submit sensitive data to free AI tiers.

## Safety limits
This is a prototype, not a production-certified autonomous agent. GitHub changes require approval and create a draft pull request. There is no arbitrary shell execution, LinkedIn publishing, or general-purpose browser automation.
