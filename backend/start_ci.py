"""CI startup script — mocks heavy AI/browser deps then starts uvicorn.
Mirrors the sys.modules patching in tests/conftest.py so the app can load
with only requirements-test.txt installed (no langchain/playwright/etc).
"""
import sys
from unittest.mock import MagicMock

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

sys.modules["anthropic"].AsyncAnthropic = MagicMock(return_value=MagicMock())

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
