import hmac
from fastapi import Header, HTTPException
from .config import settings

def require_auth(authorization: str | None = Header(default=None)):
    expected = f"Bearer {settings.app_api_token}"
    if (
        not settings.app_api_token
        or settings.app_api_token == "change-me"
        or (
            settings.app_env.strip().lower() == "production"
            and len(settings.app_api_token) < 32
        )
    ):
        raise HTTPException(status_code=503, detail="Set a strong APP_API_TOKEN in environment first.")
    if not authorization or not hmac.compare_digest(authorization, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing API token.")
    return True
