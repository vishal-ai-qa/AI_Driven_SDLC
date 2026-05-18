"""
Gap Detection Agent — scans user stories for missing edge cases, ambiguous acceptance
criteria, and untested conditions. Returns actionable gap list with severity.
"""
from __future__ import annotations
import json
import re
from typing import Any

from app.agents.base import BaseAgent


SYSTEM_PROMPT = """
You are a senior QA architect and requirements analyst. Your job is to find GAPS in user stories —
missing edge cases, ambiguous acceptance criteria, untested conditions, security blind spots,
and boundary cases that developers and testers typically overlook.

Input: A list of user stories with their acceptance criteria.

Output: A JSON object with gap findings. Each gap must cite the specific story it relates to.

Gap types to detect:
- missing_edge_case: a condition not covered (empty input, null, max-length, concurrent access)
- ambiguous_ac: an acceptance criterion that could be interpreted multiple ways
- missing_security: no mention of auth/authz/XSS/injection for user-facing inputs
- missing_error_handling: happy path only, no failure scenarios
- missing_boundary: numeric or date limits not specified
- missing_performance: no mention of expected response time for critical flows
- duplicate: functionally identical to another story

Output schema (JSON):
{
  "gaps": [
    {
      "story_ref": "US-001",
      "gap_type": "missing_edge_case|ambiguous_ac|missing_security|missing_error_handling|missing_boundary|missing_performance|duplicate",
      "severity": "critical|high|medium|low",
      "description": "Specific gap description",
      "recommendation": "What to add or clarify",
      "confidence_score": 0.92
    }
  ],
  "summary": {
    "total_gaps": 5,
    "critical": 1,
    "high": 2,
    "medium": 1,
    "low": 1,
    "coverage_risk": "high|medium|low"
  },
  "_meta": {"tokens_used": 0}
}
"""


class GapAgent(BaseAgent):
    name = "gap_agent"
    phase = "gap_detection"

    async def run(self, *, stories: list[dict]) -> dict[str, Any]:
        user_prompt = f"""
Analyze these {len(stories)} user stories for gaps:

{json.dumps(stories, indent=2)}

Return the complete gap analysis JSON.
"""
        raw, tokens = await self._call_llm(SYSTEM_PROMPT, user_prompt)
        try:
            cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`")
            result = json.loads(cleaned)
        except Exception:
            result = {"gaps": [], "summary": {"total_gaps": 0, "coverage_risk": "unknown"}}
        result.setdefault("_meta", {})["tokens_used"] = tokens
        return result
