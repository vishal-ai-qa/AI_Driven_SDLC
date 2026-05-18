from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.database import Requirement, UserStory, TestCase, TestExecution, Bug, Epic, User
from app.models.schemas import TraceabilityMatrix, TraceabilityNode
from app.api.routes.auth import get_current_user

router = APIRouter()


@router.get("/{project_id}", response_model=TraceabilityMatrix)
async def get_traceability_matrix(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
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

    tcs_result = await db.execute(
        select(TestCase)
        .join(UserStory, TestCase.story_id == UserStory.id, isouter=True)
        .join(Epic, UserStory.epic_id == Epic.id, isouter=True)
        .where(Epic.project_id == project_id)
    )
    test_cases = tcs_result.scalars().all()

    # Build story → test case map
    story_tc_map: dict[UUID, list] = {}
    for tc in test_cases:
        if tc.story_id:
            story_tc_map.setdefault(tc.story_id, []).append(tc)

    # Build requirement → story map
    req_story_map: dict[UUID, list] = {}
    for story in stories:
        if story.requirement_id:
            req_story_map.setdefault(story.requirement_id, []).append(story)

    nodes: list[TraceabilityNode] = []
    covered_reqs = 0

    for req in requirements:
        req_stories = req_story_map.get(req.id, [])
        story_nodes = []
        for story in req_stories:
            tcs = story_tc_map.get(story.id, [])
            tc_nodes = [
                TraceabilityNode(
                    id=tc.tc_id,
                    type="test_case",
                    title=tc.title,
                    status=tc.status,
                    children=[],
                )
                for tc in tcs
            ]
            story_nodes.append(
                TraceabilityNode(
                    id=story.story_id,
                    type="story",
                    title=story.title,
                    status=story.status,
                    children=tc_nodes,
                )
            )
        if req_stories:
            covered_reqs += 1
        nodes.append(
            TraceabilityNode(
                id=req.req_id,
                type="requirement",
                title=req.title,
                status=req.status,
                children=story_nodes,
            )
        )

    coverage = (covered_reqs / len(requirements) * 100) if requirements else 0.0
    uncovered = [r.req_id for r in requirements if r.id not in req_story_map]

    return TraceabilityMatrix(
        project_id=project_id,
        generated_at=datetime.utcnow(),
        coverage_percentage=round(coverage, 1),
        nodes=nodes,
        uncovered_requirements=uncovered,
    )
