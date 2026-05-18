import csv
import io
import json
from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from python_slugify import slugify

from app.database import get_db, AsyncSessionLocal
from app.models.database import (
    Project, ProjectMember, Requirement, Epic, UserStory,
    TestCase, TestRun, Bug, AgentLog,
)
from app.models.schemas import ProjectCreate, ProjectResponse
from app.api.routes.auth import get_current_user
from app.models.database import User

router = APIRouter()


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    slug = slugify(data.name)
    existing = await db.execute(select(Project).where(Project.slug == slug))
    if existing.scalar_one_or_none():
        import uuid as _uuid
        slug = f"{slug}-{str(_uuid.uuid4())[:8]}"

    project = Project(
        name=data.name,
        slug=slug,
        description=data.description,
        app_url=data.app_url,
        api_base_url=data.api_base_url,
    )
    db.add(project)
    await db.flush()

    member = ProjectMember(project_id=project.id, user_id=user.id, role=user.role)
    db.add(member)
    await db.flush()
    await db.refresh(project)
    return project


@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Project)
        .join(ProjectMember, ProjectMember.project_id == Project.id)
        .where(ProjectMember.user_id == user.id)
        .order_by(Project.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@router.get("/{project_id}/stats")
async def get_project_stats(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Aggregate counts for dashboard stats cards."""

    async def count(model, *where):
        r = await db.execute(select(func.count()).select_from(model).where(*where))
        return r.scalar() or 0

    req_total = await count(Requirement, Requirement.project_id == project_id)
    req_approved = await count(
        Requirement,
        Requirement.project_id == project_id,
        Requirement.status == "approved",
    )

    # Stories require join through Epic
    stories_result = await db.execute(
        select(func.count())
        .select_from(UserStory)
        .join(Epic, UserStory.epic_id == Epic.id)
        .where(Epic.project_id == project_id)
    )
    stories_total = stories_result.scalar() or 0

    stories_approved_result = await db.execute(
        select(func.count())
        .select_from(UserStory)
        .join(Epic, UserStory.epic_id == Epic.id)
        .where(Epic.project_id == project_id, UserStory.status == "approved")
    )
    stories_approved = stories_approved_result.scalar() or 0

    # Test cases require join through UserStory → Epic
    tc_result = await db.execute(
        select(func.count())
        .select_from(TestCase)
        .join(UserStory, TestCase.story_id == UserStory.id, isouter=True)
        .join(Epic, UserStory.epic_id == Epic.id, isouter=True)
        .where(Epic.project_id == project_id)
    )
    tc_total = tc_result.scalar() or 0

    tc_approved_result = await db.execute(
        select(func.count())
        .select_from(TestCase)
        .join(UserStory, TestCase.story_id == UserStory.id, isouter=True)
        .join(Epic, UserStory.epic_id == Epic.id, isouter=True)
        .where(Epic.project_id == project_id, TestCase.status == "approved")
    )
    tc_approved = tc_approved_result.scalar() or 0

    runs_total = await count(TestRun, TestRun.project_id == project_id)
    bugs_open_result = await db.execute(
        select(func.count())
        .select_from(Bug)
        .join(TestRun, Bug.run_id == TestRun.id, isouter=True)
        .where(TestRun.project_id == project_id, Bug.status == "open")
    )
    bugs_open = bugs_open_result.scalar() or 0

    last_log_result = await db.execute(
        select(AgentLog)
        .where(AgentLog.project_id == project_id)
        .order_by(AgentLog.created_at.desc())
        .limit(1)
    )
    last_log = last_log_result.scalar_one_or_none()

    return {
        "project_id": str(project_id),
        "requirements": {"total": req_total, "approved": req_approved},
        "stories": {"total": stories_total, "approved": stories_approved},
        "test_cases": {"total": tc_total, "approved": tc_approved},
        "test_runs": {"total": runs_total},
        "bugs": {"open": bugs_open},
        "last_agent_activity": {
            "agent": last_log.agent_name if last_log else None,
            "phase": last_log.phase if last_log else None,
            "status": last_log.status if last_log else None,
            "timestamp": last_log.created_at.isoformat() if last_log else None,
        },
    }


@router.get("/{project_id}/agent-logs")
async def get_agent_logs(
    project_id: UUID,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Recent agent activity log — poll this to track background job progress."""
    result = await db.execute(
        select(AgentLog)
        .where(AgentLog.project_id == project_id)
        .order_by(AgentLog.created_at.desc())
        .limit(min(limit, 100))
    )
    logs = result.scalars().all()
    return [
        {
            "id": str(log.id),
            "agent": log.agent_name,
            "phase": log.phase,
            "status": log.status,
            "input_summary": log.input_summary,
            "output_summary": log.output_summary,
            "tokens_used": log.tokens_used,
            "error": log.error,
            "timestamp": log.created_at.isoformat(),
        }
        for log in logs
    ]


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Project not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    await db.flush()
    await db.refresh(project)
    return project


@router.get("/{project_id}/roi")
async def get_project_roi(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """ROI metrics: coverage %, time saved estimate, defect escape cost averted, token cost."""

    # Token cost (Claude Sonnet 4.6 pricing: ~$3/MTok input, $15/MTok output — use blended ~$9/MTok)
    COST_PER_TOKEN = 9.0 / 1_000_000

    logs_result = await db.execute(
        select(AgentLog).where(AgentLog.project_id == project_id)
    )
    logs = logs_result.scalars().all()
    total_tokens = sum(l.tokens_used or 0 for l in logs)
    total_cost_usd = round(total_tokens * COST_PER_TOKEN, 4)

    # Phase breakdown
    phase_costs = {}
    for log in logs:
        phase_costs.setdefault(log.phase, {"tokens": 0, "cost_usd": 0.0})
        phase_costs[log.phase]["tokens"] += log.tokens_used or 0
        phase_costs[log.phase]["cost_usd"] = round(
            phase_costs[log.phase]["tokens"] * COST_PER_TOKEN, 4
        )

    # Test coverage: what % of requirements have at least one test case
    req_result = await db.execute(
        select(Requirement).where(Requirement.project_id == project_id)
    )
    requirements = req_result.scalars().all()

    covered = 0
    for req in requirements:
        tc_check = await db.execute(
            select(func.count())
            .select_from(TestCase)
            .join(UserStory, TestCase.story_id == UserStory.id, isouter=True)
            .join(Epic, UserStory.epic_id == Epic.id, isouter=True)
            .where(
                Epic.project_id == project_id,
                TestCase.requirement_ref == req.req_id,
            )
        )
        if (tc_check.scalar() or 0) > 0:
            covered += 1

    req_count = len(requirements)
    coverage_pct = round((covered / req_count * 100) if req_count > 0 else 0, 1)

    # Bugs caught by automation
    bugs_result = await db.execute(
        select(func.count())
        .select_from(Bug)
        .join(TestRun, Bug.run_id == TestRun.id, isouter=True)
        .where(TestRun.project_id == project_id)
    )
    bugs_caught = bugs_result.scalar() or 0

    # Time-saved estimate:
    # Manual test writing: ~30 min/test case
    # Manual test execution: ~15 min/test case/run
    # Bug report writing: ~45 min/bug
    tc_count_result = await db.execute(
        select(func.count())
        .select_from(TestCase)
        .join(UserStory, TestCase.story_id == UserStory.id, isouter=True)
        .join(Epic, UserStory.epic_id == Epic.id, isouter=True)
        .where(Epic.project_id == project_id)
    )
    tc_count = tc_count_result.scalar() or 0

    runs_result = await db.execute(
        select(func.count()).select_from(TestRun).where(TestRun.project_id == project_id)
    )
    runs_count = runs_result.scalar() or 0

    hours_writing = round(tc_count * 0.5, 1)
    hours_execution = round(tc_count * runs_count * 0.25, 1)
    hours_bug_reports = round(bugs_caught * 0.75, 1)
    hours_requirements = round(req_count * 0.5, 1)
    stories_count_result = await db.execute(
        select(func.count()).select_from(UserStory)
        .join(Epic, UserStory.epic_id == Epic.id)
        .where(Epic.project_id == project_id)
    )
    hours_stories = round((stories_count_result.scalar() or 0) * 0.5, 1)
    total_hours_saved = hours_writing + hours_execution + hours_bug_reports + hours_requirements + hours_stories

    # Defect escape cost averted (industry avg: $10K per escaped defect)
    defect_escape_averted_usd = bugs_caught * 10_000

    return {
        "project_id": str(project_id),
        "generated_at": datetime.utcnow().isoformat(),
        "cost": {
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost_usd,
            "by_phase": phase_costs,
        },
        "coverage": {
            "requirements_total": req_count,
            "requirements_covered": covered,
            "coverage_pct": coverage_pct,
        },
        "time_saved": {
            "hours_requirement_analysis": hours_requirements,
            "hours_test_case_writing": hours_writing,
            "hours_test_execution": hours_execution,
            "hours_bug_report_writing": hours_bug_reports,
            "total_hours_saved": total_hours_saved,
            "estimated_cost_saved_usd": round(total_hours_saved * 150, 0),
        },
        "quality": {
            "bugs_caught": bugs_caught,
            "defect_escape_averted_usd": defect_escape_averted_usd,
            "test_cases_generated": tc_count,
            "test_runs": runs_count,
        },
        "roi_multiplier": round(
            (total_hours_saved * 150 + defect_escape_averted_usd) / max(total_cost_usd, 0.01), 1
        ),
    }


@router.post("/{project_id}/detect-gaps", status_code=202)
async def detect_gaps(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """AI scans all stories for missing edge cases, ambiguous ACs, security gaps."""
    result = await db.execute(
        select(UserStory)
        .join(Epic, UserStory.epic_id == Epic.id)
        .where(Epic.project_id == project_id)
        .limit(50)
    )
    stories = result.scalars().all()
    if not stories:
        raise HTTPException(400, "No stories found. Generate stories first.")

    story_data = [
        {
            "story_id": s.story_id,
            "title": s.title,
            "role": s.role,
            "goal": s.goal,
            "acceptance_criteria": s.acceptance_criteria or [],
            "positive_scenarios": s.positive_scenarios or [],
            "negative_scenarios": s.negative_scenarios or [],
        }
        for s in stories
    ]
    project_id_str = str(project_id)

    async def run_gap_agent():
        from app.agents.gap_agent import GapAgent
        async with AsyncSessionLocal() as bg_db:
            try:
                agent = GapAgent()
                result_data = await agent.run(stories=story_data)
                log = AgentLog(
                    project_id=project_id,
                    agent_name="gap_agent",
                    phase="gap_detection",
                    status="completed",
                    output_summary=json.dumps(result_data.get("summary", {})),
                    tokens_used=result_data.get("_meta", {}).get("tokens_used", 0),
                    reasoning_trace=json.dumps(result_data.get("gaps", [])),
                )
                bg_db.add(log)
                await bg_db.commit()
            except Exception as exc:
                await bg_db.rollback()
                log = AgentLog(
                    project_id=project_id,
                    agent_name="gap_agent",
                    phase="gap_detection",
                    status="error",
                    error=str(exc),
                )
                bg_db.add(log)
                await bg_db.commit()
                raise

    background_tasks.add_task(run_gap_agent)
    return {"status": "processing", "message": "Gap analysis started — check /agent-logs for results"}


@router.get("/{project_id}/gaps")
async def get_gaps(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return the most recent gap detection results."""
    result = await db.execute(
        select(AgentLog)
        .where(
            AgentLog.project_id == project_id,
            AgentLog.agent_name == "gap_agent",
            AgentLog.status == "completed",
        )
        .order_by(AgentLog.created_at.desc())
        .limit(1)
    )
    log = result.scalar_one_or_none()
    if not log:
        return {"gaps": [], "summary": None, "last_run": None}
    try:
        gaps = json.loads(log.reasoning_trace or "[]")
        summary = json.loads(log.output_summary or "{}")
    except Exception:
        gaps, summary = [], {}
    return {"gaps": gaps, "summary": summary, "last_run": log.created_at.isoformat()}


@router.get("/{project_id}/export")
async def export_project(
    project_id: UUID,
    format: str = "json",
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Export full project data — requirements, stories, test cases, bugs — as JSON or CSV."""
    reqs_result = await db.execute(
        select(Requirement).where(Requirement.project_id == project_id)
    )
    requirements = reqs_result.scalars().all()

    stories_result = await db.execute(
        select(UserStory)
        .join(Epic, UserStory.epic_id == Epic.id)
        .where(Epic.project_id == project_id)
    )
    stories = stories_result.scalars().all()

    tc_result = await db.execute(
        select(TestCase)
        .join(UserStory, TestCase.story_id == UserStory.id, isouter=True)
        .join(Epic, UserStory.epic_id == Epic.id, isouter=True)
        .where(Epic.project_id == project_id)
    )
    test_cases = tc_result.scalars().all()

    bugs_result = await db.execute(
        select(Bug)
        .join(TestRun, Bug.run_id == TestRun.id, isouter=True)
        .where(TestRun.project_id == project_id)
    )
    bugs = bugs_result.scalars().all()

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["=== REQUIREMENTS ==="])
        writer.writerow(["req_id", "title", "description", "type", "priority", "status", "confidence"])
        for r in requirements:
            writer.writerow([r.req_id, r.title, r.description, r.req_type, r.priority, r.status, r.confidence_score])

        writer.writerow([])
        writer.writerow(["=== USER STORIES ==="])
        writer.writerow(["story_id", "title", "role", "goal", "priority", "status", "story_points"])
        for s in stories:
            writer.writerow([s.story_id, s.title, s.role, s.goal, s.priority, s.status, s.story_points])

        writer.writerow([])
        writer.writerow(["=== TEST CASES ==="])
        writer.writerow(["tc_id", "title", "type", "severity", "priority", "status", "automation"])
        for tc in test_cases:
            writer.writerow([tc.tc_id, tc.title, tc.test_type, tc.severity, tc.priority, tc.status, tc.automation_feasibility])

        writer.writerow([])
        writer.writerow(["=== BUGS ==="])
        writer.writerow(["bug_id", "title", "severity", "priority", "status", "root_cause"])
        for b in bugs:
            writer.writerow([b.bug_id, b.title, b.severity, b.priority, b.status, b.root_cause or ""])

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=project_{project_id}_export.csv"},
        )

    # JSON export
    data = {
        "project_id": str(project_id),
        "exported_at": datetime.utcnow().isoformat(),
        "requirements": [
            {
                "req_id": r.req_id, "title": r.title, "description": r.description,
                "type": r.req_type, "priority": r.priority, "status": r.status,
                "confidence_score": r.confidence_score,
                "assumptions": r.assumptions or [], "risks": r.risks or [],
            }
            for r in requirements
        ],
        "stories": [
            {
                "story_id": s.story_id, "title": s.title, "role": s.role,
                "goal": s.goal, "business_value": s.business_value,
                "acceptance_criteria": s.acceptance_criteria or [],
                "priority": s.priority, "status": s.status, "story_points": s.story_points,
            }
            for s in stories
        ],
        "test_cases": [
            {
                "tc_id": tc.tc_id, "title": tc.title, "type": tc.test_type,
                "test_steps": tc.test_steps or [], "expected_result": tc.expected_result,
                "severity": tc.severity, "priority": tc.priority, "status": tc.status,
                "story_ref": tc.story_ref, "requirement_ref": tc.requirement_ref,
            }
            for tc in test_cases
        ],
        "bugs": [
            {
                "bug_id": b.bug_id, "title": b.title, "description": b.description,
                "severity": b.severity, "priority": b.priority, "status": b.status,
                "root_cause": b.root_cause, "suggested_fix": b.suggested_fix,
            }
            for b in bugs
        ],
    }
    json_bytes = json.dumps(data, indent=2).encode()
    return StreamingResponse(
        iter([json_bytes]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=project_{project_id}_export.json"},
    )
