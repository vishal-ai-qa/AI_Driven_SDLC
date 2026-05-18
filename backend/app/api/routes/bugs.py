from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.database import Bug, User
from app.models.schemas import BugCreate, BugResponse
from app.api.routes.auth import get_current_user

router = APIRouter()


@router.get("", response_model=List[BugResponse])
async def list_bugs(
    project_id: Optional[UUID] = None,
    run_id: Optional[UUID] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(Bug)
    if run_id:
        query = query.where(Bug.run_id == run_id)
    if severity:
        query = query.where(Bug.severity == severity)
    if status:
        query = query.where(Bug.status == status)
    result = await db.execute(query.order_by(Bug.created_at.desc()))
    return result.scalars().all()


@router.get("/{bug_id}", response_model=BugResponse)
async def get_bug(
    bug_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Bug).where(Bug.id == bug_id))
    bug = result.scalar_one_or_none()
    if not bug:
        raise HTTPException(404, "Bug not found")
    return bug


@router.post("", response_model=BugResponse, status_code=201)
async def create_bug(
    data: BugCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from sqlalchemy import func
    count_result = await db.execute(select(func.count()).select_from(Bug))
    count = count_result.scalar() or 0
    bug = Bug(
        run_id=data.run_id,
        execution_id=data.execution_id,
        bug_id=f"BUG-{(count + 1):03d}",
        title=data.title,
        description=data.description,
        environment=data.environment,
        steps_to_reproduce=data.steps_to_reproduce,
        expected_result=data.expected_result,
        actual_result=data.actual_result,
        severity=data.severity,
        priority=data.priority,
        root_cause=data.root_cause,
        suggested_fix=data.suggested_fix,
        tags=data.tags,
        is_flaky=data.is_flaky,
        is_environment_issue=data.is_environment_issue,
    )
    db.add(bug)
    await db.flush()
    await db.refresh(bug)
    return bug


@router.patch("/{bug_id}/status")
async def update_bug_status(
    bug_id: UUID,
    status: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Bug).where(Bug.id == bug_id))
    bug = result.scalar_one_or_none()
    if not bug:
        raise HTTPException(404, "Bug not found")
    valid_statuses = {"open", "in_progress", "fixed", "wont_fix", "duplicate", "verified"}
    if status not in valid_statuses:
        raise HTTPException(400, f"Invalid status. Must be one of: {valid_statuses}")
    bug.status = status
    await db.flush()
    return {"status": status, "id": str(bug_id)}
