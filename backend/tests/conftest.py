"""
pytest configuration — mocks heavy AI/browser deps before importing the app
so CI only needs the lean requirements-test.txt (no langchain/playwright/etc).
"""
import sys
import asyncio
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
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.database import Base, get_db

TEST_DATABASE_URL = "postgresql+asyncpg://qagent:test_secret@localhost:5432/qagent_test"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(setup_db):
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
