import pytest


@pytest.mark.skip(reason="Wave 0 stub — implementation in Plan 02")
def test_generate_ols_slots_returns_required_keys():
    """generate_ols_slots returns dict with dep_var, indep_vars, transformations."""
    pass


@pytest.mark.skip(reason="Wave 0 stub — implementation in Plan 02")
def test_generate_ols_slots_uses_tool_use():
    """generate_ols_slots calls Claude with tool_choice type=tool."""
    pass


@pytest.mark.skip(reason="Wave 0 stub — implementation in Plan 02")
def test_render_ols_script_fills_all_slots():
    """render_ols_script replaces all 4 template slots: DATA_PATH, DEP_VAR, INDEP_VARS, TRANSFORMATIONS."""
    pass


@pytest.mark.skip(reason="Wave 0 stub — implementation in Plan 02")
def test_interpret_ols_results_returns_interpretation_and_suggestions():
    """interpret_ols_results returns dict with interpretation and follow_up_suggestions."""
    pass


@pytest.mark.skip(reason="Wave 0 stub — implementation in Plan 02")
def test_explain_r_error_returns_explanation_and_prompt():
    """explain_r_error returns dict with error_explanation and suggested_prompt."""
    pass
