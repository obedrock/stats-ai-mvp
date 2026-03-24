"""TDD tests for Plan 02-09: FetchRequest schema fixes and date_range flow.

These tests define the correct behavior BEFORE the implementation is fixed:
- FetchRequest should not require job_id
- FetchRequest.date_range should be Optional with None default
- map_prompt_to_sources should return dict with 'sources' and 'date_range' keys
- parse-prompt endpoint should return date_range from Claude
- /data/fetch should accept request without job_id and return 201
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.data import FetchRequest


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------

def test_fetch_request_no_job_id():
    """FetchRequest instantiation without job_id should succeed (no ValidationError)."""
    req = FetchRequest(sources=[], date_range=None)
    assert req.sources == []
    assert req.date_range is None


def test_fetch_request_date_range_none():
    """FetchRequest with date_range=None should succeed (defaults to None)."""
    req = FetchRequest(sources=[])
    assert req.date_range is None


def test_fetch_request_date_range_provided():
    """FetchRequest with explicit date_range dict should succeed."""
    req = FetchRequest(
        sources=[],
        date_range={"start": "2010-01-01", "end": "2023-12-31"},
    )
    assert req.date_range == {"start": "2010-01-01", "end": "2023-12-31"}


def test_fetch_request_no_job_id_field():
    """FetchRequest should NOT have a job_id field."""
    req = FetchRequest(sources=[])
    assert not hasattr(req, "job_id")


# ---------------------------------------------------------------------------
# series_mapper tests
# ---------------------------------------------------------------------------

def test_map_prompt_returns_dict_with_date_range():
    """map_prompt_to_sources should return a dict with 'sources' and 'date_range' keys."""
    from app.services import series_mapper

    mock_tool_use = MagicMock()
    mock_tool_use.type = "tool_use"
    mock_tool_use.input = {
        "sources": [
            {
                "source": "FRED",
                "series_id": "GDPC1",
                "display_name": "Real GDP",
                "rationale": "GDP growth.",
            }
        ],
        "date_range": {"start": "2000-01-01", "end": "2023-12-31"},
    }
    mock_response = MagicMock()
    mock_response.content = [mock_tool_use]

    with patch("app.services.series_mapper.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = series_mapper.map_prompt_to_sources("GDP growth from 2000 to 2023")

    assert isinstance(result, dict), "map_prompt_to_sources must return a dict"
    assert "sources" in result, "result must have 'sources' key"
    assert "date_range" in result, "result must have 'date_range' key"
    assert result["date_range"] == {"start": "2000-01-01", "end": "2023-12-31"}
    assert len(result["sources"]) == 1


# ---------------------------------------------------------------------------
# Router integration tests
# ---------------------------------------------------------------------------

async def _auth_header(client) -> dict:
    """Register a test user and return the Authorization header dict."""
    reg = await client.post(
        "/auth/register",
        json={"email": "plan09test@example.com", "password": "password123"},
    )
    token = reg.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


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
