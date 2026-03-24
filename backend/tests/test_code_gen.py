"""Tests for r_code_gen.py — Stage 1 Claude service for OLS slot generation."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services import r_code_gen


def _make_tool_use_response(dep_var: str, indep_vars: list, transformations: str = "") -> MagicMock:
    """Build a mock Anthropic response with a tool_use content block."""
    tool_use_block = MagicMock()
    tool_use_block.type = "tool_use"
    tool_use_block.input = {
        "dep_var": dep_var,
        "indep_vars": indep_vars,
        "transformations": transformations,
    }

    response = MagicMock()
    response.content = [tool_use_block]
    return response


def test_generate_ols_slots_returns_required_keys():
    """generate_ols_slots returns dict with dep_var, indep_vars, transformations."""
    mock_response = _make_tool_use_response(
        dep_var="gdp_growth",
        indep_vars=["interest_rate", "inflation"],
    )

    with patch("app.services.r_code_gen.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = r_code_gen.generate_ols_slots(
            prompt="Regress GDP growth on interest rates and inflation",
            column_names=["gdp_growth", "interest_rate", "inflation"],
        )

    assert isinstance(result, dict)
    assert result["dep_var"] == "gdp_growth"
    assert result["indep_vars"] == ["interest_rate", "inflation"]
    assert result["transformations"] == ""


def test_generate_ols_slots_uses_tool_use():
    """generate_ols_slots calls Claude with tool_choice type=tool."""
    mock_response = _make_tool_use_response("gdp", ["cpi"])

    with patch("app.services.r_code_gen.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        r_code_gen.generate_ols_slots(
            prompt="Regress GDP on CPI",
            column_names=["gdp", "cpi"],
        )

        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["tool_choice"] == {"type": "tool", "name": "generate_ols_slots"}
        assert call_kwargs["temperature"] == 0
        assert "Available columns (exact case, from cleaned data)" in call_kwargs["system"]
        assert "gdp" in call_kwargs["system"]
        assert "cpi" in call_kwargs["system"]


def test_render_ols_script_fills_all_slots():
    """render_ols_script replaces all 4 template slots: DATA_PATH, DEP_VAR, INDEP_VARS, TRANSFORMATIONS."""
    script = r_code_gen.render_ols_script(
        dep_var="gdp_growth",
        indep_vars=["interest_rate", "inflation"],
        transformations="data$log_gdp <- log(data$gdp_growth)",
        data_path="/data/data.csv",
    )

    assert "{{DATA_PATH}}" not in script
    assert "{{DEP_VAR}}" not in script
    assert "{{INDEP_VARS}}" not in script
    assert "{{TRANSFORMATIONS}}" not in script

    assert "/data/data.csv" in script
    assert "gdp_growth" in script
    assert "interest_rate + inflation" in script
    assert "data$log_gdp <- log(data$gdp_growth)" in script


def test_generate_ols_slots_raises_on_no_tool_use():
    """generate_ols_slots raises ValueError when Claude returns no tool_use block."""
    response = MagicMock()
    response.content = []  # no tool_use block

    with patch("app.services.r_code_gen.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = response
        mock_get_client.return_value = mock_client

        with pytest.raises(ValueError, match="tool_use block"):
            r_code_gen.generate_ols_slots("Regress y on x", ["y", "x"])


def test_render_ols_script_empty_transformations():
    """render_ols_script works with empty transformations string."""
    script = r_code_gen.render_ols_script(
        dep_var="y",
        indep_vars=["x1", "x2"],
        transformations="",
        data_path="/data/data.csv",
    )

    assert "{{TRANSFORMATIONS}}" not in script
    assert "x1 + x2" in script


def test_render_ols_script_single_indep_var():
    """render_ols_script handles a single independent variable correctly."""
    script = r_code_gen.render_ols_script(
        dep_var="gdp",
        indep_vars=["interest_rate"],
        transformations="",
        data_path="/data/data.csv",
    )

    assert "gdp ~ interest_rate" in script


def test_render_ols_script_template_exists():
    """The OLS template file exists at the expected path."""
    template_path = (
        Path(__file__).parent.parent / "app" / "templates" / "ols_template.R"
    )
    assert template_path.exists(), f"Template not found at {template_path}"


# Note: Stage 2 tests (interpret_ols_results, explain_r_error) are in test_interpretation.py
