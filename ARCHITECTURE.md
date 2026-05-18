# QAgent — AI-Native SDLC Platform
## Architecture & Design Reference

> Version 1.0.0 | Last updated: 2026-05-18

---

## 1. System Overview

QAgent is an enterprise-grade AI-driven SDLC platform that autonomously converts business requirements into running tests and Playwright automation scripts — with full traceability and human validation checkpoints at every phase.

```
Business Requirements
        │
        ▼
┌──────────────────────────────────────────────────────────┐
│                    SDLC PIPELINE (9 Phases)               │
│                                                          │
│  P1:Ingest → P2:Stories → P3:TestCases → P4:Checkpoint  │
│       ↓           ↓            ↓               ↓        │
│  P5:Execute → P6:Bugs → P7:SignOff → P8:Automation      │
└──────────────────────────────────────────────────────────┘
        │
        ▼
 Playwright Framework + HTML Reports
```

---

## 2. Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend | Next.js + Tailwind + ShadCN/Radix | 14.x |
| Backend | Python FastAPI | 0.111 |
| AI Orchestration | LangGraph + Anthropic Claude | Sonnet 4.6 |
| AI Agents | Custom agents (6) | — |
| Database | PostgreSQL + pgvector | 16 |
| Queue | Celery + Redis | 5.x |
| Browser Automation | Playwright | 1.44 |
| Container | Docker + Compose | — |
| CI/CD | GitHub Actions | — |

---

## 3. System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                       CLIENT LAYER                           │
│  Next.js 14 (App Router)  +  Tailwind  +  ShadCN           │
│  ├── Dashboard (9 modules)                                   │
│  ├── Real-time WebSocket (agent status + run progress)       │
│  └── Zustand store + React Query                            │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP + WebSocket
┌────────────────────────────▼────────────────────────────────┐
│                       API LAYER                              │
│  FastAPI 0.111                                              │
│  ├── /api/auth           JWT authentication                  │
│  ├── /api/projects       Project management                  │
│  ├── /api/requirements   P1 ingestion + CRUD                 │
│  ├── /api/stories        P2 generation + approval            │
│  ├── /api/test-cases     P3 generation + approval            │
│  ├── /api/test-runs      P5 execution trigger                │
│  ├── /api/bugs           P6 bug reports + triage             │
│  ├── /api/automation     P8 Playwright generation            │
│  ├── /api/traceability   Coverage matrix                     │
│  ├── /api/approvals      Human sign-off workflow             │
│  └── /ws/...             WebSocket streams                   │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                    AGENT ORCHESTRATION LAYER                 │
│  LangGraph StateGraph                                       │
│  ├── RequirementAgent     (Phase 1) BRD → Structured REQs   │
│  ├── StoryAgent           (Phase 2) REQs → Epics + Stories   │
│  ├── TestCaseAgent        (Phase 3) Stories → Test Cases     │
│  ├── ExecutionAgent       (Phase 5) Playwright browser agent │
│  ├── BugAnalysisAgent     (Phase 6) Root cause + fix hints   │
│  └── AutomationAgent      (Phase 8) Playwright TS code gen   │
│                                                             │
│  Anti-hallucination rules enforced in ALL agents:           │
│  - confidence_score required on every output               │
│  - NEEDS_CLARIFICATION markers                             │
│  - source_ref tracing to input text                        │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                     DATA LAYER                               │
│  PostgreSQL 16 + pgvector                                   │
│  ├── users, projects, project_members                       │
│  ├── requirements (+ 1536-dim embedding)                    │
│  ├── epics, user_stories (+ embedding)                      │
│  ├── test_cases (+ embedding)                               │
│  ├── test_runs, test_executions                             │
│  ├── bugs                                                   │
│  ├── automation_scripts                                     │
│  ├── approvals                                              │
│  └── agent_logs                                             │
│                                                             │
│  Redis                                                      │
│  ├── Celery task broker + result backend                    │
│  └── Session cache                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Agent Design

Each agent inherits `BaseAgent` which enforces:

```python
ANTI_HALLUCINATION_RULES = """
1. NEVER invent business logic not in requirements
2. NEVER fabricate API endpoints, fields, validations
3. Mark missing info as NEEDS_CLARIFICATION
4. confidence_score < 0.7 → needs_clarification = true
5. Include source_ref for every output item
...
"""
```

### Agent Flow (LangGraph)

```
phase1_ingest
    │
    ▼
await_req_approval ──(not approved)──► END
    │ (approved)
    ▼
phase2_stories
    │
    ▼
await_story_approval ──(not approved)──► END
    │ (approved)
    ▼
phase3_test_cases
    │
    ▼
await_tc_approval ──(not approved)──► END
    │ (approved)
    ▼
phase5_execution
    │
    ▼
phase6_bug_analysis
    │
    ▼
await_signoff ──(not signed off)──► END
    │ (signed off)
    ▼
phase8_automation
    │
    ▼
END
```

Human checkpoint nodes pause the pipeline and wait for external approval via the REST API before proceeding.

---

## 5. Database Schema (Key Entities)

```
projects
  └── requirements (REQ-001, REQ-002...)
        └── user_stories (US-001, US-002...)
              └── test_cases (TC-001, TC-002...)
                    └── test_executions
                          └── bugs (BUG-001, BUG-002...)
                    └── automation_scripts

test_runs ──contains──► test_executions
approvals ──refers to──► any entity
agent_logs ──tracks──► all agent calls
```

---

## 6. Traceability Engine

Every artifact carries mandatory traceability fields:

```
Requirement → req_id  (REQ-001)
User Story  → story_ref → requirement_ref
Test Case   → tc_id, story_ref, requirement_ref, acceptance_criteria_ref
Bug         → linked to test_execution → test_case → story → requirement
Automation  → linked to test_case → story → requirement
```

The `/api/traceability/{project_id}` endpoint computes a live coverage matrix and returns a JSON tree structure visualized in the dashboard.

---

## 7. Security Design

| Concern | Implementation |
|---------|---------------|
| Auth | JWT (HS256), 60-min access + 7-day refresh |
| Passwords | bcrypt hashed |
| App credentials | Fernet symmetric encryption at rest |
| SQL injection | SQLAlchemy ORM parameterized queries |
| CORS | Explicit origin allowlist |
| Secrets in logs | Never log credentials, tokens, or API keys |
| File upload | MIME type validation + size limit |

---

## 8. API Contracts Summary

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/auth/login | JWT login |
| GET | /api/projects | List projects |
| POST | /api/requirements/ingest | AI-parse raw text |
| POST | /api/stories/generate | AI-generate stories |
| POST | /api/test-cases/generate | AI-generate test cases |
| POST | /api/test-runs | Create + trigger execution |
| GET | /api/bugs | List bugs |
| POST | /api/automation/generate | Generate Playwright scripts |
| GET | /api/automation/download/{id} | Download framework ZIP |
| GET | /api/traceability/{id} | Coverage matrix |
| POST | /api/approvals | Sign off on any entity |
| WS | /ws/project/{id} | Agent event stream |
| WS | /ws/run/{id} | Execution progress stream |

Full OpenAPI docs: `GET /api/docs`

---

## 9. Playwright Framework Structure

```
automation/
├── playwright.config.ts     # Multi-browser + API project config
├── package.json
├── tsconfig.json
├── src/
│   ├── pages/               # Page Object Model
│   │   ├── BasePage.ts      # Shared POM base class
│   │   ├── LoginPage.ts
│   │   └── DashboardPage.ts
│   ├── fixtures/
│   │   └── base.ts          # Extended test fixture
│   ├── utils/
│   │   └── api-client.ts    # Typed API test client
│   └── test-data/           # JSON fixtures
├── tests/
│   ├── auth/
│   │   ├── auth.setup.ts    # Global auth state setup
│   │   └── login.spec.ts    # TC-AUTH-001..005
│   └── api/
│       └── health.api.spec.ts
└── playwright/.auth/
    └── user.json            # Saved auth state (gitignored)
```

---

## 10. HTML Reporting

The `ReportService` generates two HTML report types:

1. **Bug Report** (`bug_report.html`) — full defect list with root cause, suggested fix, screenshots
2. **Execution Summary** (`execution_summary.html`) — pass/fail matrix per test case

Reports are served at `/reports/runs/{run_id}/` by FastAPI's static file server.

---

## 11. Deployment

### Development

```bash
cp .env.example .env
# Fill ANTHROPIC_API_KEY in .env
docker compose up -d
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/api/docs
```

### Production

```bash
docker compose -f docker-compose.yml --profile monitoring up -d
```

Additional services in production:
- Flower (Celery monitoring): port 5555
- PostgreSQL with persistent volumes
- Redis with AOF persistence

### GitHub Actions CI/CD

The `.github/workflows/ci.yml` pipeline:
1. Runs backend pytest suite against a real Postgres/Redis instance
2. Type-checks and builds the Next.js frontend
3. Runs Playwright E2E tests (on push to main)
4. Builds and pushes Docker images to GHCR

---

## 12. Environment Variables

See `.env.example` for the complete list. Minimum required:

```env
ANTHROPIC_API_KEY=sk-ant-...
SECRET_KEY=<64-char-random>
POSTGRES_PASSWORD=<strong-password>
```

---

## 13. Multi-Agent Communication

```
User Request
    │
    ▼
FastAPI Route (async)
    │
    ├── BackgroundTask (for quick jobs)
    │       └── calls agent directly
    │
    └── Celery Task (for long-running jobs)
            └── Redis broker
                    └── Worker process
                            └── Agent.run()
                                    └── Anthropic API
                                    └── Playwright browser
                                    └── PostgreSQL write
```

Real-time updates flow back via WebSocket:
```
AgentLog table ──polls──► WebSocket handler ──broadcasts──► Dashboard
```

---

## 14. Extensibility

| Extension Point | How to Add |
|----------------|-----------|
| New AI provider | Subclass `BaseAgent`, swap `_client` |
| New test type | Add to `TestCaseAgent` SYSTEM_PROMPT types list |
| New report format | Add Jinja2 template to `ReportService` |
| New approval workflow | Extend `Approval` model + `/api/approvals` |
| New automation framework | New agent subclass + zip builder |
| Vector search | `Requirement.embedding` + pgvector similarity queries |

---

*Built with Claude Sonnet 4.6 | QAgent v1.0.0*
