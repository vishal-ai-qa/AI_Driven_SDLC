"""
Celery tasks — wraps AI agent calls for async execution with full traceability.
"""
import asyncio
from uuid import UUID

from app.workers.celery_app import celery_app


def _run(coro):
    """Run async coroutine in Celery sync context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, name="app.workers.tasks.run_requirement_ingestion", max_retries=2)
def run_requirement_ingestion(self, project_id: str, content: str, source_type: str):
    from app.agents.requirement_agent import RequirementAgent
    agent = RequirementAgent()
    return _run(agent.run(project_id=project_id, content=content, source_type=source_type))


@celery_app.task(bind=True, name="app.workers.tasks.run_story_generation", max_retries=2)
def run_story_generation(self, project_id: str, requirements: list):
    from app.agents.story_agent import StoryAgent
    agent = StoryAgent()
    return _run(agent.run(project_id=project_id, requirements=requirements))


@celery_app.task(bind=True, name="app.workers.tasks.run_test_case_generation", max_retries=2)
def run_test_case_generation(self, project_id: str, stories: list):
    from app.agents.test_case_agent import TestCaseAgent
    agent = TestCaseAgent()
    return _run(agent.run(project_id=project_id, stories=stories))


@celery_app.task(bind=True, name="app.workers.tasks.run_test_execution", max_retries=1)
def run_test_execution(self, run_id: str, test_case: dict, app_url: str, credentials: dict = None):
    from app.agents.execution_agent import ExecutionAgent
    agent = ExecutionAgent(run_id=run_id)
    return _run(agent.run(test_case=test_case, app_url=app_url, credentials=credentials))


@celery_app.task(bind=True, name="app.workers.tasks.run_automation_generation", max_retries=2)
def run_automation_generation(self, test_case: dict, project_name: str, base_url: str):
    from app.agents.automation_agent import AutomationAgent
    agent = AutomationAgent()
    return _run(agent.run(test_case=test_case, project_name=project_name, base_url=base_url))
