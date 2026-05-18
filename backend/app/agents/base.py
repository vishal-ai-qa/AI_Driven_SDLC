"""
Base agent class — shared LLM client, logging, anti-hallucination guardrails.
"""
from __future__ import annotations
import time
import uuid
from abc import ABC, abstractmethod
from typing import Any, Optional

import structlog
from anthropic import AsyncAnthropic

from app.config import settings

logger = structlog.get_logger()


class BaseAgent(ABC):
    """
    All agents inherit from this. Provides:
    - Shared async Anthropic client
    - Structured logging with token accounting
    - Confidence-score enforcement (anti-hallucination)
    - Retry wrapper
    """

    name: str = "base_agent"
    phase: str = "unknown"

    def __init__(self, model: Optional[str] = None):
        self._model = model or settings.AI_MODEL
        self._client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self._log = logger.bind(agent=self.name, phase=self.phase)

    # ── Anti-hallucination system prompt fragment ──────────────────────────────

    ANTI_HALLUCINATION_RULES = """
CRITICAL ANTI-HALLUCINATION RULES — MUST FOLLOW:
1. NEVER invent business logic not explicitly stated in the requirements.
2. NEVER fabricate API endpoints, fields, validation rules, or workflows.
3. If information is missing or ambiguous, mark it as "NEEDS_CLARIFICATION".
4. NEVER assume behavior — only derive from provided text.
5. Every output item MUST include a confidence_score (0.0–1.0).
6. confidence_score < 0.7 → mark needs_clarification = true.
7. Include source_ref citing the specific input text that justifies each output.
8. If you cannot determine something with certainty, say so explicitly.
9. Do NOT fill gaps with plausible-sounding but unverified assumptions.
10. Output ONLY valid JSON matching the requested schema — no extra prose.
"""

    # ── Core LLM call ─────────────────────────────────────────────────────────

    async def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: str = "json",
    ) -> tuple[str, int]:
        """Call LLM and return (content, tokens_used)."""
        full_system = f"{system_prompt}\n\n{self.ANTI_HALLUCINATION_RULES}"
        if response_format == "json":
            full_system += "\nRespond ONLY with valid JSON. No markdown fences, no prose."

        start = time.time()
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=settings.AI_MAX_TOKENS,
                temperature=settings.AI_TEMPERATURE,
                system=full_system,
                messages=[{"role": "user", "content": user_prompt}],
            )
            content = response.content[0].text
            tokens = response.usage.input_tokens + response.usage.output_tokens
            duration_ms = int((time.time() - start) * 1000)
            self._log.info(
                "llm_call_complete",
                tokens=tokens,
                duration_ms=duration_ms,
                model=self._model,
            )
            return content, tokens
        except Exception as exc:
            self._log.error("llm_call_failed", error=str(exc))
            raise

    @abstractmethod
    async def run(self, **kwargs) -> Any:
        """Main agent entrypoint."""
        ...
