# Zero-budget cloud deployment

## Render
Create a Python 3 Web Service on the Free plan.
- Build: `pip install -r requirements.txt`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Do not add a Render disk or rely on local SQLite for persistence.

## Supabase
Create a Free PostgreSQL project. Set Render `DATABASE_URL` to:
`postgresql+psycopg://postgres:<PASSWORD>@<HOST>:5432/postgres`
URL-encode special characters in the password. Supabase free projects may pause after inactivity; keep backups.

## Gemini
Create a key at https://aistudio.google.com/apikey. Set `AI_PROVIDER=gemini`, `GEMINI_API_KEY`, and `OPENAI_MODEL=gemini-3.8-flash`. The app uses Google's OpenAI-compatible Gemini endpoint. After deployment, connect to the dashboard and run **Test AI connection**; a configured key is not necessarily a valid key and does not guarantee quota. Check Google's current model availability and quota before changing the model. Do not send secrets or sensitive repository data to a free-tier model.

## GitHub
Initially leave `GITHUB_TOKEN` blank and test health/dashboard. Later create a fine-grained token restricted to selected repositories. Begin read-only.

## WhatsApp
Configure only after web dashboard works. Callback URL: `https://<service>.onrender.com/webhooks/whatsapp`. Set Meta access token, phone number ID, verify token, sender allowlist, and app secret. Render Free may sleep and delay webhooks by 50 seconds or more; this is not a dependable 24/7 WhatsApp service. Meta messaging may also incur charges.

## Cost warning
Do not choose paid compute or add a payment method if ₹0 is a hard limit. Third-party pricing, quotas, and free-tier terms can change.
