"""
Automation routes — generate Playwright scripts, download framework zip.
"""
import io
import json
import zipfile
from pathlib import Path
from typing import List
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, AsyncSessionLocal
from app.models.database import AutomationScript, TestCase, TestRun, AgentLog, User, Epic, UserStory
from app.models.schemas import AutomationScriptResponse
from app.agents.automation_agent import AutomationAgent
from app.api.routes.auth import get_current_user

router = APIRouter()


@router.post("/generate", status_code=202)
async def generate_automation(
    project_id: UUID,
    run_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Generate Playwright TypeScript scripts for all signed-off test cases in a run."""
    run_result = await db.execute(select(TestRun).where(TestRun.id == run_id))
    run = run_result.scalar_one_or_none()
    if not run:
        raise HTTPException(404, "Test run not found")

    tc_result = await db.execute(
        select(TestCase)
        .join(UserStory, TestCase.story_id == UserStory.id, isouter=True)
        .join(Epic, UserStory.epic_id == Epic.id, isouter=True)
        .where(Epic.project_id == project_id, TestCase.status == "approved")
    )
    test_cases = tc_result.scalars().all()

    # Serialize all ORM data before request session closes
    tc_snapshots = [
        {
            "id": str(tc.id),
            "tc_id": tc.tc_id,
            "title": tc.title,
            "test_type": tc.test_type,
            "preconditions": tc.preconditions or [],
            "test_steps": tc.test_steps or [],
            "test_data": tc.test_data or {},
            "expected_result": tc.expected_result,
            "requirement_ref": tc.requirement_ref,
            "story_ref": tc.story_ref,
        }
        for tc in test_cases
    ]
    app_url = run.app_url or ""
    project_id_str = str(project_id)

    async def run_agent():
        async with AsyncSessionLocal() as bg_db:
            try:
                agent = AutomationAgent()
                for tc in tc_snapshots:
                    from uuid import UUID as _UUID
                    tc_uuid = _UUID(tc["id"])
                    existing = await bg_db.execute(
                        select(AutomationScript).where(AutomationScript.test_case_id == tc_uuid)
                    )
                    if existing.scalar_one_or_none():
                        continue

                    result = await agent.run(
                        test_case={
                            "tc_id": tc["tc_id"],
                            "title": tc["title"],
                            "test_type": tc["test_type"],
                            "preconditions": tc["preconditions"],
                            "test_steps": tc["test_steps"],
                            "test_data": tc["test_data"],
                            "expected_result": tc["expected_result"],
                            "requirement_ref": tc["requirement_ref"],
                            "story_ref": tc["story_ref"],
                        },
                        project_name=project_id_str,
                        base_url=app_url,
                    )

                    for po in result.get("page_objects", []):
                        script = AutomationScript(
                            test_case_id=tc_uuid,
                            script_id=f"PO-{tc['tc_id']}",
                            file_path=po.get("file_path", f"src/pages/{tc['tc_id']}.ts"),
                            content=po.get("content", ""),
                            language="typescript",
                            framework="playwright",
                            generation_notes="Page Object",
                        )
                        bg_db.add(script)

                    spec = result.get("test_spec", {})
                    if spec:
                        script = AutomationScript(
                            test_case_id=tc_uuid,
                            script_id=f"SPEC-{tc['tc_id']}",
                            file_path=spec.get("file_path", f"tests/{tc['tc_id']}.spec.ts"),
                            content=spec.get("content", ""),
                            language="typescript",
                            framework="playwright",
                            generation_notes=result.get("generation_notes"),
                        )
                        bg_db.add(script)

                log = AgentLog(
                    project_id=project_id,
                    agent_name="automation_agent",
                    phase="phase_8_automation",
                    status="completed",
                    output_summary=f"{len(tc_snapshots)} scripts generated",
                )
                bg_db.add(log)
                await bg_db.commit()
            except Exception as exc:
                await bg_db.rollback()
                log = AgentLog(
                    project_id=project_id,
                    agent_name="automation_agent",
                    phase="phase_8_automation",
                    status="error",
                    error=str(exc),
                )
                bg_db.add(log)
                await bg_db.commit()
                raise

    background_tasks.add_task(run_agent)
    return {"status": "processing", "message": "Automation generation started"}


@router.get("", response_model=List[AutomationScriptResponse])
async def list_scripts(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(AutomationScript)
        .join(TestCase, AutomationScript.test_case_id == TestCase.id)
        .join(UserStory, TestCase.story_id == UserStory.id, isouter=True)
        .join(Epic, UserStory.epic_id == Epic.id, isouter=True)
        .where(Epic.project_id == project_id)
    )
    return result.scalars().all()


@router.get("/download/{project_id}")
async def download_framework(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Download the complete Playwright framework as a ZIP archive."""
    result = await db.execute(
        select(AutomationScript)
        .join(TestCase, AutomationScript.test_case_id == TestCase.id)
        .join(UserStory, TestCase.story_id == UserStory.id, isouter=True)
        .join(Epic, UserStory.epic_id == Epic.id, isouter=True)
        .where(Epic.project_id == project_id)
    )
    scripts = result.scalars().all()

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for script in scripts:
            zf.writestr(script.file_path, script.content)

        # Add playwright.config.ts and package.json
        zf.writestr("playwright.config.ts", _playwright_config())
        zf.writestr("package.json", _package_json())
        zf.writestr("src/fixtures/auth.ts", _auth_fixture())

    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=playwright-framework-{project_id}.zip"},
    )


def _playwright_config() -> str:
    return """import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 4 : undefined,
  reporter: [['html', { open: 'never' }], ['json', { outputFile: 'results.json' }]],
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'on-first-retry',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'Mobile Chrome', use: { ...devices['Pixel 5'] } },
  ],
});
"""


def _package_json() -> str:
    return json.dumps({
        "name": "qagent-playwright-framework",
        "version": "1.0.0",
        "scripts": {
            "test": "playwright test",
            "test:headed": "playwright test --headed",
            "test:ui": "playwright test --ui",
            "report": "playwright show-report"
        },
        "devDependencies": {
            "@playwright/test": "^1.44.0",
            "@types/node": "^20.0.0",
            "typescript": "^5.0.0"
        }
    }, indent=2)


def _auth_fixture() -> str:
    return """import { test as base, Page } from '@playwright/test';

type AuthFixtures = { authenticatedPage: Page };

export const test = base.extend<AuthFixtures>({
  authenticatedPage: async ({ page }, use) => {
    const baseUrl = process.env.BASE_URL || 'http://localhost:3000';
    await page.goto(`${baseUrl}/login`);
    await page.fill('[data-testid="email"]', process.env.TEST_USER || 'test@example.com');
    await page.fill('[data-testid="password"]', process.env.TEST_PASSWORD || 'Test@1234');
    await page.click('[data-testid="submit"]');
    await page.waitForURL('**/dashboard');
    await use(page);
  },
});

export { expect } from '@playwright/test';
"""
