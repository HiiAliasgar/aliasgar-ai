import hashlib, hmac
import httpx
from .config import settings

def verify_signature(body: bytes, signature: str | None):
    if not settings.meta_app_secret:
        return settings.app_env != "production"
    if not signature or not signature.startswith("sha256="):
        return False
    digest = hmac.new(settings.meta_app_secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest("sha256=" + digest, signature)

async def send_whatsapp_text(to: str, text: str):
    if not (settings.whatsapp_access_token and settings.whatsapp_phone_number_id):
        return False
    url = f"https://graph.facebook.com/v21.0/{settings.whatsapp_phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {settings.whatsapp_access_token}"}
    payload = {"messaging_product":"whatsapp","to":to,"type":"text","text":{"preview_url":False,"body":text[:4000]}}
    async with httpx.AsyncClient(timeout=25) as client:
        response = await client.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return True

def extract_messages(payload):
    result = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            for msg in change.get("value", {}).get("messages", []):
                if msg.get("type") == "text":
                    result.append({"from":msg.get("from",""),"text":msg.get("text",{}).get("body","")})
    return result
