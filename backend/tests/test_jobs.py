import pytest
from unittest.mock import MagicMock, patch


@pytest.mark.asyncio
async def test_submit_job(client):
    # Register and get token
    reg = await client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )
    token = reg.json()["access_token"]

    with patch("app.routers.jobs.run_r_analysis") as mock_task:
        mock_task.delay.return_value = MagicMock(id="fake-celery-id")
        response = await client.post(
            "/jobs/",
            json={"r_script": "cat('hello')"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 201
    assert response.json()["status"] == "queued"
    assert "id" in response.json()


@pytest.mark.asyncio
async def test_submit_job_unauthenticated(client):
    response = await client.post("/jobs/", json={"r_script": "cat('hello')"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_job_status(client):
    reg = await client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )
    token = reg.json()["access_token"]

    with patch("app.routers.jobs.run_r_analysis") as mock_task:
        mock_task.delay.return_value = MagicMock(id="fake-celery-id")
        submit = await client.post(
            "/jobs/",
            json={"r_script": "cat('hello')"},
            headers={"Authorization": f"Bearer {token}"},
        )

    job_id = submit.json()["id"]

    with patch("app.routers.jobs.celery_app") as mock_celery:
        mock_result = MagicMock()
        mock_result.state = "PROGRESS"
        mock_result.info = {"stage": "running_r"}
        mock_celery.AsyncResult.return_value = mock_result

        response = await client.get(
            f"/jobs/{job_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json()["status"] == "queued"


@pytest.mark.asyncio
async def test_cancel_job(client):
    reg = await client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )
    token = reg.json()["access_token"]

    with patch("app.routers.jobs.run_r_analysis") as mock_task:
        mock_task.delay.return_value = MagicMock(id="fake-celery-id")
        submit = await client.post(
            "/jobs/",
            json={"r_script": "cat('hello')"},
            headers={"Authorization": f"Bearer {token}"},
        )

    job_id = submit.json()["id"]

    with patch("app.routers.jobs.celery_app") as mock_celery:
        response = await client.post(
            f"/jobs/{job_id}/cancel",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
