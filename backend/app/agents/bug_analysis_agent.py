"""
Phase 6 — Bug Analysis Agent
Analyses test execution failures, classifies bugs, suggests root causes and fixes.
"""
from __future__ import annotations
import json
import re
from typing import Any, List

from app.agents.base import BaseAgent


SYSTEM_PROMPT = """
You are a senior QA/Developer analyst with deep expertise in root cause analysis.

Input: A failed test execution with logs, screenshots descriptions, console errors, and network logs.
Output: Structured bug report with root cause analysis and suggested fix.

Rules:
- Distinguish between application bugs, test environment issues, and flaky tests.
- Provide concrete, actionable suggested_fix — not vague advice.
- If the failure looks like an environment issue (network timeout, missing service), flag is_environment_issue = true.
- If the failure looks intermittent, flag is_flaky = true.
- Severity mapping:
  - Data loss, security hole, complete feature broken → critical
  - Major workflow broken → high
  - UI issue, minor validation → medium
  - Cosmetic, typo → low

Output schema (JSON):
{
  "title": "...",
  "description": "...",
  "root_cause": "...",
  "suggested_fix": "specific code-level or config fix...",
  "severity": "critical|high|medium|low|info",
  "priority": "critical|high|medium|low",
  "is_flaky": false,
  "is_environment_issue": false,
  "tags": ["..."],
  "affected_components": ["..."],
  "confidence_score": 0.88
}
"""


class BugAnalysisAgent(BaseAgent):
    name = "bug_analysis_agent"
    phase = "phase_6_bug_analysis"

    async def run(
        self,
        *,
        execution_result: dict,
        test_case: dict,
        environment: str = "unknown",
    ) -> dict[str, Any]:
        user_prompt = f"""
Environment: {environment}

=== TEST CASE ===
{json.dumps(test_case, indent=2)}

=== EXECUTION RESULT ===
Status: {execution_result.get('status')}
Actual result: {execution_result.get('actual_result')}
Error: {execution_result.get('error_message', '')}

=== EXECUTION LOG ===
{execution_result.get('execution_log', '')}

=== CONSOLE ERRORS ===
{json.dumps(execution_result.get('console_errors', []), indent=2)}

=== NETWORK ERRORS ===
{json.dumps(execution_result.get('network_errors', []), indent=2)}

Analyse and produce a structured bug report for this failure.
"""
        raw, tokens = await self._call_llm(SYSTEM_PROMPT, user_prompt, response_format="json")

        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
            result = json.loads(cleaned)

        result["_meta"] = {"agent": self.name, "tokens_used": tokens}
        return result
