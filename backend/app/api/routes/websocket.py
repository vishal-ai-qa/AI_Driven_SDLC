"""
WebSocket route — streams real-time agent status and execution progress to the dashboard.
"""
import asyncio
import json
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, AsyncSessionLocal
from app.models.database import AgentLog, TestRun

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, ws: WebSocket, room: str):
        await ws.accept()
        self._connections.setdefault(room, []).append(ws)

    def disconnect(self, ws: WebSocket, room: str):
        if room in self._connections:
            try:
                self._connections[room].remove(ws)
            except ValueError:
                pass

    async def broadcast(self, room: str, data: dict):
        payload = json.dumps(data)
        dead = []
        for ws in self._connections.get(room, []):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, room)


manager = ConnectionManager()


@router.websocket("/project/{project_id}")
async def project_ws(websocket: WebSocket, project_id: str):
    """Subscribe to all agent events for a project."""
    await manager.connect(websocket, f"project:{project_id}")
    last_seen_id: str | None = None
    try:
        while True:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(AgentLog)
                    .where(AgentLog.project_id == UUID(project_id))
                    .order_by(AgentLog.created_at.desc())
                    .limit(10)
                )
                logs = result.scalars().all()
                # Send only logs newer than the last one we already sent
                new_logs = [l for l in logs if str(l.id) != last_seen_id]
                if logs:
                    last_seen_id = str(logs[0].id)
                for log in reversed(new_logs):
                    await websocket.send_text(json.dumps({
                        "event": "agent_log",
                        "agent": log.agent_name,
                        "phase": log.phase,
                        "status": log.status,
                        "summary": log.output_summary,
                        "tokens": log.tokens_used,
                        "timestamp": log.created_at.isoformat(),
                    }))
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        manager.disconnect(websocket, f"project:{project_id}")


@router.websocket("/run/{run_id}")
async def run_ws(websocket: WebSocket, run_id: str):
    """Subscribe to live test execution progress for a specific run."""
    await manager.connect(websocket, f"run:{run_id}")
    try:
        last_seen_passed = -1
        while True:
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(TestRun).where(TestRun.id == UUID(run_id))
                )
                run = result.scalar_one_or_none()
                if run:
                    payload = {
                        "event": "run_progress",
                        "run_id": run_id,
                        "status": run.status,
                        "total": run.total_cases,
                        "passed": run.passed,
                        "failed": run.failed,
                        "blocked": run.blocked,
                        "skipped": run.skipped,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                    if run.passed != last_seen_passed:
                        await websocket.send_text(json.dumps(payload))
                        last_seen_passed = run.passed
                    if run.status in ("completed", "failed", "error"):
                        await websocket.send_text(json.dumps({**payload, "event": "run_complete"}))
                        break
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        manager.disconnect(websocket, f"run:{run_id}")
