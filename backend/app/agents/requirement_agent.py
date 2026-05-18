"""
Phase 1 — Requirement Ingestion Agent
Parses raw BRD/Epic/Feature text and produces structured requirements.
ZERO hallucination: marks everything uncertain as NEEDS_CLARIFICATION.
"""
from __future__ import annotations
import json
import re
from typing import Any

from app.agents.base import BaseAgent


SYSTEM_PROMPT = """
You are an expert Business Analyst and Requirements Engineer embedded in an AI SDLC platform.

Your job is to analyse raw requirement text and produce a structured JSON document.

Rules:
- Extract ONLY what is explicitly stated. Never invent.
- Separate functional vs non-functional requirements.
- Identify missing information and mark it NEEDS_CLARIFICATION.
- Never guess UI behaviour, API structure, or business logic not mentioned.
- For each requirement assign a unique req_id (REQ-001, REQ-002…).
- Assign confidence_score between 0.0 and 1.0. Low confidence = include in clarification list.
- List all edge cases, risks, and explicit dependencies mentioned in the text.
- Provide an assumptions_log for anything you had to assume (keep this minimal).

Output schema (JSON):
{
  "functional_requirements": [
    {
      "req_id": "REQ-001",
      "title": "...",
      "description": "...",
      "source_ref": "verbatim quote from input",
      "priority": "critical|high|medium|low",
      "acceptance_criteria": ["..."],
      "assumptions": ["..."],
      "ambiguities": ["..."],
      "confidence_score": 0.95
    }
  ],
  "non_functional_requirements": [ /* same structure */ ],
  "risks": ["..."],
  "dependencies": ["..."],
  "edge_cases": ["..."],
  "clarification_questions": ["..."],
  "assumptions_log": ["..."],
  "overall_confidence": 0.85
}
"""


class RequirementAgent(BaseAgent):
    name = "requirement_agent"
    phase = "phase_1_ingestion"

    async def run(
        self,
        *,
        project_id: str,
        content: str,
        source_type: str = "brd",
        additional_context: str | None = None,
    ) -> dict[str, Any]:
        user_prompt = f"""
Source type: {source_type}
Project ID: {project_id}

=== RAW REQUIREMENT TEXT ===
{content}

{f"=== ADDITIONAL CONTEXT ==={chr(10)}{additional_context}" if additional_context else ""}

Analyse the above and produce the structured JSON output described in your instructions.
If any section is empty or not applicable, return an empty list [] for it.
Do NOT hallucinate any behaviour. Mark unknowns as NEEDS_CLARIFICATION.
"""
        raw, tokens = await self._call_llm(SYSTEM_PROMPT, user_prompt, response_format="json")

        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            # Attempt to strip markdown fences if model adds them
            cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
            result = json.loads(cleaned)

        result["_meta"] = {"agent": self.name, "tokens_used": tokens, "source_type": source_type}
        return result
