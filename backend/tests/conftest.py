"""
pytest configuration — mocks heavy AI/browser deps before importing the app
so CI only needs the lean requirements-test.txt (no langchain/playwright/etc).
"""
import sys
from unittest.mock import MagicMock, AsyncMock

# ── Mock heavy packages before any app import ────────────────────────────────
# This lets the app load in CI without installing anthropic, langchain, etc.
_MOCK_MODULES = [
    "anthropic",
    "anthropic.types",
    "celery",
    "celery.app",
    "celery.schedules",
    "langchain",
    "langchain.chat_models",
    "langchain_core",
    "langchain_core.messages",
    "langchain_core.prompts",
    "langchain_anthropic",
    "langchain_community",
    "langchain_openai",
    "langgraph",
    "langgraph.graph",
    "openai",
    "tiktoken",
    "playwright",
    "playwright.async_api",
    "sentence_transformers",
    "weasyprint",
    "pytesseract",
    "PIL",
    "PIL.Image",
    "docx",
    "PyPDF2",
    "openpyxl",
]
for _mod in _MOCK_MODULES:
    sys.modules.setdefault(_mod, MagicMock())

# Make anthropic.AsyncAnthropic behave like an async client
_anthropic_mock = sys.modules["anthropic"]
_anthropic_mock.AsyncAnthropic = MagicMock(return_value=MagicMock())

# ── Now safe to import the app ───────────────────────────────────────────────
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.database import Base, get_db

TEST_DATABASE_URL = "postgresql+asyncpg://qagent:test_secret@localhost:5432/qagent_test"

# NullPool: each connection is independent, not reused across event loops.
# Prevents "Future attached to a different loop" when each test function gets
# its own asyncio event loop (pytest-asyncio asyncio_mode=auto default).
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session")
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(setup_db):
    # Mirror production get_db: commit on success, rollback on exception.
    async def override_get_db():
        async with TestSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
