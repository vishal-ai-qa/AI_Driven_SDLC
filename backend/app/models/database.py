"""
SQLAlchemy ORM models — full SDLC entity graph.
"""
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    String, Text, Boolean, Integer, Float, DateTime, ForeignKey,
    Enum as SAEnum, JSON, Index, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from pgvector.sqlalchemy import Vector
import enum

from app.database import Base


# ─── Enums ────────────────────────────────────────────────────────────────────

class ProjectStatus(str, enum.Enum):
    active = "active"
    archived = "archived"
    completed = "completed"


class RequirementStatus(str, enum.Enum):
    draft = "draft"
    needs_clarification = "needs_clarification"
    approved = "approved"
    rejected = "rejected"


class StoryStatus(str, enum.Enum):
    draft = "draft"
    review = "review"
    approved = "approved"
    rejected = "rejected"


class TestCaseStatus(str, enum.Enum):
    draft = "draft"
    review = "review"
    approved = "approved"
    rejected = "rejected"


class ExecutionStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    passed = "passed"
    failed = "failed"
    blocked = "blocked"
    skipped = "skipped"
    error = "error"


class BugSeverity(str, enum.Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"


class BugStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    fixed = "fixed"
    wont_fix = "wont_fix"
    duplicate = "duplicate"
    verified = "verified"


class Priority(str, enum.Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"


class ApprovalStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    signed_off = "signed_off"


class UserRole(str, enum.Enum):
    admin = "admin"
    product_owner = "product_owner"
    qa_lead = "qa_lead"
    qa_engineer = "qa_engineer"
    developer = "developer"
    viewer = "viewer"


# ─── User / Auth ──────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.qa_engineer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    projects: Mapped[List["ProjectMember"]] = relationship("ProjectMember", back_populates="user")
    approvals: Mapped[List["Approval"]] = relationship("Approval", back_populates="user")


# ─── Project ──────────────────────────────────────────────────────────────────

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[ProjectStatus] = mapped_column(SAEnum(ProjectStatus), default=ProjectStatus.active)
    app_url: Mapped[Optional[str]] = mapped_column(String(500))
    api_base_url: Mapped[Optional[str]] = mapped_column(String(500))
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    members: Mapped[List["ProjectMember"]] = relationship("ProjectMember", back_populates="project")
    requirements: Mapped[List["Requirement"]] = relationship("Requirement", back_populates="project")
    epics: Mapped[List["Epic"]] = relationship("Epic", back_populates="project")
    test_runs: Mapped[List["TestRun"]] = relationship("TestRun", back_populates="project")


class ProjectMember(Base):
    __tablename__ = "project_members"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole))
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["Project"] = relationship("Project", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="projects")

    __table_args__ = (UniqueConstraint("project_id", "user_id"),)


# ─── Requirements ─────────────────────────────────────────────────────────────

class Requirement(Base):
    __tablename__ = "requirements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    req_id: Mapped[str] = mapped_column(String(50), nullable=False)  # REQ-001
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    req_type: Mapped[str] = mapped_column(String(50))  # functional | non-functional | constraint
    status: Mapped[RequirementStatus] = mapped_column(SAEnum(RequirementStatus), default=RequirementStatus.draft)
    priority: Mapped[Priority] = mapped_column(SAEnum(Priority), default=Priority.medium)
    source: Mapped[Optional[str]] = mapped_column(String(255))  # BRD | Epic | Feature | Manual
    original_text: Mapped[Optional[str]] = mapped_column(Text)
    assumptions: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    risks: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    dependencies: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    ambiguities: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0)
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(1536))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project: Mapped["Project"] = relationship("Project", back_populates="requirements")
    stories: Mapped[List["UserStory"]] = relationship("UserStory", back_populates="requirement")
    attachments: Mapped[List["Attachment"]] = relationship("Attachment", back_populates="requirement")

    __table_args__ = (
        UniqueConstraint("project_id", "req_id"),
        Index("ix_requirements_project_id", "project_id"),
    )


# ─── Epics / Stories ──────────────────────────────────────────────────────────

class Epic(Base):
    __tablename__ = "epics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    epic_id: Mapped[str] = mapped_column(String(50), nullable=False)  # EPIC-001
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[StoryStatus] = mapped_column(SAEnum(StoryStatus), default=StoryStatus.draft)
    priority: Mapped[Priority] = mapped_column(SAEnum(Priority), default=Priority.medium)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["Project"] = relationship("Project", back_populates="epics")
    stories: Mapped[List["UserStory"]] = relationship("UserStory", back_populates="epic")

    __table_args__ = (UniqueConstraint("project_id", "epic_id"),)


class UserStory(Base):
    __tablename__ = "user_stories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requirement_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("requirements.id", ondelete="SET NULL"))
    epic_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("epics.id", ondelete="SET NULL"))
    story_id: Mapped[str] = mapped_column(String(50), nullable=False)  # US-001
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    role: Mapped[str] = mapped_column(String(200), nullable=False)  # "As a customer..."
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    business_value: Mapped[str] = mapped_column(Text)
    acceptance_criteria: Mapped[List[dict]] = mapped_column(JSON, default=list)
    positive_scenarios: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    negative_scenarios: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    ui_validations: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    api_validations: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    security_validations: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    boundary_conditions: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    status: Mapped[StoryStatus] = mapped_column(SAEnum(StoryStatus), default=StoryStatus.draft)
    priority: Mapped[Priority] = mapped_column(SAEnum(Priority), default=Priority.medium)
    risk_level: Mapped[str] = mapped_column(String(20), default="medium")
    story_points: Mapped[Optional[int]] = mapped_column(Integer)
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(1536))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    requirement: Mapped[Optional["Requirement"]] = relationship("Requirement", back_populates="stories")
    epic: Mapped[Optional["Epic"]] = relationship("Epic", back_populates="stories")
    test_cases: Mapped[List["TestCase"]] = relationship("TestCase", back_populates="story")


# ─── Test Cases ───────────────────────────────────────────────────────────────

class TestCase(Base):
    __tablename__ = "test_cases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    story_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("user_stories.id", ondelete="SET NULL"))
    tc_id: Mapped[str] = mapped_column(String(50), nullable=False)  # TC-001
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    test_type: Mapped[str] = mapped_column(String(50))  # functional | security | API | UI | accessibility
    preconditions: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    test_steps: Mapped[List[dict]] = mapped_column(JSON, default=list)  # [{step, action, expected}]
    test_data: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    expected_result: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[TestCaseStatus] = mapped_column(SAEnum(TestCaseStatus), default=TestCaseStatus.draft)
    priority: Mapped[Priority] = mapped_column(SAEnum(Priority), default=Priority.medium)
    severity: Mapped[BugSeverity] = mapped_column(SAEnum(BugSeverity), default=BugSeverity.medium)
    automation_feasibility: Mapped[str] = mapped_column(String(20), default="automatable")
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    requirement_ref: Mapped[Optional[str]] = mapped_column(String(100))
    story_ref: Mapped[Optional[str]] = mapped_column(String(100))
    acceptance_criteria_ref: Mapped[Optional[str]] = mapped_column(String(100))
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(1536))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    story: Mapped[Optional["UserStory"]] = relationship("UserStory", back_populates="test_cases")
    executions: Mapped[List["TestExecution"]] = relationship("TestExecution", back_populates="test_case")
    automation_scripts: Mapped[List["AutomationScript"]] = relationship("AutomationScript", back_populates="test_case")


# ─── Test Runs & Execution ────────────────────────────────────────────────────

class TestRun(Base):
    __tablename__ = "test_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    run_id: Mapped[str] = mapped_column(String(50), nullable=False)  # RUN-001
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    environment: Mapped[str] = mapped_column(String(100))  # staging | UAT | production
    app_url: Mapped[Optional[str]] = mapped_column(String(500))
    app_username: Mapped[Optional[str]] = mapped_column(String(255))
    app_password_encrypted: Mapped[Optional[str]] = mapped_column(String(500))
    status: Mapped[ExecutionStatus] = mapped_column(SAEnum(ExecutionStatus), default=ExecutionStatus.pending)
    total_cases: Mapped[int] = mapped_column(Integer, default=0)
    passed: Mapped[int] = mapped_column(Integer, default=0)
    failed: Mapped[int] = mapped_column(Integer, default=0)
    blocked: Mapped[int] = mapped_column(Integer, default=0)
    skipped: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    report_path: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["Project"] = relationship("Project", back_populates="test_runs")
    executions: Mapped[List["TestExecution"]] = relationship("TestExecution", back_populates="run")
    bugs: Mapped[List["Bug"]] = relationship("Bug", back_populates="run")


class TestExecution(Base):
    __tablename__ = "test_executions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("test_runs.id", ondelete="CASCADE"))
    test_case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("test_cases.id"))
    status: Mapped[ExecutionStatus] = mapped_column(SAEnum(ExecutionStatus), default=ExecutionStatus.pending)
    actual_result: Mapped[Optional[str]] = mapped_column(Text)
    execution_log: Mapped[Optional[str]] = mapped_column(Text)
    console_errors: Mapped[Optional[List[dict]]] = mapped_column(JSON, default=list)
    network_errors: Mapped[Optional[List[dict]]] = mapped_column(JSON, default=list)
    screenshots: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    video_path: Mapped[Optional[str]] = mapped_column(String(500))
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    agent_reasoning: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    run: Mapped["TestRun"] = relationship("TestRun", back_populates="executions")
    test_case: Mapped["TestCase"] = relationship("TestCase", back_populates="executions")
    bugs: Mapped[List["Bug"]] = relationship("Bug", back_populates="execution")


# ─── Bugs ─────────────────────────────────────────────────────────────────────

class Bug(Base):
    __tablename__ = "bugs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("test_runs.id", ondelete="SET NULL"))
    execution_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("test_executions.id", ondelete="SET NULL"))
    bug_id: Mapped[str] = mapped_column(String(50), nullable=False)  # BUG-001
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    environment: Mapped[Optional[str]] = mapped_column(String(100))
    steps_to_reproduce: Mapped[List[str]] = mapped_column(JSON, default=list)
    expected_result: Mapped[str] = mapped_column(Text)
    actual_result: Mapped[str] = mapped_column(Text)
    severity: Mapped[BugSeverity] = mapped_column(SAEnum(BugSeverity), default=BugSeverity.medium)
    priority: Mapped[Priority] = mapped_column(SAEnum(Priority), default=Priority.medium)
    status: Mapped[BugStatus] = mapped_column(SAEnum(BugStatus), default=BugStatus.open)
    root_cause: Mapped[Optional[str]] = mapped_column(Text)
    suggested_fix: Mapped[Optional[str]] = mapped_column(Text)
    screenshots: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    console_logs: Mapped[Optional[List[dict]]] = mapped_column(JSON, default=list)
    network_logs: Mapped[Optional[List[dict]]] = mapped_column(JSON, default=list)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, default=list)
    is_flaky: Mapped[bool] = mapped_column(Boolean, default=False)
    is_environment_issue: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    run: Mapped[Optional["TestRun"]] = relationship("TestRun", back_populates="bugs")
    execution: Mapped[Optional["TestExecution"]] = relationship("TestExecution", back_populates="bugs")


# ─── Automation Scripts ───────────────────────────────────────────────────────

class AutomationScript(Base):
    __tablename__ = "automation_scripts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    test_case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("test_cases.id"))
    script_id: Mapped[str] = mapped_column(String(50), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(20), default="typescript")
    framework: Mapped[str] = mapped_column(String(50), default="playwright")
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    generation_notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    test_case: Mapped["TestCase"] = relationship("TestCase", back_populates="automation_scripts")


# ─── Approvals ────────────────────────────────────────────────────────────────

class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type: Mapped[str] = mapped_column(String(50))  # requirement | story | test_case | bug | test_run
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    status: Mapped[ApprovalStatus] = mapped_column(SAEnum(ApprovalStatus), default=ApprovalStatus.pending)
    comments: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="approvals")


# ─── Attachments ──────────────────────────────────────────────────────────────

class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requirement_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("requirements.id", ondelete="CASCADE"))
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    parsed_content: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    requirement: Mapped[Optional["Requirement"]] = relationship("Requirement", back_populates="attachments")


# ─── Agent Logs ───────────────────────────────────────────────────────────────

class AgentLog(Base):
    __tablename__ = "agent_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phase: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50))
    input_summary: Mapped[Optional[str]] = mapped_column(Text)
    output_summary: Mapped[Optional[str]] = mapped_column(Text)
    reasoning_trace: Mapped[Optional[str]] = mapped_column(Text)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    error: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
