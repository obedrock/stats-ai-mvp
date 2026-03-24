import pytest


@pytest.mark.skip(reason="Wave 0 stub — implementation in Plan 01")
def test_ols_template_produces_valid_json():
    """R template with filled slots produces JSON with coefficients, diagnostics, model_summary, plotly_charts keys."""
    pass


@pytest.mark.skip(reason="Wave 0 stub — implementation in Plan 01")
def test_ols_template_diagnostics_section():
    """R template JSON contains breusch_pagan, durbin_watson, vif, shapiro_wilk in diagnostics."""
    pass


@pytest.mark.skip(reason="Wave 0 stub — implementation in Plan 01")
def test_pydantic_schemas_validate_r_output():
    """AnalysisResultResponse schema accepts the R template's JSON structure."""
    pass


@pytest.mark.skip(reason="Wave 0 stub — implementation in Plan 01")
def test_typescript_types_match_pydantic_fields():
    """TypeScript type field names match Pydantic schema field names (checked via regex on both files)."""
    pass
