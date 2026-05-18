"""
Basic health and auth endpoint tests.
These run without an AI key and verify the API starts correctly.
"""
import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_register_and_login(client):
    # Register a new user
    reg = await client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "Test@1234",
        "full_name": "Test User",
    })
    assert reg.status_code in (200, 201), reg.text

    # Login with that user
    login = await client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "Test@1234",
    })
    assert login.status_code == 200
    assert "access_token" in login.json()


@pytest.mark.asyncio
async def test_unauthenticated_projects_returns_401(client):
    response = await client.get("/api/projects")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_project(client):
    # Register + login first
    await client.post("/api/auth/register", json={
        "email": "proj@example.com",
        "password": "Test@1234",
        "full_name": "Proj User",
    })
    login = await client.post("/api/auth/login", json={
        "email": "proj@example.com",
        "password": "Test@1234",
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create = await client.post("/api/projects", json={
        "name": "Test Project",
        "description": "CI test project",
    }, headers=headers)
    assert create.status_code == 201
    assert create.json()["name"] == "Test Project"
