

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api.auth import router as auth_router
from app.api.tickets import router as tickets_router

settings = get_settings()

# Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# Create FastAPI app
app = FastAPI(
    title="QuickQueryDesk",
    description="AI-Powered Helpdesk & Ticket Resolution System",
    version="1.0.0",
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


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "QuickQueryDesk API"}
