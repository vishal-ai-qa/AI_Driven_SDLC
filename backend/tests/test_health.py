"""
Basic smoke tests — health check, auth flow, auth guard, project CRUD.
No AI key required; tests run against a real Postgres instance in CI.
"""
import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_register_and_login(client):
    reg = await client.post("/api/auth/register", json={
        "email": "ci_user1@example.com",
        "username": "ci_user1",
        "password": "Test@1234",
        "full_name": "CI User One",
    })
    assert reg.status_code == 201, reg.text

    login = await client.post("/api/auth/login", json={
        "email": "ci_user1@example.com",
        "password": "Test@1234",
    })
    assert login.status_code == 200
    assert "access_token" in login.json()


@pytest.mark.asyncio
async def test_unauthenticated_projects_returns_401(client):
    response = await client.get("/api/projects")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_and_list_project(client):
    await client.post("/api/auth/register", json={
        "email": "ci_user2@example.com",
        "username": "ci_user2",
        "password": "Test@1234",
        "full_name": "CI User Two",
    })
    login = await client.post("/api/auth/login", json={
        "email": "ci_user2@example.com",
        "password": "Test@1234",
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create = await client.post("/api/projects", json={
        "name": "CI Test Project",
        "description": "Created by CI",
    }, headers=headers)
    assert create.status_code == 201
    assert create.json()["name"] == "CI Test Project"

    lst = await client.get("/api/projects", headers=headers)
    assert lst.status_code == 200
    assert any(p["name"] == "CI Test Project" for p in lst.json())
