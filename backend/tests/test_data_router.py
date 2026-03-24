"""
Integration tests for data pipeline API endpoints (DATA-02, DATA-09, DATA-11, DATA-16).

DATA-02: Parse user prompt and return detected data sources + series IDs.
DATA-09: Detect frequency conflicts and return resolution options via API.
DATA-11: User source override endpoint (re-validate overridden series ID).
DATA-16: Data preview endpoint — return cleaned/merged dataset before analysis.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Helper: register a user and return auth header
# ---------------------------------------------------------------------------

async def _auth_header(client) -> dict:
    """Register a test user and return the Authorization header dict."""
    reg = await client.post(
        "/auth/register",
        json={"email": "datatest@example.com", "password": "password123"},
    )
    token = reg.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# parse-prompt endpoint
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_parse_prompt_endpoint(client):
    """POST /data/parse-prompt should return detected sources and series for a valid prompt."""
    headers = await _auth_header(client)

    mock_sources = {
        "sources": [
            {
                "source": "FRED",
                "series_id": "GDPC1",
                "display_name": "Real GDP",
                "rationale": "GDP growth requires real GDP series",
            }
        ],
        "date_range": None,
    }

    with patch(
        "app.routers.data.map_prompt_to_sources", return_value=mock_sources
    ), patch(
        "app.routers.data.validate_series", new_callable=AsyncMock, return_value=(True, [])
    ):
        response = await client.post(
            "/data/parse-prompt",
            json={"prompt": "GDP growth since 2000", "mode": "quick"},
            headers=headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert "sources" in data
    assert len(data["sources"]) == 1
    assert data["sources"][0]["series_id"] == "GDPC1"
    assert data["sources"][0]["valid"] is True


@pytest.mark.asyncio
async def test_parse_prompt_unauthenticated(client):
    """POST /data/parse-prompt should return 401 without auth."""
    response = await client.post(
        "/data/parse-prompt",
        json={"prompt": "GDP growth since 2000", "mode": "quick"},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# parse-prompt/override endpoint
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_override_source(client):
    """POST /data/parse-prompt/override should re-validate FRED series and return valid=True."""
    headers = await _auth_header(client)

    with patch(
        "app.routers.data.validate_series", new_callable=AsyncMock, return_value=(True, [])
    ):
        response = await client.post(
            "/data/parse-prompt/override",
            json={"index": 0, "series_id": "GDPC1", "source": "FRED"},
            headers=headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["series_id"] == "GDPC1"
    assert data["source"] == "FRED"
    assert data["valid"] is True


@pytest.mark.asyncio
async def test_override_source_yahoo(client):
    """POST /data/parse-prompt/override with source=YAHOO should not call validate_series."""
    headers = await _auth_header(client)

    with patch(
        "app.routers.data.validate_series", new_callable=AsyncMock
    ) as mock_validate:
        response = await client.post(
            "/data/parse-prompt/override",
            json={"index": 0, "series_id": "AAPL", "source": "YAHOO"},
            headers=headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    mock_validate.assert_not_called()


# ---------------------------------------------------------------------------
# fetch endpoint and frequency conflict
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_assumptions_detailed_gate(client):
    """POST /data/fetch with mode='detailed' should create a job with analysis_mode='detailed'."""
    headers = await _auth_header(client)

    mock_task = MagicMock()
    mock_task.id = "fake-celery-id-detailed"

    with patch("app.routers.data.fetch_data") as mock_fetch_data:
        mock_fetch_data.delay.return_value = mock_task
        response = await client.post(
            "/data/fetch",
            json={
                "sources": [
                    {
                        "source": "FRED",
                        "series_id": "GDPC1",
                        "display_name": "Real GDP",
                        "rationale": "GDP",
                    }
                ],
                "date_range": {"start": "2000-01-01", "end": "2023-12-31"},
                "mode": "detailed",
            },
            headers=headers,
        )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "queued"
    assert "id" in data
    # Verify mock was called
    mock_fetch_data.delay.assert_called_once()
    call_kwargs = mock_fetch_data.delay.call_args
    assert call_kwargs.kwargs.get("mode") == "detailed" or (
        len(call_kwargs.args) >= 4 and call_kwargs.args[3] == "detailed"
    )


@pytest.mark.asyncio
async def test_frequency_conflict_returned(client):
    """GET /data/preview/{job_id} should return FrequencyConflict when task result has conflict status."""
    headers = await _auth_header(client)

    conflict_result = {
        "status": "frequency_conflict",
        "job_id": "test-job-id",
        "conflict": {
            "has_conflict": True,
            "series_frequencies": [
                {"series_id": "AAPL", "frequency": "D", "row_count": 1000},
                {"series_id": "GDPC1", "frequency": "QS", "row_count": 92},
            ],
            "recommendation": "Aggregate AAPL to QS via mean",
            "recommended_method": "mean",
            "target_frequency": "QS",
        },
        "cache_keys": ["yahoo:AAPL:2000-01-01:2023-12-31"],
    }

    mock_task_obj = MagicMock()
    mock_task_obj.id = "celery-conflict-id"

    with patch("app.routers.data.fetch_data") as mock_fetch:
        mock_fetch.delay.return_value = mock_task_obj
        submit = await client.post(
            "/data/fetch",
            json={
                "sources": [
                    {
                        "source": "FRED",
                        "series_id": "GDPC1",
                        "display_name": "Real GDP",
                        "rationale": "GDP",
                    }
                ],
                "date_range": {"start": "2000-01-01", "end": "2023-12-31"},
                "mode": "quick",
            },
            headers=headers,
        )

    job_id = submit.json()["id"]

    with patch("app.routers.data.celery_app") as mock_celery:
        mock_result = MagicMock()
        mock_result.state = "SUCCESS"
        mock_result.result = conflict_result
        mock_celery.AsyncResult.return_value = mock_result

        response = await client.get(
            f"/data/preview/{job_id}",
            headers=headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["has_conflict"] is True
    assert data["recommended_method"] == "mean"
    assert data["target_frequency"] == "QS"
    assert len(data["series_frequencies"]) == 2


@pytest.mark.asyncio
async def test_preview_response(client):
    """GET /data/preview/{job_id} should return DataPreview when task has data_ready status."""
    headers = await _auth_header(client)

    data_ready_result = {
        "status": "data_ready",
        "job_id": "test-job-id",
        "preview_rows": [{"date": "2000-01-01", "value": 10000.0}],
        "column_stats": [
            {
                "name": "value",
                "dtype": "float64",
                "min": 9000.0,
                "max": 22000.0,
                "mean": 15000.0,
                "missing_count": 0,
            }
        ],
        "assumptions": ["Normalized all date indexes to UTC"],
        "total_rows": 92,
        "cache_keys": ["fred:GDPC1:2000-01-01:2023-12-31"],
    }

    mock_task_obj = MagicMock()
    mock_task_obj.id = "celery-ready-id"

    with patch("app.routers.data.fetch_data") as mock_fetch:
        mock_fetch.delay.return_value = mock_task_obj
        submit = await client.post(
            "/data/fetch",
            json={
                "sources": [
                    {
                        "source": "FRED",
                        "series_id": "GDPC1",
                        "display_name": "Real GDP",
                        "rationale": "GDP",
                    }
                ],
                "date_range": {"start": "2000-01-01", "end": "2023-12-31"},
                "mode": "quick",
            },
            headers=headers,
        )

    job_id = submit.json()["id"]

    with patch("app.routers.data.celery_app") as mock_celery:
        mock_result = MagicMock()
        mock_result.state = "SUCCESS"
        mock_result.result = data_ready_result
        mock_celery.AsyncResult.return_value = mock_result

        response = await client.get(
            f"/data/preview/{job_id}",
            headers=headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert "rows" in data
    assert data["total_rows"] == 92
    assert len(data["columns"]) == 1
    assert data["columns"][0]["name"] == "value"
    assert "assumptions" in data
    assert len(data["cache_keys"]) == 1


@pytest.mark.asyncio
async def test_parse_prompt_returns_date_range(client):
    """POST /data/parse-prompt should return date_range extracted from prompt."""
    headers = await _auth_header(client)

    mock_result = {
        "sources": [
            {
                "source": "FRED",
                "series_id": "GDPC1",
                "display_name": "Real GDP",
                "rationale": "GDP growth requires real GDP series",
            }
        ],
        "date_range": {"start": "2000-01-01", "end": "2023-12-31"},
    }

    with patch(
        "app.routers.data.map_prompt_to_sources", return_value=mock_result
    ), patch(
        "app.routers.data.validate_series", new_callable=AsyncMock, return_value=(True, [])
    ):
        response = await client.post(
            "/data/parse-prompt",
            json={"prompt": "GDP growth from 2000 to 2023", "mode": "quick"},
            headers=headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["date_range"] == {"start": "2000-01-01", "end": "2023-12-31"}


@pytest.mark.asyncio
async def test_fetch_without_job_id_succeeds(client):
    """POST /data/fetch should succeed without job_id in the request body."""
    headers = await _auth_header(client)

    mock_task = MagicMock()
    mock_task.id = "fake-celery-no-jobid"

    with patch("app.routers.data.fetch_data") as mock_fetch_data:
        mock_fetch_data.delay.return_value = mock_task
        response = await client.post(
            "/data/fetch",
            json={
                "sources": [
                    {
                        "source": "FRED",
                        "series_id": "GDPC1",
                        "display_name": "Real GDP",
                        "rationale": "GDP",
                    }
                ],
                "date_range": None,
                "mode": "quick",
            },
            headers=headers,
        )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["status"] == "queued"
