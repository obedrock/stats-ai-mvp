import json
import os
import signal
import subprocess
import sys
import tempfile
import uuid

import pandas as pd
import redis
from celery import current_task  # noqa: F401
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from .celery_app import celery_app
from app.models.job import Job
from app.services.data_pipeline import clean_and_merge
from app.services.r_code_gen import generate_ols_slots, render_ols_script
from app.services.r_interpreter import explain_r_error, interpret_ols_results

_current_proc = None


def _sigterm_handler(signum, frame):
    """Kill the R subprocess when Celery revokes the task."""
    global _current_proc
    if _current_proc and _current_proc.poll() is None:
        _current_proc.terminate()
        try:
            _current_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _current_proc.kill()
    sys.exit(0)


signal.signal(signal.SIGTERM, _sigterm_handler)


@celery_app.task(bind=True, name="run_r_analysis")
def run_r_analysis(self, r_script: str, job_id: str):
    global _current_proc
    self.update_state(state="PROGRESS", meta={"stage": "queued", "job_id": job_id})

    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = os.path.join(tmpdir, "analysis.R")
        with open(script_path, "w") as f:
            f.write(r_script)

        self.update_state(state="PROGRESS", meta={"stage": "running_r", "job_id": job_id})

        try:
            _current_proc = subprocess.Popen(
                [
                    "docker",
                    "run",
                    "--rm",
                    "--network",
                    "none",
                    "--memory",
                    "512m",
                    "--cpus",
                    "1.0",
                    "--read-only",
                    "--tmpfs",
                    "/tmp:size=64m",
                    "--user",
                    "1000",
                    "-v",
                    f"{script_path}:/analysis.R:ro",
                    "stats-ai-r-sandbox",
                    "Rscript",
                    "/analysis.R",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = _current_proc.communicate(timeout=60)
            returncode = _current_proc.returncode
        except subprocess.TimeoutExpired:
            _current_proc.kill()
            _current_proc.communicate()
            _current_proc = None
            raise RuntimeError("R script execution timed out after 60 seconds")
        finally:
            _current_proc = None

        if returncode != 0:
            return {
                "status": "error",
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "job_id": job_id,
            }

        return {
            "status": "success",
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "job_id": job_id,
        }


@celery_app.task(bind=True, name="run_ols_analysis")
def run_ols_analysis(self, job_id: str, prompt: str):
    """Full OLS analysis pipeline: data reconstruction -> Claude Stage 1 -> R Docker -> Claude Stage 2 -> Job update.

    Steps:
    1. Update state to "preparing"
    2. Load Job from DB (sync SQLAlchemy session)
    3. Reconstruct DataFrame from Redis cache keys stored on Job
    4. Get column names from DataFrame
    5. Call Stage 1 Claude: generate_ols_slots() -> dep_var, indep_vars, transformations
    6. Render R script: render_ols_script() -> filled R script string
    7. Write CSV + R script to tmpdir, run Docker with two volume mounts
    8. On success: parse JSON stdout, call Stage 2 Claude, update Job with success fields
    9. On R error: call error interpretation, update Job with error fields
    10. Return {"status": ..., "job_id": ...}
    """
    global _current_proc

    self.update_state(state="PROGRESS", meta={"stage": "preparing", "job_id": job_id})

    # Sync SQLAlchemy engine for Celery worker context
    from app.config import settings
    database_url = settings.database_url.replace("+asyncpg", "")
    engine = create_engine(database_url)

    try:
        # Step 2: Load Job from DB
        with Session(engine) as session:
            job = session.get(Job, uuid.UUID(job_id))
            if not job:
                raise ValueError(f"Job {job_id} not found in database")
            cached_data_keys = json.loads(job.cached_data_keys) if job.cached_data_keys else []

        # Step 3: Reconstruct DataFrame from Redis cache
        redis_url = settings.redis_url
        redis_client = redis.from_url(redis_url)

        dataframes: dict[str, pd.DataFrame] = {}
        for cache_key in cached_data_keys:
            raw = redis_client.get(cache_key)
            if raw is None:
                raise ValueError(f"Cache key {cache_key!r} not found in Redis — data may have expired")
            df = pd.DataFrame(pd.read_json(raw.decode("utf-8")))
            # Restore UTC timezone after JSON round-trip (same as fetch_data task)
            if df.index.tz is None:
                df.index = df.index.tz_localize("UTC")
            # Use series_id from cache key (format: source:series_id:start:end)
            series_id = cache_key.split(":")[1]
            dataframes[series_id] = df

        result = clean_and_merge(dataframes)
        df = result["merged_df"]

        # Step 4: Get column names (exclude date index)
        column_names = [col for col in df.columns.tolist()]

        # Step 5: Call Stage 1 Claude
        self.update_state(state="PROGRESS", meta={"stage": "generating_code", "job_id": job_id})
        slots = generate_ols_slots(prompt, column_names)
        dep_var = slots["dep_var"]
        indep_vars = slots["indep_vars"]
        transformations = slots["transformations"]

        # Step 6: Render R script
        r_script = render_ols_script(dep_var, indep_vars, transformations, "/data/data.csv")

        # Step 7: Write CSV + R script, run Docker
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "data.csv")
            df.to_csv(csv_path, index=True, index_label="date")
            script_path = os.path.join(tmpdir, "analysis.R")
            with open(script_path, "w") as f:
                f.write(r_script)

            self.update_state(state="PROGRESS", meta={"stage": "running_r", "job_id": job_id})

            try:
                _current_proc = subprocess.Popen(
                    [
                        "docker",
                        "run",
                        "--rm",
                        "--network",
                        "none",
                        "--memory",
                        "512m",
                        "--cpus",
                        "1.0",
                        "--read-only",
                        "--tmpfs",
                        "/tmp:size=64m",
                        "--user",
                        "1000",
                        "-v",
                        f"{script_path}:/analysis.R:ro",
                        "-v",
                        f"{csv_path}:/data/data.csv:ro",
                        "stats-ai-r-sandbox",
                        "Rscript",
                        "/analysis.R",
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                stdout, stderr = _current_proc.communicate(timeout=60)
                returncode = _current_proc.returncode
            except subprocess.TimeoutExpired:
                _current_proc.kill()
                _current_proc.communicate()
                _current_proc = None
                raise RuntimeError("R script execution timed out after 60 seconds")
            finally:
                _current_proc = None

        # Step 8: On R success
        if returncode == 0:
            r_result = json.loads(stdout.decode("utf-8"))

            # Process plotly_charts: parse inner JSON string for each chart
            if "plotly_charts" in r_result:
                processed_charts = []
                for chart in r_result["plotly_charts"]:
                    parsed = json.loads(chart["json"])
                    processed_charts.append({
                        "name": chart["name"],
                        "data": parsed.get("data", []),
                        "layout": parsed.get("layout", {}),
                    })
                r_result["plotly_charts"] = processed_charts

            self.update_state(state="PROGRESS", meta={"stage": "generating_interpretation", "job_id": job_id})
            interp = interpret_ols_results(prompt, r_result)

            with Session(engine) as session:
                job = session.get(Job, uuid.UUID(job_id))
                job.status = "success"
                job.stage = "done"
                job.r_script = r_script
                job.r_result_json = json.dumps(r_result)
                job.result_stdout = stdout.decode("utf-8", errors="replace")
                job.interpretation = interp["interpretation"]
                job.follow_up_suggestions = json.dumps(interp["follow_up_suggestions"])
                session.commit()

            return {"status": "success", "job_id": job_id}

        # Step 9: On R error
        else:
            stderr_text = stderr.decode("utf-8", errors="replace")
            self.update_state(state="PROGRESS", meta={"stage": "generating_interpretation", "job_id": job_id})
            err = explain_r_error(prompt, stderr_text)

            with Session(engine) as session:
                job = session.get(Job, uuid.UUID(job_id))
                job.status = "error"
                job.stage = "done"
                job.r_script = r_script
                job.result_stderr = stderr_text
                job.error_explanation = err["error_explanation"]
                job.suggested_prompt = err["suggested_prompt"]
                session.commit()

            return {"status": "error", "job_id": job_id}

    except Exception as exc:
        # Unexpected exception: store error on Job and re-raise for Celery
        try:
            with Session(engine) as session:
                job = session.get(Job, uuid.UUID(job_id))
                if job:
                    job.status = "error"
                    job.stage = "done"
                    job.error_message = str(exc)
                    session.commit()
        except Exception:
            pass  # Don't mask the original exception
        raise
