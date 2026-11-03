# Aliasgar AI

A personal engineering agent built with FastAPI, Gemini/OpenAI-compatible tool calling, SQLite/PostgreSQL, GitHub read tools, approval-gated GitHub file changes, LinkedIn draft storage, a web dashboard and an optional WhatsApp webhook.

## Local setup

Python 3.11+ is recommended.

1. Create and activate a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env`.
4. Set a strong `APP_API_TOKEN` and a Gemini API key.
5. Start the service with `uvicorn app.main:app --reload`.
6. Open `http://127.0.0.1:8000`.

## Important: two different secrets

- `APP_API_TOKEN` is the dashboard login token. Enter this token in the dashboard.
- `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) is the server-side model key. Store it in Render environment variables. Never paste it into the dashboard or commit it to GitHub.

The dashboard's `/api/me` response reports whether the server has a configured AI key without exposing the key value.

## Gemini configuration

- `AI_PROVIDER=gemini`
- `GEMINI_API_KEY=...` or `GOOGLE_API_KEY=...`
- `OPENAI_MODEL=gemini-3.8-flash`

The application migrates the old `gemini-2.5-flash-lite` setting to `gemini-3.8-flash` for Gemini deployments. The Gemini API key must have access to the selected model and an active quota/billing arrangement where required.

For OpenAI instead, set `AI_PROVIDER=openai`, `OPENAI_API_KEY`, and a valid `OPENAI_MODEL`.

## Render deployment

The Render blueprint is in `render.yaml`. Configure the Gemini key in the service environment as `GEMINI_API_KEY` or `GOOGLE_API_KEY`. The dashboard token is a separate generated value named `APP_API_TOKEN`.

After deployment, check:

- `/health` for service and AI configuration status.
- `/api/me` (with the dashboard token) for the active provider, model and key-configured flag.

Do not share API key values in screenshots or chat. Share only redacted error messages and request IDs when debugging.

## Safety and permissions

- GitHub repository inspection is read-only by default.
- Proposed GitHub file changes are stored as pending approvals.
- Approving a change creates a draft pull request; it does not directly push to the default branch.
- LinkedIn support is draft-only. Publishing is not implemented.
- The agent has no arbitrary shell, filesystem, credential or browser access.

## Tests

Run configuration tests with:

```bash
python -m unittest discover -s tests -v
```
