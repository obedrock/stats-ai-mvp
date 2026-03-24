import pytest


@pytest.mark.skip(reason="Wave 0 stub — implementation in Plan 03")
def test_run_ols_analysis_task_success_path():
    """run_ols_analysis task completes and updates Job with status=success, r_result_json, interpretation."""
    pass


@pytest.mark.skip(reason="Wave 0 stub — implementation in Plan 03")
def test_run_ols_analysis_task_error_path():
    """run_ols_analysis task handles R failure, updates Job with status=error, error_explanation."""
    pass


@pytest.mark.skip(reason="Wave 0 stub — implementation in Plan 03")
def test_analysis_run_endpoint_starts_celery_task():
    """POST /analysis/run returns 200 with job_id and status=running."""
    pass


@pytest.mark.skip(reason="Wave 0 stub — implementation in Plan 03")
def test_analysis_poll_endpoint_returns_results():
    """GET /analysis/{job_id} returns full AnalysisResultResponse when job is complete."""
    pass
