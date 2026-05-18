"""
QAgent — AI-Native SDLC Platform
FastAPI application entrypoint.
"""
import os
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import create_tables

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    logger.info("Starting QAgent platform", version=settings.APP_VERSION)
    await create_tables()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.REPORTS_DIR, exist_ok=True)
    yield
    logger.info("Shutting down QAgent platform")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Native SDLC Platform — Requirements → Stories → Tests → Automation",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ─── Middleware ───────────────────────────────────────────────────────────────

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("request", method=request.method, url=str(request.url))
    response = await call_next(request)
    logger.info("response", status=response.status_code)
    return response


# ─── Static files (reports, screenshots) ─────────────────────────────────────

if os.path.exists(settings.REPORTS_DIR):
    app.mount("/reports", StaticFiles(directory=settings.REPORTS_DIR), name="reports")

if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


# ─── Routes ───────────────────────────────────────────────────────────────────

from app.api.routes import (
    auth, projects, requirements, stories, test_cases,
    test_runs, bugs, automation, approvals, traceability, websocket,
)

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(requirements.router, prefix="/api/requirements", tags=["Requirements"])
app.include_router(stories.router, prefix="/api/stories", tags=["User Stories"])
app.include_router(test_cases.router, prefix="/api/test-cases", tags=["Test Cases"])
app.include_router(test_runs.router, prefix="/api/test-runs", tags=["Test Runs"])
app.include_router(bugs.router, prefix="/api/bugs", tags=["Bugs"])
app.include_router(automation.router, prefix="/api/automation", tags=["Automation"])
app.include_router(approvals.router, prefix="/api/approvals", tags=["Approvals"])
app.include_router(traceability.router, prefix="/api/traceability", tags=["Traceability"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])


# ─── Health ───────────────────────────────────────────────────────────────────

@app.get("/api/health", tags=["Health"])
async def health():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


# ─── Global error handler ─────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", error=str(exc), url=str(request.url))
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__},
    )
