"""
Test Run routes — create runs, trigger AI execution, stream progress.
"""
import base64
import hashlib
import uuid
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from cryptography.fernet import Fernet
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, AsyncSessionLocal
from app.models.database import TestRun, TestCase, TestExecution, Bug, AgentLog, User, Epic, UserStory
from app.models.schemas import TestRunCreate, TestRunResponse, TestExecutionResponse
from app.agents.execution_agent import ExecutionAgent
from app.agents.bug_analysis_agent import BugAnalysisAgent
from app.api.routes.auth import get_current_user
from app.config import settings

router = APIRouter()

# Derive a stable 32-byte key from SECRET_KEY so encrypted values survive restarts.
_fernet_key = base64.urlsafe_b64encode(
    hashlib.sha256(settings.SECRET_KEY.encode()).digest()
)
_fernet = Fernet(_fernet_key)


def _encrypt(value: str) -> str:
    return _fernet.encrypt(value.encode()).decode()


def _decrypt(value: str) -> str:
    return _fernet.decrypt(value.encode()).decode()


async def _next_run_id(db: AsyncSession) -> str:
    result = await db.execute(select(func.count()).select_from(TestRun))
    count = result.scalar() or 0
    return f"RUN-{(count + 1):03d}"


@router.post("", response_model=TestRunResponse, status_code=201)
async def create_test_run(
    data: TestRunCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    run_id = await _next_run_id(db)

    # Gather test cases
    if data.test_case_ids:
        result = await db.execute(
            select(TestCase).where(TestCase.id.in_(data.test_case_ids))
        )
    else:
        result = await db.execute(
            select(TestCase)
            .join(UserStory, TestCase.story_id == UserStory.id, isouter=True)
            .join(Epic, UserStory.epic_id == Epic.id, isouter=True)
            .where(Epic.project_id == data.project_id, TestCase.status == "approved")
        )
    test_cases = result.scalars().all()
    if not test_cases:
        raise HTTPException(400, "No approved test cases found for this project.")

    run = TestRun(
        project_id=data.project_id,
        run_id=run_id,
        name=data.name,
        environment=data.environment,
        app_url=data.app_url,
        app_username=data.app_username,
        app_password_encrypted=_encrypt(data.app_password) if data.app_password else None,
        total_cases=len(test_cases),
        status="pending",
    )
    db.add(run)
    await db.flush()

    # Pre-create execution records
    for tc in test_cases:
        execution = TestExecution(run_id=run.id, test_case_id=tc.id, status="pending")
        db.add(execution)

    await db.flush()
    run_db_id = run.id
    await db.refresh(run)

    # Capture only serializable primitives before the request session closes
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
        }
        for tc in test_cases
    ]
    run_id_str = str(run_db_id)
    app_url = data.app_url
    app_username = data.app_username
    app_password = data.app_password
    environment = data.environment
    project_id = data.project_id

    async def execute_run():
        async with AsyncSessionLocal() as bg_db:
            try:
                agent = ExecutionAgent(run_id=run_id_str)
                bug_agent = BugAnalysisAgent()
                credentials = None
                if app_username:
                    credentials = {"username": app_username, "password": app_password or ""}

                run_obj = await bg_db.get(TestRun, run_db_id)
                if run_obj:
                    run_obj.status = "running"
                    await bg_db.commit()

                passed = failed = blocked = skipped = 0

                for tc_snap in tc_snapshots:
                    tc_uuid = UUID(tc_snap["id"])
                    result_data = await agent.run(
                        test_case={
                            "tc_id": tc_snap["tc_id"],
                            "title": tc_snap["title"],
                            "test_type": tc_snap["test_type"],
                            "preconditions": tc_snap["preconditions"],
                            "test_steps": tc_snap["test_steps"],
                            "test_data": tc_snap["test_data"],
                            "expected_result": tc_snap["expected_result"],
                        },
                        app_url=app_url,
                        credentials=credentials,
                    )

                    exec_result = await bg_db.execute(
                        select(TestExecution).where(
                            TestExecution.run_id == run_db_id,
                            TestExecution.test_case_id == tc_uuid,
                        )
                    )
                    exec_obj = exec_result.scalar_one_or_none()
                    if exec_obj:
                        exec_obj.status = result_data.get("status", "failed")
                        exec_obj.actual_result = result_data.get("actual_result")
                        exec_obj.execution_log = result_data.get("execution_log")
                        exec_obj.console_errors = result_data.get("console_errors", [])
                        exec_obj.network_errors = result_data.get("network_errors", [])
                        exec_obj.screenshots = result_data.get("screenshots", [])
                        exec_obj.duration_ms = result_data.get("duration_ms")

                    status_val = result_data.get("status", "failed")
                    if status_val == "passed":
                        passed += 1
                    elif status_val == "failed":
                        failed += 1
                        bug_data = await bug_agent.run(
                            execution_result=result_data,
                            test_case={
                                "tc_id": tc_snap["tc_id"],
                                "title": tc_snap["title"],
                                "expected_result": tc_snap["expected_result"],
                            },
                            environment=environment,
                        )
                        bug_count_result = await bg_db.execute(select(func.count()).select_from(Bug))
                        bug_count = bug_count_result.scalar() or 0
                        bug = Bug(
                            run_id=run_db_id,
                            execution_id=exec_obj.id if exec_obj else None,
                            bug_id=f"BUG-{(bug_count + 1):03d}",
                            title=bug_data.get("title", f"Failure in {tc_snap['tc_id']}"),
                            description=bug_data.get("description", ""),
                            environment=environment,
                            steps_to_reproduce=tc_snap["test_steps"][:5],
                            expected_result=tc_snap["expected_result"],
                            actual_result=result_data.get("actual_result", ""),
                            severity=bug_data.get("severity", "medium"),
                            priority=bug_data.get("priority", "medium"),
                            root_cause=bug_data.get("root_cause"),
                            suggested_fix=bug_data.get("suggested_fix"),
                            screenshots=result_data.get("screenshots", []),
                            console_logs=result_data.get("console_errors", []),
                            network_logs=result_data.get("network_errors", []),
                            is_flaky=bug_data.get("is_flaky", False),
                            is_environment_issue=bug_data.get("is_environment_issue", False),
                        )
                        bg_db.add(bug)
                    elif status_val == "blocked":
                        blocked += 1
                    else:
                        skipped += 1

                    await bg_db.commit()

                run_final = await bg_db.get(TestRun, run_db_id)
                if run_final:
                    run_final.status = "completed" if failed == 0 else "failed"
                    run_final.passed = passed
                    run_final.failed = failed
                    run_final.blocked = blocked
                    run_final.skipped = skipped
                    await bg_db.commit()

            except Exception as exc:
                await bg_db.rollback()
                log = AgentLog(
                    project_id=project_id,
                    agent_name="execution_agent",
                    phase="phase_5_execution",
                    status="error",
                    error=str(exc),
                )
                bg_db.add(log)
                await bg_db.commit()
                raise

    background_tasks.add_task(execute_run)
    return run


@router.get("", response_model=List[TestRunResponse])
async def list_runs(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(TestRun).where(TestRun.project_id == project_id).order_by(TestRun.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{run_id}", response_model=TestRunResponse)
async def get_run(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(TestRun).where(TestRun.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(404, "Test run not found")
    return run


@router.get("/{run_id}/executions", response_model=List[TestExecutionResponse])
async def get_run_executions(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(TestExecution).where(TestExecution.run_id == run_id)
    )
    return result.scalars().all()
