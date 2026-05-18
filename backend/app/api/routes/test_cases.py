from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, AsyncSessionLocal
from app.models.database import TestCase, UserStory, Epic, AgentLog, User
from app.models.schemas import TestCaseCreate, TestCaseResponse, TestCaseUpdate
from app.agents.test_case_agent import TestCaseAgent
from app.api.routes.auth import get_current_user

router = APIRouter()


async def _next_tc_id(db: AsyncSession) -> str:
    result = await db.execute(select(func.count()).select_from(TestCase))
    count = result.scalar() or 0
    return f"TC-{(count + 1):03d}"


@router.post("/generate", status_code=202)
async def generate_test_cases(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """AI generates test cases from all approved stories in the project."""
    result = await db.execute(
        select(UserStory)
        .join(Epic, UserStory.epic_id == Epic.id)
        .where(Epic.project_id == project_id, UserStory.status == "approved")
    )
    stories = result.scalars().all()
    if not stories:
        raise HTTPException(400, "No approved stories found. Approve stories first.")

    story_data = [
        {
            "story_id": s.story_id,
            "title": s.title,
            "role": s.role,
            "goal": s.goal,
            "business_value": s.business_value,
            "acceptance_criteria": s.acceptance_criteria or [],
            "positive_scenarios": s.positive_scenarios or [],
            "negative_scenarios": s.negative_scenarios or [],
            "ui_validations": s.ui_validations or [],
            "api_validations": s.api_validations or [],
            "security_validations": s.security_validations or [],
            "boundary_conditions": s.boundary_conditions or [],
            "priority": s.priority,
            "risk_level": s.risk_level,
        }
        for s in stories
    ]

    # Map story_id string → db UUID (captured as primitive dict before session closes)
    story_id_map = {s.story_id: str(s.id) for s in stories}
    project_id_str = str(project_id)

    async def run_agent():
        async with AsyncSessionLocal() as bg_db:
            try:
                agent = TestCaseAgent()
                result_data = await agent.run(project_id=project_id_str, stories=story_data)

                for tc_data in result_data.get("test_cases", []):
                    tc_id = tc_data.get("tc_id") or await _next_tc_id(bg_db)
                    story_ref = tc_data.get("story_ref")
                    story_db_id = story_id_map.get(story_ref) if story_ref else None

                    tc = TestCase(
                        story_id=story_db_id,
                        tc_id=tc_id,
                        title=tc_data.get("title", ""),
                        description=tc_data.get("description"),
                        test_type=tc_data.get("test_type", "functional"),
                        preconditions=tc_data.get("preconditions", []),
                        test_steps=tc_data.get("test_steps", []),
                        test_data=tc_data.get("test_data", {}),
                        expected_result=tc_data.get("expected_result", ""),
                        priority=tc_data.get("priority", "medium"),
                        severity=tc_data.get("severity", "medium"),
                        automation_feasibility=tc_data.get("automation_feasibility", "automatable"),
                        tags=tc_data.get("tags", []),
                        requirement_ref=tc_data.get("requirement_ref"),
                        story_ref=tc_data.get("story_ref"),
                        acceptance_criteria_ref=tc_data.get("acceptance_criteria_ref"),
                    )
                    bg_db.add(tc)

                log = AgentLog(
                    project_id=project_id,
                    agent_name="test_case_agent",
                    phase="phase_3_test_cases",
                    status="completed",
                    tokens_used=result_data.get("_meta", {}).get("tokens_used", 0),
                    output_summary=f"{len(result_data.get('test_cases', []))} test cases",
                )
                bg_db.add(log)
                await bg_db.commit()
            except Exception as exc:
                await bg_db.rollback()
                log = AgentLog(
                    project_id=project_id,
                    agent_name="test_case_agent",
                    phase="phase_3_test_cases",
                    status="error",
                    error=str(exc),
                )
                bg_db.add(log)
                await bg_db.commit()
                raise

    background_tasks.add_task(run_agent)
    return {"status": "processing", "message": "Test case generation started", "project_id": project_id_str}


@router.get("", response_model=List[TestCaseResponse])
async def list_test_cases(
    project_id: UUID,
    story_id: Optional[UUID] = None,
    test_type: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = (
        select(TestCase)
        .join(UserStory, TestCase.story_id == UserStory.id, isouter=True)
        .join(Epic, UserStory.epic_id == Epic.id, isouter=True)
        .where(Epic.project_id == project_id)
    )
    if story_id:
        query = query.where(TestCase.story_id == story_id)
    if test_type:
        query = query.where(TestCase.test_type == test_type)
    if status:
        query = query.where(TestCase.status == status)
    result = await db.execute(query.order_by(TestCase.tc_id))
    return result.scalars().all()


@router.get("/{tc_id}", response_model=TestCaseResponse)
async def get_test_case(
    tc_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(TestCase).where(TestCase.id == tc_id))
    tc = result.scalar_one_or_none()
    if not tc:
        raise HTTPException(404, "Test case not found")
    return tc


@router.patch("/approve-all")
async def approve_all_test_cases(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Bulk-approve all draft/review test cases for a project (confidence ≥ 0.7)."""
    result = await db.execute(
        select(TestCase)
        .join(UserStory, TestCase.story_id == UserStory.id, isouter=True)
        .join(Epic, UserStory.epic_id == Epic.id, isouter=True)
        .where(
            Epic.project_id == project_id,
            TestCase.status.in_(["draft", "review"]),
            TestCase.confidence_score >= 0.7,
        )
    )
    test_cases = result.scalars().all()
    for tc in test_cases:
        tc.status = "approved"
    await db.flush()
    return {"approved_count": len(test_cases), "project_id": str(project_id)}


@router.patch("/{tc_id}/approve")
async def approve_test_case(
    tc_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(TestCase).where(TestCase.id == tc_id))
    tc = result.scalar_one_or_none()
    if not tc:
        raise HTTPException(404, "Test case not found")
    tc.status = "approved"
    await db.flush()
    return {"status": "approved", "id": str(tc_id)}


@router.patch("/{tc_id}", response_model=TestCaseResponse)
async def update_test_case(
    tc_id: UUID,
    data: TestCaseUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Human edits: fix test steps, adjust severity, add tags."""
    result = await db.execute(select(TestCase).where(TestCase.id == tc_id))
    tc = result.scalar_one_or_none()
    if not tc:
        raise HTTPException(404, "Test case not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(tc, field, value)
    await db.flush()
    await db.refresh(tc)
    return tc
