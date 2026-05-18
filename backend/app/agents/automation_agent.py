"""
Phase 8 — Playwright Automation Generation Agent
Generates production-grade TypeScript Playwright scripts with POM architecture.
"""
from __future__ import annotations
import json
import re
from typing import Any, List

from app.agents.base import BaseAgent


SYSTEM_PROMPT = """
You are an expert in Playwright TypeScript automation with deep knowledge of:
- Page Object Model (POM) pattern
- Playwright best practices
- Enterprise test automation standards
- CI/CD integration
- Resilient, low-flakiness test design

Input: An approved test case with steps, test data, and traceability info.
Output: Production-ready TypeScript Playwright test code.

Rules:
- Use TypeScript strictly typed.
- Use Page Object Model — create a page class for each distinct page.
- Use data-testid selectors first; fall back to aria-label, role, then CSS.
- No hard-coded timeouts (use waitForSelector, waitForResponse, etc.).
- Use test.step() for each logical group of actions.
- Include test metadata in the test title: "TC-001 | {title}".
- Add expect assertions that precisely validate the expected result.
- Use test fixtures for authentication.
- Handle both positive and negative paths in separate it() blocks.
- Include JSDoc for page objects.

Output schema (JSON):
{
  "page_objects": [
    {
      "file_path": "src/pages/LoginPage.ts",
      "content": "import { Page, Locator } from '@playwright/test';\\n..."
    }
  ],
  "test_spec": {
    "file_path": "tests/auth/TC-001-login.spec.ts",
    "content": "import { test, expect } from '@playwright/test';\\n..."
  },
  "fixtures_needed": ["authFixture"],
  "test_data_file": {
    "file_path": "src/test-data/auth.json",
    "content": "{...}"
  },
  "generation_notes": "..."
}
"""


class AutomationAgent(BaseAgent):
    name = "automation_agent"
    phase = "phase_8_automation"

    async def run(
        self,
        *,
        test_case: dict,
        project_name: str,
        base_url: str,
    ) -> dict[str, Any]:
        user_prompt = f"""
Project: {project_name}
Base URL: {base_url}

=== APPROVED TEST CASE ===
{json.dumps(test_case, indent=2)}

Generate production-grade Playwright TypeScript code.
Ensure:
1. Page Object created for each page visited.
2. Test spec with proper describe/test blocks.
3. All assertions map to the test case expected_result.
4. Test data externalized to JSON fixture.
5. No flaky patterns (no fixed sleeps, no brittle selectors).
"""
        raw, tokens = await self._call_llm(SYSTEM_PROMPT, user_prompt, response_format="json")

        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
            result = json.loads(cleaned)

        result["_meta"] = {"agent": self.name, "tokens_used": tokens}
        return result
