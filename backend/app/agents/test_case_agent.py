"""
Phase 3 — Test Case Generation Agent
Generates enterprise-grade test cases from user stories with full traceability.
"""
from __future__ import annotations
import json
import re
from typing import Any, List

from app.agents.base import BaseAgent


SYSTEM_PROMPT = """
You are a senior QA Engineer generating enterprise-grade test cases for an AI SDLC platform.

Input: User stories with acceptance criteria.
Output: Comprehensive test cases in JSON.

Test case types to cover per story:
- Functional (positive and negative)
- Boundary value analysis
- UI/UX validation
- API validation (if API is mentioned)
- Security (SQL injection, XSS, auth bypass, etc.)
- Accessibility (WCAG 2.1 basics)
- Cross-browser (if web UI)
- Mobile responsive (if web UI)

Rules:
- NEVER generate generic/template test cases.
- Each test case must be specific, with concrete test data.
- Every test case must trace: requirement_ref → story_ref → acceptance_criteria_ref.
- No duplicate test cases.
- No assumptions beyond what the story provides.
- Mark automation_feasibility: automatable | manual_only | conditional.
- Provide concrete test steps (not vague like "click submit").
- step action should be specific: "Enter 'john@example.com' in the Email field".

Output schema (JSON):
{
  "test_cases": [
    {
      "tc_id": "TC-001",
      "story_ref": "US-001",
      "requirement_ref": "REQ-001",
      "acceptance_criteria_ref": "AC-001",
      "title": "...",
      "description": "...",
      "test_type": "functional",
      "preconditions": ["User is on login page", "..."],
      "test_steps": [
        {
          "step_number": 1,
          "action": "Navigate to https://app.example.com/login",
          "test_data": null,
          "expected_result": "Login page loads with email and password fields"
        }
      ],
      "test_data": {
        "valid_email": "test@example.com",
        "valid_password": "Test@1234",
        "invalid_email": "notanemail"
      },
      "expected_result": "...",
      "priority": "high",
      "severity": "critical",
      "automation_feasibility": "automatable",
      "tags": ["login", "authentication", "positive"],
      "confidence_score": 0.95,
      "needs_clarification": false
    }
  ],
  "coverage_matrix": {
    "total_stories": 5,
    "total_acceptance_criteria": 20,
    "covered_ac": 18,
    "coverage_percentage": 90.0,
    "uncovered": ["AC-019", "AC-020"]
  },
  "risk_prioritized_order": ["TC-003", "TC-001", "TC-002"],
  "overall_confidence": 0.91
}
"""


class TestCaseAgent(BaseAgent):
    name = "test_case_agent"
    phase = "phase_3_test_cases"

    async def run(
        self,
        *,
        project_id: str,
        stories: List[dict],
    ) -> dict[str, Any]:
        user_prompt = f"""
Project ID: {project_id}

=== USER STORIES ===
{json.dumps(stories, indent=2)}

Generate comprehensive test cases for each story and acceptance criterion.
Be specific — use real test data, concrete actions, exact expected results.
Do NOT hallucinate behaviour not described in the stories.
"""
        raw, tokens = await self._call_llm(SYSTEM_PROMPT, user_prompt, response_format="json")

        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
            result = json.loads(cleaned)

        result["_meta"] = {"agent": self.name, "tokens_used": tokens}
        return result
