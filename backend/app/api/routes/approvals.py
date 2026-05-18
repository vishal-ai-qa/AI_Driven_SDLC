from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.database import Approval, User
from app.models.schemas import ApprovalCreate, ApprovalResponse
from app.api.routes.auth import get_current_user

router = APIRouter()

VALID_ENTITY_TYPES = {"requirement", "story", "test_case", "bug", "test_run"}


@router.post("", response_model=ApprovalResponse, status_code=201)
async def create_approval(
    data: ApprovalCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if data.entity_type not in VALID_ENTITY_TYPES:
        raise HTTPException(400, f"Invalid entity_type. Must be one of: {VALID_ENTITY_TYPES}")

    # Check for existing approval from this user for this entity
    existing = await db.execute(
        select(Approval).where(
            Approval.entity_type == data.entity_type,
            Approval.entity_id == data.entity_id,
            Approval.user_id == user.id,
        )
    )
    approval = existing.scalar_one_or_none()

    if approval:
        approval.status = data.status
        approval.comments = data.comments
    else:
        approval = Approval(
            entity_type=data.entity_type,
            entity_id=data.entity_id,
            user_id=user.id,
            status=data.status,
            comments=data.comments,
        )
        db.add(approval)

    await db.flush()
    await db.refresh(approval)
    return approval


@router.get("", response_model=List[ApprovalResponse])
async def list_approvals(
    entity_type: Optional[str] = None,
    entity_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(Approval)
    if entity_type:
        query = query.where(Approval.entity_type == entity_type)
    if entity_id:
        query = query.where(Approval.entity_id == entity_id)
    result = await db.execute(query.order_by(Approval.created_at.desc()))
    return result.scalars().all()
