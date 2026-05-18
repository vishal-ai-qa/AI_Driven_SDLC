# QAgent — AI-Driven SDLC Platform

> Convert business requirements into running tests and Playwright automation scripts — fully autonomous, with human approval checkpoints at every phase.

[![CI](https://github.com/vishal-ai-qa/AI_Driven_SDLC/actions/workflows/ci.yml/badge.svg)](https://github.com/vishal-ai-qa/AI_Driven_SDLC/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![Next.js](https://img.shields.io/badge/Next.js-14-black)
![Claude](https://img.shields.io/badge/AI-Claude%20Sonnet%204.6-orange)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Workflow Overview

**[Open Interactive Flow Diagram](https://htmlpreview.github.io/?https://github.com/vishal-ai-qa/AI_Driven_SDLC/blob/main/WORKFLOW.html)**

The diagram shows the complete 8-phase SDLC pipeline — from raw requirements to deployed Playwright automation — including all 7 AI agents, human checkpoints, and data flow between every component.

---

## What It Does

QAgent automates the entire software testing lifecycle using AI agents powered by Claude Sonnet 4.6:

| Phase | Agent | Input → Output |
|-------|-------|----------------|
| **1 — Ingest** | `RequirementAgent` | BRD / raw text → Structured requirements |
| **2 — Stories** | `StoryAgent` | Requirements → Epics + User stories |
| **3 — Test Cases** | `TestCaseAgent` | Stories → Full test case suite |
| **4 — Gap Detection** | `GapAgent` | Stories → Missing edge cases & security gaps |
| **5 — Execution** | `ExecutionAgent` | Test cases → Live Playwright browser runs |
| **6 — Bug Analysis** | `BugAnalysisAgent` | Failures → Root cause + fix suggestions |
| **8 — Automation** | `AutomationAgent` | Test cases → Downloadable Playwright TypeScript framework |

Human approval checkpoints after phases 1, 2, and 3 ensure AI output is reviewed before the next phase starts.

---

## Key Features

- **Zero-config AI pipeline** — paste requirements, approve, get tests
- **Full traceability** — every test case traces back to its requirement
- **Real-time dashboard** — WebSocket live agent status + execution progress
- **ROI analytics** — token cost, time saved, defect escape cost averted, ROI multiplier
- **Gap detection** — AI scans stories for missing edge cases, ambiguous ACs, security gaps
- **Playwright code generation** — download a complete typed framework ZIP
- **pgvector semantic search** — 1536-dim embeddings on requirements, stories, test cases
- **Anti-hallucination** — every agent output requires `confidence_score` + `source_ref`

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, Tailwind CSS, Radix UI, Zustand, React Query |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 (async) |
| AI | Anthropic Claude Sonnet 4.6, LangGraph, LangChain |
| Database | PostgreSQL 16 + pgvector |
| Queue | Celery + Redis |
| Automation | Playwright 1.44 |
| Container | Docker + Docker Compose |
| CI/CD | GitHub Actions → GHCR |

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- An [Anthropic API key](https://console.anthropic.com/)

### Run in 3 steps

```bash
git clone https://github.com/vishal-ai-qa/AI_Driven_SDLC.git
cd AI_Driven_SDLC
cp .env.example .env
```

Edit `.env` and set `ANTHROPIC_API_KEY` and `SECRET_KEY`, then:

```bash
docker compose up -d
```

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:3000 |
| API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/api/docs |

---

## Usage Walkthrough

1. **Create a project** — give it a name and your app's URL
2. **Paste requirements** — BRD, user stories, Confluence text, anything
3. **Approve requirements** — review AI-extracted requirements, approve good ones
4. **Generate stories** — one click creates epics + user stories with acceptance criteria
5. **Approve stories** — review, edit, approve
6. **Generate test cases** — AI creates functional, security, API, and UI test cases
7. **Run gap analysis** — AI scans for missing edge cases
8. **Start execution** — AI agents run tests via Playwright with live progress
9. **Review bugs** — AI-analyzed defects with root cause and fix suggestions
10. **Download automation** — get a complete Playwright TypeScript framework ZIP

---

## Project Structure

```
AI_Driven_SDLC/
├── backend/                  # FastAPI + AI agents
│   ├── app/
│   │   ├── agents/           # 7 AI agents (BaseAgent subclasses)
│   │   ├── api/routes/       # REST + WebSocket endpoints
│   │   ├── models/           # SQLAlchemy ORM + Pydantic schemas
│   │   ├── services/         # HTML report generation
│   │   └── workers/          # Celery background tasks
│   ├── tests/                # pytest test suite
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                 # Next.js 14 dashboard
│   ├── app/(dashboard)/      # 9 dashboard pages
│   ├── components/           # UI components
│   ├── hooks/                # useWebSocket, etc.
│   └── lib/                  # Axios API client, Zustand store
├── automation/               # Playwright E2E framework
├── WORKFLOW.html             # Interactive pipeline diagram
├── ARCHITECTURE.md           # Full architecture reference
├── docker-compose.yml
└── .env.example
```

---

## Environment Variables

Copy `.env.example` to `.env`. Minimum required:

```env
ANTHROPIC_API_KEY=sk-ant-...       # Required — powers all AI agents
SECRET_KEY=<64-char-random>        # JWT signing key
POSTGRES_PASSWORD=<strong-password>
```

See [`.env.example`](.env.example) for the complete list including WebSocket URLs, upload limits, AI model config, and optional email/Flower settings.

---

## API Reference

Full interactive docs at `http://localhost:8000/api/docs`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login` | JWT login |
| `POST` | `/api/requirements/ingest` | AI-parse raw requirements |
| `POST` | `/api/stories/generate` | AI-generate user stories |
| `POST` | `/api/test-cases/generate` | AI-generate test cases |
| `POST` | `/api/test-runs` | Start AI test execution |
| `GET` | `/api/projects/{id}/roi` | ROI metrics dashboard |
| `POST` | `/api/projects/{id}/detect-gaps` | Run gap analysis |
| `GET` | `/api/automation/download/{id}` | Download Playwright ZIP |
| `GET` | `/api/traceability/{id}` | Full coverage matrix |
| `WS` | `/ws/project/{id}` | Real-time agent events |
| `WS` | `/ws/run/{id}` | Live execution progress |

---

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full design reference including system diagrams, agent design, anti-hallucination rules, database schema, security design, and deployment guide.

---

## CI/CD

GitHub Actions pipeline (`.github/workflows/ci.yml`):

1. **Backend Tests** — pytest against real Postgres + Redis
2. **Frontend Build & Type Check** — `tsc --noEmit` + `next build`
3. **Playwright E2E** — full browser tests (on push to main)
4. **Docker Build & Push** — images pushed to GitHub Container Registry

---

## License

MIT

---

*Built with [Claude Sonnet 4.6](https://anthropic.com) · QAgent v1.0.0*
