"""
Phase 2 — User Story Generation Agent
Converts structured requirements into epics + user stories with acceptance criteria.
"""
from __future__ import annotations
import json
import re
from typing import Any, List

from app.agents.base import BaseAgent


SYSTEM_PROMPT = """
You are a senior Agile Product Owner and BA producing enterprise-grade user stories.

Input: A list of structured requirements (JSON).
Output: Epics and User Stories in JSON.

Story format:
  "As a [role], I want [goal] so that [business_value]."

Rules:
- One story per distinct user goal. Never merge unrelated goals.
- Every story must have at least 3 acceptance criteria (Given/When/Then preferred).
- Every story must include: positive scenarios, negative scenarios, boundary conditions.
- Map each story back to its source requirement via requirement_ref.
- Include UI validations, API validations, security validations where applicable.
- Assign risk_level: critical | high | medium | low.
- NEVER invent functionality not traceable to the requirement.
- Confidence < 0.7 → set needs_clarification = true.

Output schema (JSON):
{
  "epics": [
    {
      "epic_id": "EPIC-001",
      "title": "...",
      "description": "...",
      "stories": [
        {
          "story_id": "US-001",
          "epic_id": "EPIC-001",
          "requirement_ref": "REQ-001",
          "title": "...",
          "role": "customer",
          "goal": "...",
          "business_value": "...",
          "acceptance_criteria": [
            {"id": "AC-001", "description": "Given... When... Then...", "type": "functional"}
          ],
          "positive_scenarios": ["..."],
          "negative_scenarios": ["..."],
          "ui_validations": ["..."],
          "api_validations": ["..."],
          "security_validations": ["..."],
          "boundary_conditions": ["..."],
          "priority": "high",
          "risk_level": "medium",
          "story_points": 3,
          "confidence_score": 0.92,
          "needs_clarification": false,
          "clarification_notes": []
        }
      ]
    }
  ],
  "traceability_gaps": ["..."],
  "overall_confidence": 0.88
}
"""


class StoryAgent(BaseAgent):
    name = "story_agent"
    phase = "phase_2_stories"

    async def run(
        self,
        *,
        project_id: str,
        requirements: List[dict],
    ) -> dict[str, Any]:
        user_prompt = f"""
Project ID: {project_id}

=== STRUCTURED REQUIREMENTS ===
{json.dumps(requirements, indent=2)}

Generate epics and user stories strictly derived from these requirements.
Do not add features not mentioned. Flag unclear requirements with needs_clarification.
"""
        raw, tokens = await self._call_llm(SYSTEM_PROMPT, user_prompt, response_format="json")

        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
            result = json.loads(cleaned)

        result["_meta"] = {"agent": self.name, "tokens_used": tokens}
        return result
