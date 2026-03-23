import pytest


@pytest.mark.asyncio
async def test_register(client):
    response = await client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate(client):
    await client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )
    response = await client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password456"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_weak_password(client):
    response = await client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "short"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login(client):
    await client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )
    response = await client.post(
        "/auth/token",
        data={"username": "test@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_invalid(client):
    response = await client.post(
        "/auth/token",
        data={"username": "test@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me(client):
    reg = await client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )
    token = reg.json()["access_token"]
    response = await client.get(
        "/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_me_unauthorized(client):
    response = await client.get("/auth/me")
    assert response.status_code == 401
