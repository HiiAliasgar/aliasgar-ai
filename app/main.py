import json, hmac, logging
from fastapi import FastAPI, Depends, HTTPException, Request, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from .config import settings
from .db import init_db, get_db, Task, Approval, Draft, Message
from .security import require_auth
from .agent import ask_agent
from .github_service import create_file_pr
from .whatsapp import verify_signature, extract_messages, send_whatsapp_text

logger = logging.getLogger("aliasgar_ai")


def provider_error_detail(exc: Exception) -> str:
    status = getattr(exc, "status_code", None)
    request_id = getattr(exc, "request_id", None)
    if status == 401:
        message = "The AI provider rejected the configured credential (HTTP 401). Check the selected environment variable and replace the key if it is invalid or revoked."
    elif status == 403:
        message = "The AI provider denied this request (HTTP 403). Check API access, project restrictions and model permissions for the selected key."
    elif status == 404:
        message = "The configured model or API endpoint was not found (HTTP 404). Check OPENAI_MODEL and the provider endpoint."
    elif status == 429:
        message = "The AI provider rate limit or quota was reached (HTTP 429). Check usage limits, billing and retry timing."
    elif status is not None and status >= 500:
        message = f"The AI provider returned a server error (HTTP {status}). Retry after the provider recovers."
    elif "timeout" in type(exc).__name__.lower():
        message = "The AI provider request timed out. Check service availability and retry."
    elif "connection" in type(exc).__name__.lower():
        message = "The server could not connect to the AI provider. Check outbound network access and provider availability."
    else:
        message = f"The AI provider request failed ({type(exc).__name__}). Check the provider key, model access and server logs."
    if request_id:
        message += f" Provider request ID: {request_id}."
    return message


app = FastAPI(title=settings.app_name, version="0.2.0")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
def dashboard():
    return FileResponse("app/static/index.html")

@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name, "ai_provider": settings.normalized_ai_provider,
            "ai_configured": settings.ai_configured, "model": settings.model_name}

@app.get("/api/me", dependencies=[Depends(require_auth)])
def me():
    return {
        "name": "Aliasgar AI", "owner": "Aliasgar Lohawala",
        "model": settings.model_name, "configured_model": settings.openai_model,
        "model_migrated": settings.model_migrated,
        "ai_provider": settings.normalized_ai_provider, "ai_key_env": settings.api_key_env_name,
        "active_ai_key_env": settings.active_api_key_source,
        "github_configured": bool(settings.github_token),
        "whatsapp_configured": bool(settings.whatsapp_access_token and settings.whatsapp_phone_number_id),
        "openai_configured": bool(settings.openai_api_key),
        "ai_configured": settings.ai_configured, "linkedin_mode": "draft_only"
    }

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=12000)
    channel: str = "web"

@app.post("/api/chat", dependencies=[Depends(require_auth)])
async def chat(body: ChatRequest, db: Session = Depends(get_db)):
    key = "owner"
    prior = db.query(Message).filter_by(conversation_key=key).order_by(Message.id.desc()).limit(12).all()
    history = [{"role":m.role,"content":m.content} for m in reversed(prior)]
    db.add(Message(channel=body.channel,conversation_key=key,role="user",content=body.message)); db.commit()
    try:
        answer = await ask_agent(body.message, history)
        task = Task(channel=body.channel,user_ref=key,prompt=body.message,status="completed",result=answer)
        db.add(task); db.add(Message(channel=body.channel,conversation_key=key,role="assistant",content=answer)); db.commit()
        return {"task_id":task.id,"status":"completed","reply":answer}
    except Exception as exc:
        logger.exception("AI provider request failed")
        detail = provider_error_detail(exc)
        db.add(Task(channel=body.channel, user_ref=key, prompt=body.message, status="failed",
                    result=(type(exc).__name__ + ": " + detail)[:700]))
        db.commit()
        if isinstance(exc, RuntimeError) and "not configured" in str(exc).lower():
            raise HTTPException(status_code=503, detail=settings.api_key_env_name + " is not configured for the selected provider.")
        raise HTTPException(status_code=502, detail=detail)

@app.get("/api/tasks", dependencies=[Depends(require_auth)])
def tasks(db: Session = Depends(get_db)):
    rows = db.query(Task).order_by(Task.id.desc()).limit(100).all()
    return [{"id":x.id,"channel":x.channel,"prompt":x.prompt,"status":x.status,"result":x.result,"created_at":x.created_at.isoformat()} for x in rows]

@app.get("/api/approvals", dependencies=[Depends(require_auth)])
def approvals(db: Session = Depends(get_db)):
    rows = db.query(Approval).order_by(Approval.id.desc()).limit(100).all()
    return [{"id":x.id,"action_type":x.action_type,"summary":x.summary,"payload":json.loads(x.payload),"status":x.status,"result":x.result,"created_at":x.created_at.isoformat()} for x in rows]

@app.post("/api/approvals/{approval_id}/approve", dependencies=[Depends(require_auth)])
async def approve(approval_id: int, db: Session = Depends(get_db)):
    item = db.get(Approval, approval_id)
    if not item: raise HTTPException(404,"Approval not found")
    if item.status != "pending": raise HTTPException(409,f"Approval is {item.status}")
    payload = json.loads(item.payload)
    if item.action_type != "github_file_pr": raise HTTPException(400,"Unsupported approval action")
    try:
        result = await create_file_pr(payload["owner"],payload["repo"],payload["path"],payload["content"],payload["commit_message"],payload["pr_title"],payload["pr_body"])
        item.status="approved_executed"; item.result=json.dumps(result); db.commit()
        return {"status":item.status,"result":result}
    except Exception as exc:
        item.status="execution_failed"; item.result=str(exc); db.commit()
        raise HTTPException(502,str(exc))

@app.post("/api/approvals/{approval_id}/reject", dependencies=[Depends(require_auth)])
def reject(approval_id: int, db: Session = Depends(get_db)):
    item=db.get(Approval, approval_id)
    if not item: raise HTTPException(404,"Approval not found")
    if item.status!="pending": raise HTTPException(409,f"Approval is {item.status}")
    item.status="rejected"; db.commit()
    return {"status":"rejected"}

@app.get("/api/drafts", dependencies=[Depends(require_auth)])
def drafts(db: Session = Depends(get_db)):
    rows=db.query(Draft).order_by(Draft.id.desc()).limit(100).all()
    return [{"id":x.id,"platform":x.platform,"content":x.content,"status":x.status,"created_at":x.created_at.isoformat()} for x in rows]

@app.get("/webhooks/whatsapp")
def verify_whatsapp(mode: str|None=Query(default=None,alias="hub.mode"),token: str|None=Query(default=None,alias="hub.verify_token"),challenge: str|None=Query(default=None,alias="hub.challenge")):
    if mode=="subscribe" and token and hmac.compare_digest(token,settings.whatsapp_verify_token):
        return int(challenge) if challenge and challenge.isdigit() else challenge
    raise HTTPException(403,"Webhook verification failed")

@app.post("/webhooks/whatsapp")
async def whatsapp_webhook(request: Request, db: Session=Depends(get_db)):
    body=await request.body()
    if len(body) > 1_000_000:
        raise HTTPException(413, "Webhook payload too large")
    if not verify_signature(body,request.headers.get("X-Hub-Signature-256")):
        raise HTTPException(401,"Invalid webhook signature")
    try: payload=json.loads(body)
    except json.JSONDecodeError: raise HTTPException(400,"Invalid JSON")
    for msg in extract_messages(payload):
        sender,prompt=msg["from"],msg["text"].strip()
        if sender not in settings.allowed_phones: continue
        db.add(Message(channel="whatsapp",conversation_key=sender,role="user",content=prompt)); db.commit()
        try:
            prior = db.query(Message).filter_by(conversation_key=sender).order_by(Message.id.desc()).limit(12).all()
            history = [{"role": m.role, "content": m.content} for m in reversed(prior[:-1])]
            answer=await ask_agent(prompt, history)
            db.add(Task(channel="whatsapp",user_ref=sender,prompt=prompt,status="completed",result=answer))
            db.add(Message(channel="whatsapp",conversation_key=sender,role="assistant",content=answer)); db.commit()
            await send_whatsapp_text(sender,answer)
        except Exception as exc:
            await send_whatsapp_text(sender,"Aliasgar AI error: "+str(exc)[:600])
    return {"received":True}
