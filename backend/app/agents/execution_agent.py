"""
Phase 5 — AI Test Execution Agent
Uses Playwright to autonomously execute test cases against a live application.
Captures screenshots, console errors, network logs, and produces rich execution logs.
"""
from __future__ import annotations
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import structlog
from playwright.async_api import (
    async_playwright, Browser, BrowserContext, Page,
    ConsoleMessage, Request, Response,
)

from app.agents.base import BaseAgent
from app.config import settings

logger = structlog.get_logger()


class ExecutionAgent(BaseAgent):
    """
    Autonomous Playwright-based test execution agent.
    For each test case:
      1. Interprets the test steps using the LLM to map to Playwright actions.
      2. Executes the actions in a real browser.
      3. Captures evidence (screenshots, console logs, network requests).
      4. Compares actual vs expected results.
      5. Returns a structured execution result.
    """

    name = "execution_agent"
    phase = "phase_5_execution"

    def __init__(self, run_id: str, reports_dir: str | None = None):
        super().__init__()
        self.run_id = run_id
        self.reports_dir = Path(reports_dir or settings.REPORTS_DIR) / "runs" / run_id
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self._console_logs: list[dict] = []
        self._network_logs: list[dict] = []

    # ── Main entry ─────────────────────────────────────────────────────────────

    async def run(
        self,
        *,
        test_case: dict,
        app_url: str,
        credentials: dict | None = None,
    ) -> dict[str, Any]:
        """Execute a single test case. Returns structured execution result."""
        tc_id = test_case.get("tc_id", "unknown")
        self._log.info("executing_test_case", tc_id=tc_id)
        start = time.time()
        screenshots: list[str] = []
        self._console_logs = []
        self._network_logs = []

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=settings.PLAYWRIGHT_HEADLESS,
                slow_mo=settings.PLAYWRIGHT_SLOW_MO,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            context = await browser.new_context(
                base_url=app_url,
                viewport={"width": 1280, "height": 800},
                record_video_dir=str(self.reports_dir) if settings.VIDEO_ON_FAILURE else None,
            )
            context.on("console", self._capture_console)
            page = await context.new_page()
            page.on("request", self._capture_request)
            page.on("response", self._capture_response)

            status = "passed"
            actual_result = ""
            error_message = ""
            step_logs: list[str] = []

            try:
                # Auth if credentials provided
                if credentials and credentials.get("username"):
                    await self._authenticate(page, app_url, credentials)

                # Execute each test step
                for step in test_case.get("test_steps", []):
                    step_num = step.get("step_number", "?")
                    action = step.get("action", "")
                    expected = step.get("expected_result", "")
                    log_line = await self._execute_step(page, step_num, action, expected, tc_id)
                    step_logs.append(log_line)

                    # Screenshot after each step
                    ss_path = await self._screenshot(page, tc_id, step_num)
                    if ss_path:
                        screenshots.append(ss_path)

                actual_result = f"All {len(test_case.get('test_steps', []))} steps executed"

                # Final result validation via LLM
                validation = await self._validate_result(
                    test_case=test_case,
                    step_logs=step_logs,
                    console_errors=[e for e in self._console_logs if e.get("type") == "error"],
                    network_errors=[e for e in self._network_logs if e.get("status", 200) >= 400],
                )
                status = validation.get("status", "passed")
                actual_result = validation.get("actual_result", actual_result)

            except Exception as exc:
                status = "failed"
                error_message = str(exc)
                actual_result = f"Execution error: {exc}"
                self._log.error("test_case_error", tc_id=tc_id, error=str(exc))
                if settings.SCREENSHOT_ON_FAILURE:
                    ss_path = await self._screenshot(page, tc_id, "error")
                    if ss_path:
                        screenshots.append(ss_path)
            finally:
                await context.close()
                await browser.close()

        duration_ms = int((time.time() - start) * 1000)
        return {
            "tc_id": tc_id,
            "status": status,
            "actual_result": actual_result,
            "error_message": error_message,
            "execution_log": "\n".join(step_logs),
            "console_errors": [e for e in self._console_logs if e.get("type") == "error"],
            "network_errors": [e for e in self._network_logs if e.get("status", 200) >= 400],
            "all_console_logs": self._console_logs,
            "screenshots": screenshots,
            "duration_ms": duration_ms,
            "started_at": datetime.utcnow().isoformat(),
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    async def _authenticate(self, page: Page, app_url: str, credentials: dict) -> None:
        """Attempt to authenticate. Strategy determined by AI analysis."""
        auth_prompt = f"""
Given app URL: {app_url}
Credentials: username="{credentials.get('username')}", password available.

Return JSON with Playwright steps to log in:
{{"steps": [{{"action": "goto", "url": "..."}}, {{"action": "fill", "selector": "...", "value": "username"}}, ...]}}
"""
        raw, _ = await self._call_llm(
            "You are a Playwright automation expert. Return only valid JSON action steps to authenticate.",
            auth_prompt,
        )
        try:
            steps = json.loads(raw).get("steps", [])
            for s in steps:
                await self._apply_playwright_action(page, s, credentials)
        except Exception as e:
            logger.warning("auth_strategy_failed", error=str(e))

    async def _execute_step(
        self, page: Page, step_num: Any, action: str, expected: str, tc_id: str
    ) -> str:
        """Use LLM to convert a human-readable action into Playwright code and execute it."""
        step_prompt = f"""
Convert this test step action to a Playwright JSON action object.

Action: "{action}"
Expected result hint: "{expected}"

Return JSON:
{{"playwright_action": "click|fill|goto|wait_for_selector|assert_text|...", "selector": "...", "value": "...", "url": "...", "assertion": "..."}}

Use best-practice selectors (data-testid > aria-label > text > css).
"""
        raw, _ = await self._call_llm(
            "You are a Playwright automation expert. Return ONLY a JSON action object.",
            step_prompt,
        )
        try:
            action_obj = json.loads(raw)
            await self._apply_playwright_action(page, action_obj, {})
            return f"[STEP {step_num}] PASS: {action}"
        except Exception as exc:
            return f"[STEP {step_num}] WARN: {action} — {exc}"

    async def _apply_playwright_action(self, page: Page, action_obj: dict, creds: dict) -> None:
        act = action_obj.get("playwright_action", "")
        selector = action_obj.get("selector", "")
        value = action_obj.get("value", "")

        # Replace credential placeholders
        if value == "username":
            value = creds.get("username", "")
        elif value == "password":
            value = creds.get("password", "")

        if act == "goto":
            await page.goto(action_obj.get("url", "/"), timeout=settings.PLAYWRIGHT_TIMEOUT)
        elif act == "click":
            await page.click(selector, timeout=settings.PLAYWRIGHT_TIMEOUT)
        elif act == "fill":
            await page.fill(selector, value, timeout=settings.PLAYWRIGHT_TIMEOUT)
        elif act == "wait_for_selector":
            await page.wait_for_selector(selector, timeout=settings.PLAYWRIGHT_TIMEOUT)
        elif act == "assert_text":
            await page.wait_for_selector(f"text={action_obj.get('assertion', '')}", timeout=10000)
        elif act == "press":
            await page.press(selector, value)
        elif act == "select_option":
            await page.select_option(selector, value)
        elif act == "check":
            await page.check(selector)
        elif act == "screenshot":
            await page.screenshot(path=str(self.reports_dir / f"manual_{int(time.time())}.png"))

    async def _validate_result(
        self,
        test_case: dict,
        step_logs: list[str],
        console_errors: list[dict],
        network_errors: list[dict],
    ) -> dict:
        prompt = f"""
Test case: {test_case.get('tc_id')}
Expected result: {test_case.get('expected_result')}
Step logs: {json.dumps(step_logs)}
Console errors: {json.dumps(console_errors)}
Network errors: {json.dumps(network_errors)}

Based on this evidence, determine the test result.
Return JSON: {{"status": "passed|failed|blocked", "actual_result": "...", "failure_reason": "..."}}
"""
        raw, _ = await self._call_llm(
            "You are a QA analyst evaluating test execution results. Be precise.",
            prompt,
        )
        try:
            return json.loads(raw)
        except Exception:
            return {"status": "passed" if not console_errors and not network_errors else "failed"}

    async def _screenshot(self, page: Page, tc_id: str, suffix: Any) -> str | None:
        try:
            path = self.reports_dir / f"{tc_id}_step{suffix}.png"
            await page.screenshot(path=str(path), full_page=True)
            return str(path)
        except Exception:
            return None

    def _capture_console(self, msg: ConsoleMessage) -> None:
        self._console_logs.append({
            "type": msg.type,
            "text": msg.text,
            "location": str(msg.location),
        })

    def _capture_request(self, request: Request) -> None:
        self._network_logs.append({
            "method": request.method,
            "url": request.url,
            "type": "request",
        })

    def _capture_response(self, response: Response) -> None:
        for entry in self._network_logs:
            if entry.get("url") == response.url and entry.get("type") == "request":
                entry["status"] = response.status
                entry["type"] = "response"
                break
