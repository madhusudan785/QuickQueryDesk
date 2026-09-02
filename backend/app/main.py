"""FastAPI application entry point.

NOTE: This is the Part 3 (agent dashboard + WebSocket real-time updates)
commit. The metrics dashboard and knowledge-base browsing API are added
in a later commit — see app/api/metrics.py and app/api/knowledge_base.py
once those land.
"""

from contextlib import asynccontextmanager
import logging
import re

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status, Query
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.security import decode_access_token
from app.api.auth import router as auth_router
from app.api.tickets import router as tickets_router
from app.api.metrics import router as metrics_router
from app.websocket.manager import manager
from app.rag.engine import async_initialize_rag

settings = get_settings()


class SensitiveDataFilter(logging.Filter):
    """Filter to redact sensitive query parameters (e.g. token=...) from logs."""

    _TOKEN_PATTERN = re.compile(r'(token=)[^&\s"\'\\]+', re.IGNORECASE)

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self._TOKEN_PATTERN.sub(r'\1[REDACTED]', record.msg)
        if record.args:
            clean_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    clean_args.append(self._TOKEN_PATTERN.sub(r'\1[REDACTED]', arg))
                else:
                    clean_args.append(arg)
            record.args = tuple(clean_args)
        return True


def apply_log_filters():
    """Apply sanitization filter to root, app, and uvicorn loggers."""
    log_filter = SensitiveDataFilter()
    for name in ("", "uvicorn", "uvicorn.access", "uvicorn.error", "app"):
        log = logging.getLogger(name)
        log.addFilter(log_filter)
        for handler in log.handlers:
            handler.addFilter(log_filter)


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
apply_log_filters()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager to initialize expensive RAG resources once on startup."""
    apply_log_filters()
    logger.info("Initializing RAG resources on application startup...")
    try:
        success = await async_initialize_rag()
        if success:
            logger.info("RAG engine pre-warmed and ready for requests.")
        else:
            logger.warning("RAG engine initialization reported incomplete state.")
    except Exception as e:
        logger.error(f"Error during startup RAG initialization: {e}")
    yield
    logger.info("Application shutting down.")


# Create FastAPI app
app = FastAPI(
    title="QuickQueryDesk",
    description="AI-Powered Helpdesk & Ticket Resolution System",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth_router)
app.include_router(tickets_router)
app.include_router(metrics_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "QuickQueryDesk API"}


# --- WebSocket endpoints ---
#
# Real-time updates: when an employee creates a ticket, all connected
# agents see it appear without refreshing (see api/tickets.py's
# create_ticket -> manager.notify_agents). When an agent resolves a
# ticket, that specific employee sees the status flip to Resolved
# without refreshing (see reply_to_ticket -> manager.notify_employee).
#
# Auth: the browser WebSocket API can't set custom headers, so the JWT
# is passed as a query param (?token=...) and validated before the
# connection is accepted. REST endpoints remain the source of truth —
# WebSocket is a live-update convenience on top of them, not a
# replacement; a client that misses a message (e.g. during a brief
# disconnect) will still see the correct state on its next REST fetch
# or page load.

async def validate_ws_token(websocket: WebSocket, token: str | None = None) -> dict | None:
    """Validate WebSocket token and return payload."""
    if not token:
        logger.warning("WebSocket auth failed: missing token")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
    try:
        payload = decode_access_token(token)
        return payload
    except Exception:
        logger.warning("WebSocket auth failed: invalid or expired token")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None


@app.websocket("/ws/agent")
async def agent_websocket(websocket: WebSocket, token: str | None = Query(None)):
    """WebSocket endpoint for agents to receive real-time updates."""
    payload = await validate_ws_token(websocket, token)
    if not payload:
        return

    if payload.get("role") != "agent":
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect_agent(websocket)
    try:
        while True:
            # Keep connection alive; agents don't send data, just receive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_agent(websocket)


@app.websocket("/ws/employee")
async def employee_websocket(websocket: WebSocket, token: str | None = Query(None)):
    """WebSocket endpoint for employees to receive real-time updates."""
    payload = await validate_ws_token(websocket, token)
    if not payload:
        return

    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect_employee(websocket, user_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_employee(websocket, user_id)
