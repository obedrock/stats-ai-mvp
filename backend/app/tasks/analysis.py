import os
import signal
import subprocess
import sys
import tempfile

from celery import current_task  # noqa: F401

from .celery_app import celery_app

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
