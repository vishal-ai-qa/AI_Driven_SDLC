"""
Requirements routes — ingestion (AI parse), CRUD, file upload, bulk approve.
"""
import os
import uuid
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, BackgroundTasks
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, AsyncSessionLocal
from app.models.database import Requirement, Attachment, AgentLog, User
from app.models.schemas import RequirementCreate, RequirementResponse, RequirementIngest, RequirementUpdate
from app.agents.requirement_agent import RequirementAgent
from app.api.routes.auth import get_current_user
from app.config import settings

router = APIRouter()


async def _next_req_id(db: AsyncSession, project_id: UUID) -> str:
    result = await db.execute(
        select(func.count()).where(Requirement.project_id == project_id)
    )
    count = result.scalar() or 0
    return f"REQ-{(count + 1):03d}"


@router.post("/ingest", status_code=202)
async def ingest_requirements(
    data: RequirementIngest,
    project_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Async AI ingestion — parses raw text and creates structured requirements.
    Returns immediately with a job_id; poll /requirements?project_id=X for results.
    """
    job_id = str(uuid.uuid4())
    # Capture only primitives — never pass the request-scoped session into a background task
    project_id_str = str(project_id)
    content_snapshot = data.content
    source_type = data.source_type
    additional_context = data.additional_context

    async def run_agent():
        async with AsyncSessionLocal() as bg_db:
            try:
                agent = RequirementAgent()
                result = await agent.run(
                    project_id=project_id_str,
                    content=content_snapshot,
                    source_type=source_type,
                    additional_context=additional_context,
                )

                # Persist functional requirements
                for req_data in result.get("functional_requirements", []):
                    req_id = req_data.get("req_id") or await _next_req_id(bg_db, project_id)
                    req = Requirement(
                        project_id=project_id,
                        req_id=req_id,
                        title=req_data.get("title", ""),
                        description=req_data.get("description", ""),
                        req_type="functional",
                        priority=req_data.get("priority", "medium"),
                        source=source_type,
                        original_text=content_snapshot[:2000],
                        assumptions=req_data.get("assumptions", []),
                        risks=req_data.get("risks", []),
                        dependencies=req_data.get("dependencies", []),
                        ambiguities=req_data.get("ambiguities", []),
                        confidence_score=float(req_data.get("confidence_score", 1.0)),
                    )
                    bg_db.add(req)

                for req_data in result.get("non_functional_requirements", []):
                    req_id = req_data.get("req_id") or await _next_req_id(bg_db, project_id)
                    req = Requirement(
                        project_id=project_id,
                        req_id=req_id,
                        title=req_data.get("title", ""),
                        description=req_data.get("description", ""),
                        req_type="non-functional",
                        priority=req_data.get("priority", "medium"),
                        source=source_type,
                        original_text=content_snapshot[:2000],
                        confidence_score=float(req_data.get("confidence_score", 1.0)),
                    )
                    bg_db.add(req)

                func_count = len(result.get("functional_requirements", []))
                nfunc_count = len(result.get("non_functional_requirements", []))
                log = AgentLog(
                    project_id=project_id,
                    agent_name="requirement_agent",
                    phase="phase_1_ingestion",
                    status="completed",
                    input_summary=f"{source_type}: {len(content_snapshot)} chars",
                    output_summary=f"{func_count} functional, {nfunc_count} non-functional",
                    tokens_used=result.get("_meta", {}).get("tokens_used", 0),
                )
                bg_db.add(log)
                await bg_db.commit()
            except Exception as exc:
                await bg_db.rollback()
                log = AgentLog(
                    project_id=project_id,
                    agent_name="requirement_agent",
                    phase="phase_1_ingestion",
                    status="error",
                    error=str(exc),
                )
                bg_db.add(log)
                await bg_db.commit()
                raise

    background_tasks.add_task(run_agent)
    return {
        "job_id": job_id,
        "status": "processing",
        "message": "Requirement ingestion started — poll /requirements?project_id=X for results",
    }


@router.post("", response_model=RequirementResponse, status_code=201)
async def create_requirement(
    data: RequirementCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    req_id = data.req_id or await _next_req_id(db, data.project_id)
    req = Requirement(
        project_id=data.project_id,
        req_id=req_id,
        title=data.title,
        description=data.description,
        req_type=data.req_type,
        priority=data.priority,
        source=data.source,
        original_text=data.original_text,
        assumptions=data.assumptions,
        risks=data.risks,
        dependencies=data.dependencies,
        ambiguities=data.ambiguities,
        confidence_score=data.confidence_score,
    )
    db.add(req)
    await db.flush()
    await db.refresh(req)
    return req


@router.get("", response_model=List[RequirementResponse])
async def list_requirements(
    project_id: UUID,
    req_type: Optional[str] = None,
    status: Optional[str] = None,
    needs_clarification: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(Requirement).where(Requirement.project_id == project_id)
    if req_type:
        query = query.where(Requirement.req_type == req_type)
    if status:
        query = query.where(Requirement.status == status)
    if needs_clarification is True:
        # Requirements with low confidence or ambiguities
        query = query.where(Requirement.confidence_score < 0.7)
    result = await db.execute(query.order_by(Requirement.req_id))
    return result.scalars().all()


@router.get("/{req_id_or_uuid}", response_model=RequirementResponse)
async def get_requirement(
    req_id_or_uuid: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        uid = UUID(req_id_or_uuid)
        result = await db.execute(select(Requirement).where(Requirement.id == uid))
    except ValueError:
        result = await db.execute(select(Requirement).where(Requirement.req_id == req_id_or_uuid))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(404, "Requirement not found")
    return req


@router.patch("/approve-all")
async def approve_all_requirements(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Bulk-approve all draft requirements for a project (confidence ≥ 0.7)."""
    result = await db.execute(
        select(Requirement).where(
            Requirement.project_id == project_id,
            Requirement.status.in_(["draft", "needs_clarification"]),
            Requirement.confidence_score >= 0.7,
        )
    )
    reqs = result.scalars().all()
    for r in reqs:
        r.status = "approved"
    await db.flush()
    return {"approved_count": len(reqs), "project_id": str(project_id)}


@router.patch("/{requirement_id}/approve")
async def approve_requirement(
    requirement_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Requirement).where(Requirement.id == requirement_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(404, "Requirement not found")
    req.status = "approved"
    await db.flush()
    return {"status": "approved", "id": str(requirement_id)}


@router.patch("/{requirement_id}", response_model=RequirementResponse)
async def update_requirement(
    requirement_id: UUID,
    data: RequirementUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Human edits: fix AI mistakes, add clarifications, update priority."""
    result = await db.execute(select(Requirement).where(Requirement.id == requirement_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(404, "Requirement not found")
    for field, value in data.model_dump(exclude_unset=True, exclude={"clarification_answer"}).items():
        setattr(req, field, value)
    if data.clarification_answer:
        req.ambiguities = []
        req.confidence_score = min(req.confidence_score + 0.2, 1.0)
        if req.status == "needs_clarification":
            req.status = "draft"
    await db.flush()
    await db.refresh(req)
    return req


@router.post("/upload")
async def upload_requirement_file(
    project_id: UUID = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Upload BRD/PDF/Word doc — stores file for later AI ingestion."""
    if file.size and file.size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(400, f"File too large (max {settings.MAX_UPLOAD_SIZE_MB}MB)")

    safe_name = Path(file.filename).name if file.filename else "upload.bin"
    upload_dir = Path(settings.UPLOAD_DIR) / str(project_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / safe_name

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    attachment = Attachment(
        requirement_id=None,
        filename=safe_name,
        file_path=str(file_path),
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(content),
    )
    db.add(attachment)
    await db.flush()
    await db.refresh(attachment)

    return {"filename": safe_name, "attachment_id": str(attachment.id), "size": len(content)}
