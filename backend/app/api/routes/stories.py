import uuid
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, AsyncSessionLocal
from app.models.database import UserStory, Requirement, Epic, AgentLog, User
from app.models.schemas import UserStoryCreate, UserStoryResponse, UserStoryUpdate
from app.agents.story_agent import StoryAgent
from app.api.routes.auth import get_current_user

router = APIRouter()


async def _next_story_id(db: AsyncSession) -> str:
    result = await db.execute(select(func.count()).select_from(UserStory))
    count = result.scalar() or 0
    return f"US-{(count + 1):03d}"


@router.post("/generate", status_code=202)
async def generate_stories(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """AI generates user stories from all approved requirements in the project."""
    result = await db.execute(
        select(Requirement)
        .where(Requirement.project_id == project_id, Requirement.status == "approved")
    )
    requirements = result.scalars().all()
    if not requirements:
        raise HTTPException(400, "No approved requirements found. Approve requirements first.")

    req_data = [
        {
            "req_id": r.req_id,
            "title": r.title,
            "description": r.description,
            "req_type": r.req_type,
            "priority": r.priority,
            "acceptance_criteria": [],
            "assumptions": r.assumptions or [],
        }
        for r in requirements
    ]

    # Capture only primitives — never pass the request-scoped db session into a background task
    project_id_str = str(project_id)

    async def run_agent():
        # Open a fresh session — the request session is closed by the time this runs
        async with AsyncSessionLocal() as bg_db:
            try:
                agent = StoryAgent()
                result_data = await agent.run(project_id=project_id_str, requirements=req_data)

                for epic_data in result_data.get("epics", []):
                    # Count existing epics to generate a safe ID
                    count_result = await bg_db.execute(
                        select(func.count()).select_from(Epic).where(Epic.project_id == project_id)
                    )
                    epic_count = count_result.scalar() or 0
                    epic_id = epic_data.get("epic_id") or f"EPIC-{(epic_count + 1):03d}"

                    epic = Epic(
                        project_id=project_id,
                        epic_id=epic_id,
                        title=epic_data.get("title", ""),
                        description=epic_data.get("description"),
                    )
                    bg_db.add(epic)
                    await bg_db.flush()

                    for story_data in epic_data.get("stories", []):
                        story_id = story_data.get("story_id") or await _next_story_id(bg_db)
                        story = UserStory(
                            epic_id=epic.id,
                            story_id=story_id,
                            title=story_data.get("title", ""),
                            role=story_data.get("role", "user"),
                            goal=story_data.get("goal", ""),
                            business_value=story_data.get("business_value", ""),
                            acceptance_criteria=story_data.get("acceptance_criteria", []),
                            positive_scenarios=story_data.get("positive_scenarios", []),
                            negative_scenarios=story_data.get("negative_scenarios", []),
                            ui_validations=story_data.get("ui_validations", []),
                            api_validations=story_data.get("api_validations", []),
                            security_validations=story_data.get("security_validations", []),
                            boundary_conditions=story_data.get("boundary_conditions", []),
                            priority=story_data.get("priority", "medium"),
                            risk_level=story_data.get("risk_level", "medium"),
                            story_points=story_data.get("story_points"),
                        )
                        bg_db.add(story)

                log = AgentLog(
                    project_id=project_id,
                    agent_name="story_agent",
                    phase="phase_2_stories",
                    status="completed",
                    tokens_used=result_data.get("_meta", {}).get("tokens_used", 0),
                    output_summary=f"{sum(len(e.get('stories', [])) for e in result_data.get('epics', []))} stories in {len(result_data.get('epics', []))} epics",
                )
                bg_db.add(log)
                await bg_db.commit()
            except Exception as exc:
                await bg_db.rollback()
                log = AgentLog(
                    project_id=project_id,
                    agent_name="story_agent",
                    phase="phase_2_stories",
                    status="error",
                    error=str(exc),
                )
                bg_db.add(log)
                await bg_db.commit()
                raise

    background_tasks.add_task(run_agent)
    return {"status": "processing", "message": "Story generation started", "project_id": project_id_str}


@router.get("", response_model=List[UserStoryResponse])
async def list_stories(
    project_id: UUID,
    epic_id: Optional[UUID] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = (
        select(UserStory)
        .join(Epic, UserStory.epic_id == Epic.id)
        .where(Epic.project_id == project_id)
    )
    if epic_id:
        query = query.where(UserStory.epic_id == epic_id)
    if status:
        query = query.where(UserStory.status == status)
    result = await db.execute(query.order_by(UserStory.story_id))
    return result.scalars().all()


@router.get("/{story_id}", response_model=UserStoryResponse)
async def get_story(
    story_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(UserStory).where(UserStory.id == story_id))
    story = result.scalar_one_or_none()
    if not story:
        raise HTTPException(404, "Story not found")
    return story


@router.patch("/approve-all")
async def approve_all_stories(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Bulk-approve all draft/review stories for a project."""
    result = await db.execute(
        select(UserStory)
        .join(Epic, UserStory.epic_id == Epic.id)
        .where(Epic.project_id == project_id, UserStory.status.in_(["draft", "review"]))
    )
    stories = result.scalars().all()
    for s in stories:
        s.status = "approved"
    await db.flush()
    return {"approved_count": len(stories), "project_id": str(project_id)}


@router.patch("/{story_id}/approve")
async def approve_story(
    story_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(UserStory).where(UserStory.id == story_id))
    story = result.scalar_one_or_none()
    if not story:
        raise HTTPException(404, "Story not found")
    story.status = "approved"
    await db.flush()
    return {"status": "approved", "id": str(story_id)}


@router.patch("/{story_id}", response_model=UserStoryResponse)
async def update_story(
    story_id: UUID,
    data: UserStoryUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Human edits: fix AI mistakes, adjust acceptance criteria, re-point story."""
    result = await db.execute(select(UserStory).where(UserStory.id == story_id))
    story = result.scalar_one_or_none()
    if not story:
        raise HTTPException(404, "Story not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(story, field, value)
    await db.flush()
    await db.refresh(story)
    return story
