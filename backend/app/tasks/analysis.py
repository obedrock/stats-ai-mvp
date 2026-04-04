import io
import json
import logging
import os
import shutil
import tempfile
import uuid

import docker
import pandas as pd
import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from .celery_app import celery_app
from app.models.job import Job
from app.services.data_pipeline import clean_and_merge
from app.services.r_code_gen import generate_ols_slots, render_ols_script
from app.services.r_interpreter import explain_r_error, interpret_ols_results

logger = logging.getLogger(__name__)

R_SANDBOX_IMAGE = "stats-ai-r-sandbox"


def _run_r_container(volumes: dict, timeout: int = 60) -> tuple[int, str, str]:
    """Run R script in a sandboxed Docker container via the Docker SDK.

    Args:
        volumes: Dict mapping host paths to container mount specs,
                 e.g. {"/tmp/job-x/analysis.R": {"bind": "/analysis.R", "mode": "ro"}}
        timeout: Max seconds to wait for container to finish.

    Returns:
        (exit_code, stdout, stderr) tuple.
    """
    client = docker.from_env()

    # Debug: verify files exist before mounting
    for host_path, mount in volumes.items():
        exists = os.path.isfile(host_path)
        size = os.path.getsize(host_path) if exists else -1
        logger.info("[_run_r_container] mount %s -> %s exists=%s size=%d", host_path, mount["bind"], exists, size)

    # Debug: test mount with a quick ls command
    test = client.containers.run(
        R_SANDBOX_IMAGE,
        command=["ls", "-la", "/data/", "/analysis.R"],
        volumes=volumes,
        network_mode="none",
        read_only=True,
        tmpfs={"/tmp": "size=64m"},
        user="1000",
        remove=True,
    )
    logger.info("[_run_r_container] mount test: %s", test.decode("utf-8", errors="replace"))

    container = client.containers.run(
        R_SANDBOX_IMAGE,
        command=["Rscript", "/analysis.R"],
        volumes=volumes,
        network_mode="none",
        mem_limit="512m",
        nano_cpus=1_000_000_000,  # 1.0 CPU
        read_only=True,
        tmpfs={"/tmp": "size=64m"},
        user="1000",
        detach=True,
    )
    try:
        result = container.wait(timeout=timeout)
        exit_code = result.get("StatusCode", -1)
        stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
        stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")
    except Exception:
        container.kill()
        raise RuntimeError("R script execution timed out or failed")
    finally:
        container.remove(force=True)

    return exit_code, stdout, stderr


@celery_app.task(bind=True, name="run_r_analysis")
def run_r_analysis(self, r_script: str, job_id: str):
    self.update_state(state="PROGRESS", meta={"stage": "queued", "job_id": job_id})

    sandbox_base = os.environ.get("R_SANDBOX_TMPDIR", tempfile.gettempdir())
    tmpdir = os.path.join(sandbox_base, f"job-{job_id}")
    os.makedirs(tmpdir, exist_ok=True)
    try:
        script_path = os.path.join(tmpdir, "analysis.R")
        with open(script_path, "w") as f:
            f.write(r_script)

        self.update_state(state="PROGRESS", meta={"stage": "running_r", "job_id": job_id})

        exit_code, stdout, stderr = _run_r_container(
            volumes={script_path: {"bind": "/analysis.R", "mode": "ro"}},
        )

        return {
            "status": "success" if exit_code == 0 else "error",
            "stdout": stdout,
            "stderr": stderr,
            "job_id": job_id,
        }
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


@celery_app.task(bind=True, name="run_ols_analysis")
def run_ols_analysis(self, job_id: str, prompt: str):
    """Full OLS analysis pipeline: data reconstruction -> Claude Stage 1 -> R Docker -> Claude Stage 2 -> Job update."""

    self.update_state(state="PROGRESS", meta={"stage": "preparing", "job_id": job_id})

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
            resolution_method = job.resolution_method  # e.g. "mean", or None

        # Step 3: Reconstruct DataFrame from Redis cache
        redis_client = redis.from_url(settings.redis_url)

        dataframes: dict[str, pd.DataFrame] = {}
        for cache_key in cached_data_keys:
            raw = redis_client.get(cache_key)
            if raw is None:
                raise ValueError(f"Cache key {cache_key!r} not found in Redis — data may have expired")
            df = pd.read_json(io.StringIO(raw.decode("utf-8")))
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index, unit="ms", utc=True)
            elif df.index.tz is None:
                df.index = df.index.tz_localize("UTC")
            series_id = cache_key.split(":")[1]
            # Rename generic "value" column to series_id so merged DataFrame
            # has meaningful column names (GDPC1, DFF, etc.) for R formulas
            df = df.rename(columns={"value": series_id})
            dataframes[series_id] = df

        # Step 3b: Re-apply frequency resolution if the user chose one.
        # Redis cache stores raw un-resolved data; the resolution was only
        # applied in-memory during the fetch_data task.
        if resolution_method and len(dataframes) > 1:
            from app.services.frequency_resolver import check_frequency_conflict, apply_resolution
            conflict = check_frequency_conflict(dataframes)
            if conflict["has_conflict"]:
                target_freq = conflict["target_frequency"]
                logger.info(
                    "[run_ols_analysis] job=%s applying frequency resolution: method=%s target=%s",
                    job_id, resolution_method, target_freq,
                )
                for sid, dframe in list(dataframes.items()):
                    dataframes[sid] = apply_resolution(dframe, target_freq, resolution_method)

        result = clean_and_merge(dataframes)
        df = result["merged_df"]

        # Step 4: Get column names
        column_names = list(df.columns)
        logger.info("[run_ols_analysis] job=%s columns=%s shape=%s", job_id, column_names, df.shape)

        # Step 5: Call Stage 1 Claude
        self.update_state(state="PROGRESS", meta={"stage": "generating_code", "job_id": job_id})
        slots = generate_ols_slots(prompt, column_names)
        dep_var = slots["dep_var"]
        indep_vars = slots["indep_vars"]
        transformations = slots["transformations"]
        logger.info(
            "[run_ols_analysis] job=%s dep_var=%s indep_vars=%s transformations=%r",
            job_id, dep_var, indep_vars, transformations,
        )

        # Step 6: Render R script
        r_script = render_ols_script(dep_var, indep_vars, transformations)

        # Step 7: Write CSV + R script, run in Docker container
        sandbox_base = os.environ.get("R_SANDBOX_TMPDIR", tempfile.gettempdir())
        tmpdir = os.path.join(sandbox_base, f"job-{job_id}")
        os.makedirs(tmpdir, exist_ok=True)
        try:
            csv_path = os.path.join(tmpdir, "data.csv")
            df.to_csv(csv_path, index=True, index_label="date")
            script_path = os.path.join(tmpdir, "analysis.R")
            with open(script_path, "w") as f:
                f.write(r_script)

            # DEBUG: log CSV contents (first 3 lines)
            with open(csv_path) as f:
                csv_lines = [f.readline() for _ in range(3)]
            logger.info(
                "[run_ols_analysis] job=%s columns=%s shape=%s csv_lines=%s",
                job_id, column_names, df.shape, csv_lines,
            )

            # DEBUG: log full R script
            logger.info(
                "[run_ols_analysis] job=%s R_SCRIPT_START\n%s\nR_SCRIPT_END",
                job_id, r_script,
            )

            # DEBUG: log volume mounts
            volumes = {
                script_path: {"bind": "/analysis.R", "mode": "ro"},
                csv_path: {"bind": "/data/data.csv", "mode": "ro"},
            }
            logger.info(
                "[run_ols_analysis] job=%s volumes=%s",
                job_id, volumes,
            )

            self.update_state(state="PROGRESS", meta={"stage": "running_r", "job_id": job_id})

            exit_code, stdout, stderr = _run_r_container(volumes=volumes)
            logger.info(
                "[run_ols_analysis] job=%s exit_code=%d stdout_len=%d stderr=\n%s",
                job_id, exit_code, len(stdout), stderr[:3000],
            )

            # Step 8: On R success
            if exit_code == 0:
                r_result = json.loads(stdout)

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
                    job.result_stdout = stdout
                    job.interpretation = interp["interpretation"]
                    job.follow_up_suggestions = json.dumps(interp["follow_up_suggestions"])
                    session.commit()

                return {"status": "success", "job_id": job_id}

            # Step 9: On R error
            else:
                self.update_state(state="PROGRESS", meta={"stage": "generating_interpretation", "job_id": job_id})
                err = explain_r_error(prompt, stderr)

                with Session(engine) as session:
                    job = session.get(Job, uuid.UUID(job_id))
                    job.status = "error"
                    job.stage = "done"
                    job.r_script = r_script
                    job.result_stderr = stderr
                    job.error_explanation = err["error_explanation"]
                    job.suggested_prompt = err["suggested_prompt"]
                    session.commit()

                return {"status": "error", "job_id": job_id}
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    except Exception as exc:
        try:
            with Session(engine) as session:
                job = session.get(Job, uuid.UUID(job_id))
                if job:
                    job.status = "error"
                    job.stage = "done"
                    job.error_message = str(exc)
                    session.commit()
        except Exception:
            pass
        raise
