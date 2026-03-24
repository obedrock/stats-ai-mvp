"""Data pipeline API router.

Provides all endpoints for the data acquisition and preparation pipeline:
prompt parsing, source override, file upload, data fetching, frequency
resolution, and data preview.

DATA-02: Parse user prompt and return detected data sources.
DATA-09: Frequency conflict detection and resolution.
DATA-11: User source override (re-validate overridden series ID).
DATA-12: File upload and preview.
DATA-14: Column mapping confirmation.
DATA-16: Data preview endpoint.
"""
import asyncio
import json
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.job import Job
from app.models.user import User
from app.schemas.data import (
    ConfirmMapping,
    DataPreview,
    FrequencyConflict,
    ParsedSource,
    PromptParseResponse,
    PromptSubmit,
    ResolutionChoice,
    SourceOverride,
    UploadResult,
)
from app.schemas.jobs import JobCreated
from app.schemas.data import FetchRequest
from app.services.fred_fetcher import validate_series
from app.services.series_mapper import map_prompt_to_sources
from app.services.file_parser import parse_uploaded_file
from app.tasks.data_pipeline import fetch_data
from app.tasks.celery_app import celery_app

router = APIRouter()


@router.post("/parse-prompt", response_model=PromptParseResponse)
async def parse_prompt(
    payload: PromptSubmit,
    current_user: User = Depends(get_current_user),
):
    """Parse a natural language prompt and return detected data sources.

    Calls Claude via series_mapper to extract structured source+series_id pairs,
    then validates FRED series IDs against the FRED REST API. Run in a thread
    executor since map_prompt_to_sources is a synchronous Claude API call.
    """
    loop = asyncio.get_event_loop()
    try:
        parsed_result = await loop.run_in_executor(
            None, map_prompt_to_sources, payload.prompt
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    raw_sources = parsed_result["sources"]
    date_range_obj = parsed_result.get("date_range")

    parsed: list[ParsedSource] = []
    for src in raw_sources:
        if src["source"] == "FRED":
            valid, suggestions = await validate_series(src["series_id"])
        else:
            # Yahoo symbols: basic non-empty check
            valid = bool(src["series_id"].strip())
            suggestions = []

        parsed.append(
            ParsedSource(
                source=src["source"],
                series_id=src["series_id"],
                display_name=src["display_name"],
                rationale=src["rationale"],
                valid=valid,
                suggestions=suggestions,
            )
        )

    return PromptParseResponse(sources=parsed, date_range=date_range_obj)


@router.post("/parse-prompt/override", response_model=ParsedSource)
async def override_source(
    payload: SourceOverride,
    current_user: User = Depends(get_current_user),
):
    """Re-validate an overridden series ID.

    Uses payload.source to determine validation type:
    - FRED: calls validate_series against FRED REST API
    - YAHOO: basic non-empty string check
    """
    if payload.source == "FRED":
        valid, suggestions = await validate_series(payload.series_id)
    else:
        valid = bool(payload.series_id.strip())
        suggestions = []

    return ParsedSource(
        source=payload.source,
        series_id=payload.series_id,
        display_name=payload.series_id,  # No display_name in override; use series_id
        rationale="User override",
        valid=valid,
        suggestions=suggestions,
    )


@router.post("/upload", response_model=UploadResult)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload a CSV, Excel, or JSON file and return a parsed preview.

    Auto-detects column types and applies auto-fix transformations.
    Unsupported file types raise HTTP 422.
    """
    content = await file.read()
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            None, parse_uploaded_file, content, file.filename
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return UploadResult(
        preview=result["preview"],
        columns=result["columns"],
        changes=result["changes"],
        total_rows=result["total_rows"],
    )


@router.post("/upload/confirm-mapping")
async def confirm_mapping(
    payload: ConfirmMapping,
    current_user: User = Depends(get_current_user),
):
    """Confirm user-corrected column mappings for an uploaded file.

    Stores the mapping acknowledgment (future: persist to session/job).
    """
    return {"status": "confirmed", "columns": len(payload.columns)}


@router.post("/fetch", response_model=JobCreated, status_code=201)
async def fetch_data_endpoint(
    payload: FetchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start data fetching by enqueuing a Celery fetch_data task.

    Creates a Job record in the DB, enqueues the task with all source/range/mode
    parameters, and returns the job ID for polling.
    """
    # Use provided date_range or default to last 20 years
    date_range = payload.date_range
    if date_range is None:
        today = date.today()
        date_range = {
            "start": str(today.replace(year=today.year - 20)),
            "end": str(today),
        }

    job = Job(
        user_id=current_user.id,
        prompt=None,  # Prompt stored at analysis submit time
        data_sources=json.dumps(
            [s.model_dump() for s in payload.sources]
        ),
        date_range=json.dumps(date_range),
        analysis_mode=payload.mode,
        status="queued",
        stage="queued",
    )
    if payload.resolution:
        job.resolution_method = payload.resolution.method
    db.add(job)
    await db.commit()
    await db.refresh(job)

    task = fetch_data.delay(
        job_id=str(job.id),
        sources=[s.model_dump() for s in payload.sources],
        date_range=date_range,
        mode=payload.mode,
        resolution=payload.resolution.model_dump() if payload.resolution else None,
    )
    job.celery_task_id = task.id
    await db.commit()

    return JobCreated(id=job.id, status="queued")


@router.post("/resolve-frequency", response_model=JobCreated, status_code=201)
async def resolve_frequency(
    job_id: str,
    resolution: ResolutionChoice,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accept user's frequency resolution choice and re-enqueue the fetch task.

    Looks up the original job to retrieve sources and date_range, then
    re-submits the Celery task with the chosen resolution applied.
    """
    try:
        job_uuid = UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid job_id format")

    result = await db.execute(
        select(Job).where(Job.id == job_uuid, Job.user_id == current_user.id)
    )
    original_job = result.scalar_one_or_none()
    if not original_job:
        raise HTTPException(status_code=404, detail="Job not found")

    sources = json.loads(original_job.data_sources) if original_job.data_sources else []

    # Use stored date_range from the original job
    date_range = json.loads(original_job.date_range) if original_job.date_range else {"start": "2000-01-01", "end": "2023-12-31"}

    # Re-enqueue fetch with resolution
    new_job = Job(
        user_id=current_user.id,
        data_sources=original_job.data_sources,
        date_range=original_job.date_range,  # Carry forward stored date_range
        analysis_mode=original_job.analysis_mode,
        resolution_method=resolution.method,
        status="queued",
        stage="queued",
    )
    db.add(new_job)
    await db.commit()
    await db.refresh(new_job)

    task = fetch_data.delay(
        job_id=str(new_job.id),
        sources=sources,
        date_range=date_range,
        mode=original_job.analysis_mode or "quick",
        resolution=resolution.model_dump(),
    )
    new_job.celery_task_id = task.id
    await db.commit()

    return JobCreated(id=new_job.id, status="queued")


@router.get("/preview/{job_id}")
async def get_preview(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get data preview or frequency conflict for a fetch job.

    Returns:
    - DataPreview when task result has status "data_ready"
    - FrequencyConflict schema when status is "frequency_conflict"
    - Stage info dict when task is still in progress
    """
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.user_id == current_user.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if not job.celery_task_id:
        return {"status": "queued", "stage": job.stage}

    task_result = celery_app.AsyncResult(job.celery_task_id)

    if task_result.state == "PROGRESS":
        meta = task_result.info or {}
        return {
            "status": "in_progress",
            "stage": meta.get("stage", "fetching_data"),
            "sub_status": meta.get("sub_status"),
        }

    if task_result.state == "SUCCESS":
        data = task_result.result or {}
        task_status = data.get("status")

        if task_status == "frequency_conflict":
            conflict = data["conflict"]
            return FrequencyConflict(
                has_conflict=conflict["has_conflict"],
                series_frequencies=conflict["series_frequencies"],
                recommendation=conflict["recommendation"],
                recommended_method=conflict["recommended_method"],
                target_frequency=conflict["target_frequency"],
            )

        if task_status == "data_ready":
            return DataPreview(
                rows=data["preview_rows"],
                total_rows=data["total_rows"],
                columns=data["column_stats"],
                assumptions=data["assumptions"],
                cache_keys=data["cache_keys"],
            )

    if task_result.state == "FAILURE":
        raise HTTPException(
            status_code=500,
            detail=f"Data fetch failed: {task_result.info}",
        )

    return {"status": task_result.state.lower(), "stage": job.stage}
