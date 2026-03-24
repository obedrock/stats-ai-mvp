"""
Integration tests for file upload endpoint (DATA-12, DATA-14).

DATA-12: Accept CSV, Excel, JSON uploads and return parsed preview.
DATA-14: Allow user to override auto-detected column mappings (date, variable names).
"""

import io
import os

import pytest


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

_FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


async def _auth_header(client) -> dict:
    """Register a test user and return the Authorization header dict."""
    reg = await client.post(
        "/auth/register",
        json={"email": "upload_test@example.com", "password": "password123"},
    )
    token = reg.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# CSV upload
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upload_csv_returns_preview(client):
    """POST /data/upload with sample.csv should return preview with columns and total_rows."""
    headers = await _auth_header(client)

    csv_path = os.path.join(_FIXTURES_DIR, "sample.csv")
    with open(csv_path, "rb") as f:
        content = f.read()

    response = await client.post(
        "/data/upload",
        files={"file": ("sample.csv", io.BytesIO(content), "text/csv")},
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "columns" in data
    assert "preview" in data
    assert "total_rows" in data
    assert data["total_rows"] > 0
    assert isinstance(data["columns"], list)
    assert len(data["columns"]) > 0


# ---------------------------------------------------------------------------
# Excel upload
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upload_excel_returns_preview(client):
    """POST /data/upload with sample.xlsx should return preview with columns and total_rows."""
    headers = await _auth_header(client)

    xlsx_path = os.path.join(_FIXTURES_DIR, "sample.xlsx")
    with open(xlsx_path, "rb") as f:
        content = f.read()

    response = await client.post(
        "/data/upload",
        files={
            "file": (
                "sample.xlsx",
                io.BytesIO(content),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "columns" in data
    assert "preview" in data
    assert "total_rows" in data
    assert data["total_rows"] > 0


# ---------------------------------------------------------------------------
# Invalid file type
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upload_invalid_type_rejected(client):
    """POST /data/upload with a .txt file should return HTTP 422 with an error message."""
    headers = await _auth_header(client)

    fake_content = b"This is a text file, not a supported format."

    response = await client.post(
        "/data/upload",
        files={"file": ("report.txt", io.BytesIO(fake_content), "text/plain")},
        headers=headers,
    )

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Column mapping confirmation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mapping_override(client):
    """POST /data/upload/confirm-mapping with valid column list should return 200."""
    headers = await _auth_header(client)

    response = await client.post(
        "/data/upload/confirm-mapping",
        json={
            "columns": [
                {"name": "date", "type": "date", "role": "date_index"},
                {"name": "gdp", "type": "numeric", "role": "dependent"},
                {"name": "inflation", "type": "numeric", "role": "independent"},
            ]
        },
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "confirmed"


@pytest.mark.asyncio
async def test_upload_unauthenticated(client):
    """POST /data/upload should return 401 without auth."""
    response = await client.post(
        "/data/upload",
        files={"file": ("test.csv", io.BytesIO(b"a,b\n1,2"), "text/csv")},
    )
    assert response.status_code == 401
