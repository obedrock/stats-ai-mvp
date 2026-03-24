import pytest


@pytest.mark.skip(reason="Wave 0 stub — implementation in Plan 02/03")
def test_interpretation_contains_coefficient_references():
    """Interpretation text references specific coefficient values and p-values."""
    pass


@pytest.mark.skip(reason="Wave 0 stub — implementation in Plan 02/03")
def test_coefficient_table_has_all_fields():
    """Coefficient rows contain variable, estimate, std_error, t_stat, p_value, ci_lower, ci_upper."""
    pass


@pytest.mark.skip(reason="Wave 0 stub — implementation in Plan 02/03")
def test_diagnostics_bundle_complete():
    """Diagnostics contain breusch_pagan, durbin_watson, vif, shapiro_wilk results."""
    pass


@pytest.mark.skip(reason="Wave 0 stub — implementation in Plan 02/03")
def test_follow_up_suggestions_are_context_aware():
    """Follow-up suggestions reference diagnostic failures from the results."""
    pass
