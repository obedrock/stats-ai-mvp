from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.job import Job
from app.models.user import User
from app.schemas.jobs import JobCreated, JobStatus, JobSubmit
from app.tasks.analysis import run_r_analysis
from app.tasks.celery_app import celery_app

router = APIRouter()


@router.post("/", response_model=JobCreated, status_code=201)
async def submit_job(
    payload: JobSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = Job(
        user_id=current_user.id,
        r_script=payload.r_script,
        status="queued",
        stage="queued",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    task = run_r_analysis.delay(payload.r_script, str(job.id))
    job.celery_task_id = task.id
    await db.commit()

    return JobCreated(id=job.id, status="queued")


@router.get("/{job_id}", response_model=JobStatus)
async def get_job_status(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.user_id == current_user.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Sync status from Celery if job is still in progress
    if job.celery_task_id and job.status not in ("success", "error", "cancelled"):
        task_result = celery_app.AsyncResult(job.celery_task_id)
        if task_result.state == "PROGRESS":
            meta = task_result.info or {}
            job.stage = meta.get("stage", job.stage)
        elif task_result.state == "SUCCESS":
            result_data = task_result.result or {}
            job.status = result_data.get("status", "success")
            job.stage = "done"
            job.result_stdout = result_data.get("stdout")
            job.result_stderr = result_data.get("stderr")
        elif task_result.state == "FAILURE":
            job.status = "error"
            job.error_message = str(task_result.info)
        elif task_result.state == "REVOKED":
            job.status = "cancelled"
        await db.commit()

    return job


@router.post("/{job_id}/cancel")
async def cancel_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.user_id == current_user.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status in ("success", "error", "cancelled"):
        raise HTTPException(status_code=400, detail="Job already completed")

    if job.celery_task_id:
        celery_app.control.revoke(job.celery_task_id, terminate=True, signal="SIGTERM")
    job.status = "cancelled"
    await db.commit()
    return {"status": "cancelled"}
