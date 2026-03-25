"""Analysis API router.

Provides endpoints for triggering and polling OLS analysis:
  - POST /analysis/run   — Start OLS analysis Celery task
  - GET  /analysis/{job_id} — Poll for analysis results (success, error, or running)
"""
import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.job import Job
from app.models.user import User
from app.schemas.analysis import (
    AnalysisErrorResponse,
    AnalysisResultResponse,
    AnalysisRunRequest,
    ChartData,
    CoefficientRow,
    DiagnosticsBundle,
    DiagnosticResult,
    FollowUpSuggestion,
    ModelSummary,
)
from app.schemas.jobs import JobCreated
from app.tasks.analysis import run_ols_analysis
from app.tasks.celery_app import celery_app

router = APIRouter()


@router.post("/run", response_model=JobCreated, status_code=202)
async def run_analysis(
    body: AnalysisRunRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start OLS analysis for an existing job that has cached data.

    Expects the job to have cached_data_keys populated (set by the data
    fetch pipeline). Transitions the job status to "running" and enqueues
    the run_ols_analysis Celery task.
    """
    try:
        job_uuid = UUID(body.job_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid job_id format")

    result = await db.execute(
        select(Job).where(Job.id == job_uuid)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if not job.cached_data_keys:
        raise HTTPException(status_code=400, detail="Job has no cached data — run data fetch first")

    # Update job to running state
    job.status = "running"
    job.stage = "running_analysis"
    await db.commit()

    # Enqueue Celery task
    task = run_ols_analysis.delay(str(job.id), body.prompt)
    job.celery_task_id = task.id
    await db.commit()

    return JobCreated(id=job.id, status="running")


@router.get("/{job_id}")
async def get_analysis_result(
    job_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Poll for analysis results.

    Returns:
    - AnalysisResultResponse when job.status == "success"
    - AnalysisErrorResponse when job.status == "error" and error_explanation is set
    - Running status dict when job is still in progress
    """
    try:
        job_uuid = UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid job_id format")

    result = await db.execute(
        select(Job).where(Job.id == job_uuid)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Success path: full structured results
    if job.status == "success" and job.r_result_json:
        r_result = json.loads(job.r_result_json)
        follow_up_suggestions = json.loads(job.follow_up_suggestions) if job.follow_up_suggestions else []

        # Map R plotly_charts to ChartData schema
        charts: list[ChartData] = []
        for chart in r_result.get("plotly_charts", []):
            # Charts may already be parsed (dicts) or still need inner JSON parsing
            if isinstance(chart.get("json"), str):
                parsed = json.loads(chart["json"])
                charts.append(ChartData(
                    name=chart["name"],
                    data=parsed.get("data", []),
                    layout=parsed.get("layout", {}),
                ))
            else:
                charts.append(ChartData(
                    name=chart["name"],
                    data=chart.get("data", []),
                    layout=chart.get("layout", {}),
                ))

        # Build coefficient rows
        coefficients = [
            CoefficientRow(**row) for row in r_result.get("coefficients", [])
        ]

        # Build model summary
        ms = r_result.get("model_summary", {})
        model_summary = ModelSummary(
            r_squared=ms.get("r_squared", 0.0),
            adj_r_squared=ms.get("adj_r_squared", 0.0),
            f_statistic=ms.get("f_statistic", 0.0),
            f_p_value=ms.get("f_p_value", 0.0),
            n_obs=ms.get("n_obs", 0),
            degrees_of_freedom=ms.get("degrees_of_freedom", 0),
        )

        # Build diagnostics bundle
        diag = r_result.get("diagnostics", {})
        bp = diag.get("breusch_pagan", {})
        dw = diag.get("durbin_watson", {})
        sw = diag.get("shapiro_wilk", {})
        # R returns [] (empty list) for VIF when there's only one predictor;
        # coerce to dict for Pydantic validation
        vif_raw = diag.get("vif", {})
        vif_dict = vif_raw if isinstance(vif_raw, dict) else {}
        diagnostics = DiagnosticsBundle(
            breusch_pagan=DiagnosticResult(
                statistic=bp.get("statistic", 0.0),
                p_value=bp.get("p_value"),
                df=bp.get("df"),
            ),
            durbin_watson=DiagnosticResult(
                statistic=dw.get("statistic", 0.0),
                p_value=dw.get("p_value"),
            ),
            vif=vif_dict,
            shapiro_wilk=DiagnosticResult(
                statistic=sw.get("statistic", 0.0),
                p_value=sw.get("p_value"),
            ),
        )

        # Build follow-up suggestions
        suggestions = [
            FollowUpSuggestion(**s) for s in follow_up_suggestions
        ]

        return AnalysisResultResponse(
            job_id=str(job.id),
            status="success",
            coefficients=coefficients,
            model_summary=model_summary,
            diagnostics=diagnostics,
            charts=charts,
            r_code=job.r_script or "",
            interpretation=job.interpretation or "",
            follow_up_suggestions=suggestions,
        )

    # Error path: Claude-interpreted error explanation
    if job.status == "error" and job.error_explanation is not None:
        return AnalysisErrorResponse(
            job_id=str(job.id),
            status="error",
            error_explanation=job.error_explanation,
            suggested_prompt=job.suggested_prompt or "",
            r_stderr=job.result_stderr or "",
            r_code=job.r_script or "",
        )

    # Still running: check Celery task state for current stage
    if job.celery_task_id:
        task_result = celery_app.AsyncResult(job.celery_task_id)
        stage = job.stage or "queued"
        if task_result.info and isinstance(task_result.info, dict):
            stage = task_result.info.get("stage", stage)
        return {"status": "running", "stage": stage, "job_id": str(job.id)}

    return {"status": job.status, "stage": job.stage or "queued", "job_id": str(job.id)}
