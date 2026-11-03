# Aliasgar AI

A personal engineering-agent project that combines a FastAPI service, LLM tool calling, GitHub read operations, approval-gated repository changes, and a lightweight web dashboard.

## What it explores

- **LLM integration:** Gemini or OpenAI-compatible provider configuration.
- **Tool calling:** structured interactions between the model and application tools.
- **GitHub workflows:** repository inspection is read-only by default; proposed file changes wait for approval and create draft pull requests.
- **Dashboard:** token-protected interface with provider and model diagnostics.
- **Optional integration:** WhatsApp webhook support.
- **Persistence:** SQLite or PostgreSQL configuration.

This is a personal engineering project, not an autonomous agent with unrestricted access to a user's machine or accounts.

## Architecture at a glance

1. FastAPI exposes the application and dashboard APIs.
2. The configured LLM provider handles model requests.
3. Application tools perform explicitly scoped operations.
4. Repository edits are stored as pending approvals.
5. Approval creates a draft pull request rather than directly changing a default branch.

## Local development

Python 3.11+ is recommended.

```bash
git clone https://github.com/HiiAliasgar/aliasgar-ai.git
cd aliasgar-ai
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env`, then configure the dashboard token and one model provider.

### Gemini

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=your_key
OPENAI_MODEL=gemini-3.8-flash
```

### OpenAI-compatible provider

```env
AI_PROVIDER=openai
OPENAI_API_KEY=your_key
OPENAI_MODEL=your_model
```

Keep API keys server-side. Never commit `.env` or paste secrets into dashboard fields.

Start the service:

```bash
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`.

## Deployment notes

A Render blueprint is provided in `render.yaml`. Configure `APP_API_TOKEN` and the selected model-provider key as service environment variables.

- `/health` reports service and configuration status; key presence does not prove that a key is valid.
- `/api/me` reports the active provider/model configuration to an authenticated dashboard.
- Use **Test AI connection** to validate actual model access.

## Security model

- No arbitrary shell execution.
- No unrestricted filesystem or credential access.
- GitHub inspection is read-only by default.
- File changes require an approval step and produce a draft pull request.
- LinkedIn functionality stores drafts; it does not publish posts.

## Tests

```bash
python -m unittest discover -s tests -v
```

## Repository

[View source code](https://github.com/HiiAliasgar/aliasgar-ai)
