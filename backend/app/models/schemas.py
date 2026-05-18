"""
Pydantic schemas for request/response validation.
Every schema includes confidence and traceability metadata.
"""
from datetime import datetime
from typing import Optional, List, Any, Dict
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator
import enum


# ─── Shared Base ──────────────────────────────────────────────────────────────

class TimestampMixin(BaseModel):
    created_at: datetime
    updated_at: Optional[datetime] = None


class TracedOutput(BaseModel):
    """Every AI-generated output must carry traceability metadata."""
    confidence_score: float = Field(ge=0.0, le=1.0, default=1.0)
    source_ref: Optional[str] = None
    needs_clarification: bool = False
    clarification_notes: Optional[List[str]] = None


# ─── Auth ─────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8)
    full_name: str
    role: str = "qa_engineer"


class UserResponse(TimestampMixin):
    id: UUID
    email: str
    username: str
    full_name: str
    role: str
    is_active: bool
    avatar_url: Optional[str] = None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ─── Project ──────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    app_url: Optional[str] = None
    api_base_url: Optional[str] = None


class ProjectResponse(TimestampMixin):
    id: UUID
    name: str
    slug: str
    description: Optional[str] = None
    status: str
    app_url: Optional[str] = None
    api_base_url: Optional[str] = None

    model_config = {"from_attributes": True}


# ─── Requirements ─────────────────────────────────────────────────────────────

class RequirementIngest(BaseModel):
    """Raw intake — user provides unstructured text/BRD/etc."""
    content: str = Field(min_length=10)
    source_type: str = "brd"  # brd | epic | feature | api_spec | acceptance_criteria
    additional_context: Optional[str] = None


class RequirementCreate(BaseModel):
    project_id: UUID
    req_id: Optional[str] = None
    title: str
    description: str
    req_type: str = "functional"
    priority: str = "medium"
    source: Optional[str] = None
    original_text: Optional[str] = None
    assumptions: List[str] = []
    risks: List[str] = []
    dependencies: List[str] = []
    ambiguities: List[str] = []
    confidence_score: float = 1.0


class RequirementResponse(TimestampMixin, TracedOutput):
    id: UUID
    project_id: UUID
    req_id: str
    title: str
    description: str
    req_type: str
    status: str
    priority: str
    source: Optional[str] = None
    assumptions: List[str] = []
    risks: List[str] = []
    dependencies: List[str] = []
    ambiguities: List[str] = []

    model_config = {"from_attributes": True}


class RequirementUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    req_type: Optional[str] = None
    assumptions: Optional[List[str]] = None
    risks: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None
    ambiguities: Optional[List[str]] = None
    clarification_answer: Optional[str] = None  # human answer to resolve NEEDS_CLARIFICATION


class RequirementIngestResponse(BaseModel):
    """AI analysis result from raw requirement text."""
    project_id: UUID
    functional_requirements: List[RequirementCreate]
    non_functional_requirements: List[RequirementCreate]
    risks: List[str]
    dependencies: List[str]
    assumptions: List[str]
    edge_cases: List[str]
    clarification_questions: List[str]
    overall_confidence: float


# ─── User Stories ─────────────────────────────────────────────────────────────

class AcceptanceCriterion(BaseModel):
    id: str
    description: str
    type: str = "functional"  # functional | non-functional | UI | security


class UserStoryUpdate(BaseModel):
    title: Optional[str] = None
    role: Optional[str] = None
    goal: Optional[str] = None
    business_value: Optional[str] = None
    acceptance_criteria: Optional[List[Any]] = None
    positive_scenarios: Optional[List[str]] = None
    negative_scenarios: Optional[List[str]] = None
    priority: Optional[str] = None
    risk_level: Optional[str] = None
    story_points: Optional[int] = None


class UserStoryCreate(BaseModel):
    requirement_id: Optional[UUID] = None
    epic_id: Optional[UUID] = None
    story_id: Optional[str] = None
    title: str
    role: str
    goal: str
    business_value: str
    acceptance_criteria: List[AcceptanceCriterion] = []
    positive_scenarios: List[str] = []
    negative_scenarios: List[str] = []
    ui_validations: List[str] = []
    api_validations: List[str] = []
    security_validations: List[str] = []
    boundary_conditions: List[str] = []
    priority: str = "medium"
    risk_level: str = "medium"
    story_points: Optional[int] = None


class UserStoryResponse(TimestampMixin, TracedOutput):
    id: UUID
    story_id: str
    title: str
    role: str
    goal: str
    business_value: str
    acceptance_criteria: List[AcceptanceCriterion]
    positive_scenarios: List[str]
    negative_scenarios: List[str]
    ui_validations: List[str]
    api_validations: List[str]
    security_validations: List[str]
    boundary_conditions: List[str]
    status: str
    priority: str
    risk_level: str
    story_points: Optional[int] = None
    requirement_id: Optional[UUID] = None

    model_config = {"from_attributes": True}


# ─── Test Cases ───────────────────────────────────────────────────────────────

class TestStep(BaseModel):
    step_number: int
    action: str
    test_data: Optional[str] = None
    expected_result: str


class TestCaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    preconditions: Optional[List[str]] = None
    test_steps: Optional[List[Any]] = None
    expected_result: Optional[str] = None
    priority: Optional[str] = None
    severity: Optional[str] = None
    tags: Optional[List[str]] = None
    automation_feasibility: Optional[str] = None


class TestCaseCreate(BaseModel):
    story_id: Optional[UUID] = None
    tc_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    test_type: str = "functional"
    preconditions: List[str] = []
    test_steps: List[TestStep] = []
    test_data: Dict[str, Any] = {}
    expected_result: str
    priority: str = "medium"
    severity: str = "medium"
    automation_feasibility: str = "automatable"
    tags: List[str] = []
    requirement_ref: Optional[str] = None
    story_ref: Optional[str] = None
    acceptance_criteria_ref: Optional[str] = None


class TestCaseResponse(TimestampMixin, TracedOutput):
    id: UUID
    story_id: Optional[UUID] = None
    tc_id: str
    title: str
    description: Optional[str] = None
    test_type: str
    preconditions: List[str]
    test_steps: List[TestStep]
    test_data: Dict[str, Any]
    expected_result: str
    status: str
    priority: str
    severity: str
    automation_feasibility: str
    tags: List[str]
    requirement_ref: Optional[str] = None
    story_ref: Optional[str] = None
    acceptance_criteria_ref: Optional[str] = None

    model_config = {"from_attributes": True}


# ─── Test Runs ────────────────────────────────────────────────────────────────

class TestRunCreate(BaseModel):
    project_id: UUID
    name: str
    environment: str = "staging"
    app_url: str
    app_username: Optional[str] = None
    app_password: Optional[str] = None
    test_case_ids: Optional[List[UUID]] = None  # None = all approved cases


class TestRunResponse(TimestampMixin):
    id: UUID
    project_id: UUID
    run_id: str
    name: str
    environment: str
    app_url: Optional[str] = None
    status: str
    total_cases: int
    passed: int
    failed: int
    blocked: int
    skipped: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    report_path: Optional[str] = None

    model_config = {"from_attributes": True}


# ─── Test Execution ───────────────────────────────────────────────────────────

class TestExecutionResponse(BaseModel):
    id: UUID
    run_id: UUID
    test_case_id: UUID
    status: str
    actual_result: Optional[str] = None
    execution_log: Optional[str] = None
    console_errors: List[dict] = []
    network_errors: List[dict] = []
    screenshots: List[str] = []
    video_path: Optional[str] = None
    duration_ms: Optional[int] = None
    agent_reasoning: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── Bugs ─────────────────────────────────────────────────────────────────────

class BugCreate(BaseModel):
    run_id: Optional[UUID] = None
    execution_id: Optional[UUID] = None
    title: str
    description: str
    environment: Optional[str] = None
    steps_to_reproduce: List[str] = []
    expected_result: str
    actual_result: str
    severity: str = "medium"
    priority: str = "medium"
    root_cause: Optional[str] = None
    suggested_fix: Optional[str] = None
    tags: List[str] = []
    is_flaky: bool = False
    is_environment_issue: bool = False


class BugResponse(TimestampMixin):
    id: UUID
    bug_id: str
    title: str
    description: str
    environment: Optional[str] = None
    steps_to_reproduce: List[str]
    expected_result: str
    actual_result: str
    severity: str
    priority: str
    status: str
    root_cause: Optional[str] = None
    suggested_fix: Optional[str] = None
    screenshots: List[str] = []
    tags: List[str] = []
    is_flaky: bool
    is_environment_issue: bool

    model_config = {"from_attributes": True}


# ─── Automation ───────────────────────────────────────────────────────────────

class AutomationScriptResponse(BaseModel):
    id: UUID
    test_case_id: UUID
    script_id: str
    file_path: str
    content: str
    language: str
    framework: str
    version: int
    generation_notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Approval ─────────────────────────────────────────────────────────────────

class ApprovalCreate(BaseModel):
    entity_type: str
    entity_id: UUID
    status: str
    comments: Optional[str] = None


class ApprovalResponse(TimestampMixin):
    id: UUID
    entity_type: str
    entity_id: UUID
    user_id: UUID
    status: str
    comments: Optional[str] = None

    model_config = {"from_attributes": True}


# ─── Traceability ─────────────────────────────────────────────────────────────

class TraceabilityNode(BaseModel):
    id: str
    type: str  # requirement | story | test_case | execution | bug
    title: str
    status: str
    children: List["TraceabilityNode"] = []


class TraceabilityMatrix(BaseModel):
    project_id: UUID
    generated_at: datetime
    coverage_percentage: float
    nodes: List[TraceabilityNode]
    uncovered_requirements: List[str] = []
    uncovered_stories: List[str] = []


# ─── AI Agent Status ──────────────────────────────────────────────────────────

class AgentStatus(BaseModel):
    agent_name: str
    phase: str
    status: str  # idle | running | completed | error
    current_task: Optional[str] = None
    progress: float = 0.0
    message: Optional[str] = None
    reasoning_trace: Optional[str] = None
    tokens_used: int = 0


class StreamEvent(BaseModel):
    event_type: str  # agent_update | progress | result | error
    agent: Optional[str] = None
    data: Any
    timestamp: datetime = Field(default_factory=datetime.utcnow)
