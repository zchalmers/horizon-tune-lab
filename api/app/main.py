from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from app import db
from app.engine import build_answer
from app.safety import SecurityHeadersMiddleware, check_rate_limit, get_client_ip
from app.schemas import (
    AskRequest,
    AskResponse,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    CarSearchResponse,
    HealthResponse,
    RefusalResponse,
    SafetyInfo,
)

logger = logging.getLogger("horizon_tune_lab")
logging.basicConfig(level=logging.INFO)

REFUSAL_TEXT = (
    "I can only help with Forza Horizon tuning questions. "
    "Try asking something like: 'My AWD S2 car understeers on throttle exit — what should I adjust?'"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    status = db.check_db_health()
    if status != "ok":
        logger.warning("DB health check at startup: %s", status)
    yield


app = FastAPI(
    title="Horizon Tune Lab API",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan,
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error for %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "An error occurred. Please try again."})


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.get("/api/health", response_model=HealthResponse)
async def health():
    db_status = db.check_db_health()
    return HealthResponse(status="ok" if db_status == "ok" else "degraded", db=db_status)


@app.post("/api/ask", response_model=AskResponse | RefusalResponse)
async def ask(raw_req: Request):
    ip = get_client_ip(raw_req)
    check_rate_limit(ip)

    body = await raw_req.body()
    if len(body) > 8_192:
        raise HTTPException(status_code=413, detail="Request too large.")

    try:
        req = AskRequest.model_validate_json(body)
    except ValidationError as exc:
        errors = exc.errors()
        if any(e.get("msg") == "Value error, off_topic" for e in errors):
            return RefusalResponse(
                answer=REFUSAL_TEXT,
                safety=SafetyInfo(mode="deterministic", refused=True, refusal_reason="off_topic"),
            )
        raise HTTPException(status_code=422, detail="Invalid request.")

    return build_answer(req)


@app.post("/api/chat", response_model=ChatResponse)
async def chat(raw_req: Request):
    ip = get_client_ip(raw_req)
    check_rate_limit(ip)

    body = await raw_req.body()
    if len(body) > 65_536:
        raise HTTPException(status_code=413, detail="Request too large.")

    try:
        chat_req = ChatRequest.model_validate_json(body)
        req = chat_req.to_ask_request()
    except ValidationError as exc:
        errors = exc.errors()
        if any(e.get("msg") == "Value error, off_topic" for e in errors):
            refusal = RefusalResponse(
                answer=REFUSAL_TEXT,
                safety=SafetyInfo(mode="deterministic", refused=True, refusal_reason="off_topic"),
            )
            return ChatResponse(
                message=ChatMessage(role="assistant", content=refusal.answer),
                answer=refusal,
            )
        raise HTTPException(status_code=422, detail="Invalid request.")
    except ValueError as exc:
        if "no_user_message" in str(exc):
            raise HTTPException(status_code=422, detail="Chat must include a user message.") from exc
        raise HTTPException(status_code=422, detail="Invalid request.") from exc

    answer = build_answer(req)
    return ChatResponse(
        message=ChatMessage(role="assistant", content=answer.answer),
        answer=answer,
    )


@app.get("/api/cars/search", response_model=CarSearchResponse)
async def cars_search(q: str = "", limit: int = 8):
    if not q.strip():
        return CarSearchResponse(results=[], total=0)
    q_safe = q[:80]
    limit_safe = min(max(1, limit), 20)
    rows = db.search_cars(q_safe, limit_safe)
    from app.schemas import CarResult
    results = [CarResult(**r) for r in rows]
    return CarSearchResponse(results=results, total=len(results))


@app.get("/api/settings/search")
async def settings_search(q: str = "", limit: int = 5):
    if not q.strip():
        return {"results": [], "total": 0}
    q_safe = q[:80]
    limit_safe = min(max(1, limit), 10)
    docs = db.search_documents(q_safe, limit_safe)
    results = [
        {"title": d.get("title") or d.get("section") or "Tuning note", "summary": (d.get("content") or "")[:200]}
        for d in docs
    ]
    return {"results": results, "total": len(results)}


# Serve frontend static files (built assets) — mounted last so API routes take priority
import os
_STATIC_DIR = os.environ.get("STATIC_DIR", "/app/static")
if os.path.isdir(_STATIC_DIR):
    app.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="static")
