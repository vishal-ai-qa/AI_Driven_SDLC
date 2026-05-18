"""
LangGraph Orchestrator — coordinates all phases of the SDLC pipeline.
Each phase is a node in the graph. Edges enforce the correct flow and human checkpoints.
"""
from __future__ import annotations
import asyncio
from typing import Any, TypedDict, Optional, List

import structlog
from langgraph.graph import StateGraph, END

from app.agents.requirement_agent import RequirementAgent
from app.agents.story_agent import StoryAgent
from app.agents.test_case_agent import TestCaseAgent
from app.agents.execution_agent import ExecutionAgent
from app.agents.bug_analysis_agent import BugAnalysisAgent
from app.agents.automation_agent import AutomationAgent

logger = structlog.get_logger()


# ─── Pipeline State ───────────────────────────────────────────────────────────

class PipelineState(TypedDict, total=False):
    project_id: str
    phase: str
    error: Optional[str]

    # Phase 1
    raw_content: str
    source_type: str
    additional_context: Optional[str]
    requirement_result: Optional[dict]

    # Phase 2
    story_result: Optional[dict]

    # Phase 3
    test_case_result: Optional[dict]

    # Human checkpoint flags
    requirements_approved: bool
    stories_approved: bool
    test_cases_approved: bool

    # Phase 4
    app_url: Optional[str]
    credentials: Optional[dict]
    environment: str
    run_id: Optional[str]

    # Phase 5
    test_cases_to_run: List[dict]
    execution_results: List[dict]

    # Phase 6
    bug_reports: List[dict]

    # Human approval
    test_run_signed_off: bool

    # Phase 8
    automation_results: List[dict]

    # Streaming
    event_queue: Optional[Any]


# ─── Nodes ────────────────────────────────────────────────────────────────────

async def phase1_ingest(state: PipelineState) -> PipelineState:
    logger.info("pipeline_phase", phase="1_ingest", project=state["project_id"])
    agent = RequirementAgent()
    result = await agent.run(
        project_id=state["project_id"],
        content=state["raw_content"],
        source_type=state.get("source_type", "brd"),
        additional_context=state.get("additional_context"),
    )
    return {**state, "phase": "requirements_generated", "requirement_result": result}


async def phase2_stories(state: PipelineState) -> PipelineState:
    logger.info("pipeline_phase", phase="2_stories", project=state["project_id"])
    req_result = state["requirement_result"]
    all_reqs = (
        req_result.get("functional_requirements", []) +
        req_result.get("non_functional_requirements", [])
    )
    agent = StoryAgent()
    result = await agent.run(project_id=state["project_id"], requirements=all_reqs)
    return {**state, "phase": "stories_generated", "story_result": result}


async def phase3_test_cases(state: PipelineState) -> PipelineState:
    logger.info("pipeline_phase", phase="3_test_cases", project=state["project_id"])
    all_stories = []
    for epic in state["story_result"].get("epics", []):
        all_stories.extend(epic.get("stories", []))
    agent = TestCaseAgent()
    result = await agent.run(project_id=state["project_id"], stories=all_stories)
    return {**state, "phase": "test_cases_generated", "test_case_result": result}


async def phase5_execution(state: PipelineState) -> PipelineState:
    logger.info("pipeline_phase", phase="5_execution", project=state["project_id"])
    run_id = state.get("run_id", "default_run")
    agent = ExecutionAgent(run_id=run_id)
    results = []
    for tc in state.get("test_cases_to_run", []):
        result = await agent.run(
            test_case=tc,
            app_url=state.get("app_url", ""),
            credentials=state.get("credentials"),
        )
        results.append(result)
    return {**state, "phase": "execution_complete", "execution_results": results}


async def phase6_bug_analysis(state: PipelineState) -> PipelineState:
    logger.info("pipeline_phase", phase="6_bug_analysis", project=state["project_id"])
    bug_agent = BugAnalysisAgent()
    bug_reports = []
    tc_map = {tc["tc_id"]: tc for tc in state.get("test_cases_to_run", [])}

    for execution in state.get("execution_results", []):
        if execution.get("status") == "failed":
            tc = tc_map.get(execution.get("tc_id"), {})
            bug = await bug_agent.run(
                execution_result=execution,
                test_case=tc,
                environment=state.get("environment", "unknown"),
            )
            bug_reports.append(bug)

    return {**state, "phase": "bugs_analyzed", "bug_reports": bug_reports}


async def phase8_automation(state: PipelineState) -> PipelineState:
    logger.info("pipeline_phase", phase="8_automation", project=state["project_id"])
    agent = AutomationAgent()
    results = []
    for tc in state.get("test_cases_to_run", []):
        script = await agent.run(
            test_case=tc,
            project_name=state["project_id"],
            base_url=state.get("app_url", ""),
        )
        results.append(script)
    return {**state, "phase": "automation_generated", "automation_results": results}


# ─── Human checkpoint nodes (pause and wait for external approval) ─────────────

def check_requirements_approved(state: PipelineState) -> str:
    return "approved" if state.get("requirements_approved") else "pending_approval"


def check_stories_approved(state: PipelineState) -> str:
    return "approved" if state.get("stories_approved") else "pending_approval"


def check_test_cases_approved(state: PipelineState) -> str:
    return "approved" if state.get("test_cases_approved") else "pending_approval"


def check_run_signed_off(state: PipelineState) -> str:
    return "signed_off" if state.get("test_run_signed_off") else "pending_signoff"


# ─── Graph Assembly ───────────────────────────────────────────────────────────

def build_pipeline() -> StateGraph:
    graph = StateGraph(PipelineState)

    graph.add_node("phase1_ingest", phase1_ingest)
    graph.add_node("phase2_stories", phase2_stories)
    graph.add_node("phase3_test_cases", phase3_test_cases)
    graph.add_node("phase5_execution", phase5_execution)
    graph.add_node("phase6_bug_analysis", phase6_bug_analysis)
    graph.add_node("phase8_automation", phase8_automation)

    # Human checkpoints use conditional edges
    graph.add_node("await_req_approval", lambda s: s)
    graph.add_node("await_story_approval", lambda s: s)
    graph.add_node("await_tc_approval", lambda s: s)
    graph.add_node("await_signoff", lambda s: s)

    graph.set_entry_point("phase1_ingest")
    graph.add_edge("phase1_ingest", "await_req_approval")
    graph.add_conditional_edges(
        "await_req_approval",
        check_requirements_approved,
        {"approved": "phase2_stories", "pending_approval": END},
    )
    graph.add_edge("phase2_stories", "await_story_approval")
    graph.add_conditional_edges(
        "await_story_approval",
        check_stories_approved,
        {"approved": "phase3_test_cases", "pending_approval": END},
    )
    graph.add_edge("phase3_test_cases", "await_tc_approval")
    graph.add_conditional_edges(
        "await_tc_approval",
        check_test_cases_approved,
        {"approved": "phase5_execution", "pending_approval": END},
    )
    graph.add_edge("phase5_execution", "phase6_bug_analysis")
    graph.add_edge("phase6_bug_analysis", "await_signoff")
    graph.add_conditional_edges(
        "await_signoff",
        check_run_signed_off,
        {"signed_off": "phase8_automation", "pending_signoff": END},
    )
    graph.add_edge("phase8_automation", END)

    return graph.compile()


# Global compiled pipeline
pipeline = build_pipeline()
