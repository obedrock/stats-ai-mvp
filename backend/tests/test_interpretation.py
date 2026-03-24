"""Tests for r_interpreter.py -- Stage 2 Claude services for results interpretation."""
from unittest.mock import MagicMock, patch

import pytest

from app.services import r_interpreter


def _make_interpret_response(interpretation, suggestions):
    tool_use_block = MagicMock()
    tool_use_block.type = "tool_use"
    tool_use_block.input = {"interpretation": interpretation, "follow_up_suggestions": suggestions}
    response = MagicMock()
    response.content = [tool_use_block]
    return response


def _make_error_response(explanation, suggested_prompt):
    tool_use_block = MagicMock()
    tool_use_block.type = "tool_use"
    tool_use_block.input = {"error_explanation": explanation, "suggested_prompt": suggested_prompt}
    response = MagicMock()
    response.content = [tool_use_block]
    return response


def test_interpretation_contains_coefficient_references():
    suggestions = [
        {"title": "Add lag", "explanation": "Check autocorrelation.", "prompt_text": "Redo with lags"},
        {"title": "Log transform", "explanation": "Reduce skew.", "prompt_text": "Redo with log"},
    ]
    mock_response = _make_interpret_response("A one-unit increase (p=0.002).", suggestions)
    with patch("app.services.r_interpreter.get_client") as mock_get:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_get.return_value = mock_client
        result = r_interpreter.interpret_ols_results("Regress GDP on rates", {"r_squared": 0.75})
    assert "interpretation" in result
    assert len(result["interpretation"]) > 0


def test_coefficient_table_has_all_fields():
    suggestions = [
        {"title": "Robust SEs", "explanation": "Heteroskedasticity.", "prompt_text": "Redo robust"},
        {"title": "VIF check", "explanation": "Multicollinearity.", "prompt_text": "Check VIF"},
    ]
    mock_response = _make_interpret_response("Good fit.", suggestions)
    r_result = {"coefficients": [{"variable": "interest_rate", "estimate": 0.45}], "r_squared": 0.75}
    with patch("app.services.r_interpreter.get_client") as mock_get:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_get.return_value = mock_client
        r_interpreter.interpret_ols_results("Regress GDP", r_result)
        call_kwargs = mock_client.messages.create.call_args.kwargs
        user_message = call_kwargs["messages"][0]["content"]
        assert "interest_rate" in user_message
        assert "r_squared" in user_message


def test_diagnostics_bundle_complete():
    suggestions = [
        {"title": "Add lag", "explanation": "Fix autocorrelation.", "prompt_text": "Redo lags"},
        {"title": "Log GDP", "explanation": "Normalize.", "prompt_text": "Redo log GDP"},
    ]
    mock_response = _make_interpret_response("Good fit.", suggestions)
    with patch("app.services.r_interpreter.get_client") as mock_get:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_get.return_value = mock_client
        r_interpreter.interpret_ols_results("Regress y on x", {"r_squared": 0.5})
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["tool_choice"] == {"type": "tool", "name": "interpret_ols_results"}
        assert call_kwargs["temperature"] == 0.3


def test_follow_up_suggestions_are_context_aware():
    suggestions = [
        {"title": "Robust SEs", "explanation": "BP significant.", "prompt_text": "Redo robust"},
        {"title": "Add lag y", "explanation": "DW < 1.5.", "prompt_text": "Add lag"},
        {"title": "Drop X2", "explanation": "VIF > 10.", "prompt_text": "Drop X2"},
    ]
    mock_response = _make_interpret_response("Strong fit.", suggestions)
    with patch("app.services.r_interpreter.get_client") as mock_get:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_get.return_value = mock_client
        result = r_interpreter.interpret_ols_results("Regress GDP on inflation", {"r_squared": 0.8})
    assert 2 <= len(result["follow_up_suggestions"]) <= 3
    for s in result["follow_up_suggestions"]:
        assert "title" in s and "explanation" in s and "prompt_text" in s


def test_interpret_ols_results_raises_on_no_tool_use():
    response = MagicMock()
    response.content = []
    with patch("app.services.r_interpreter.get_client") as mock_get:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = response
        mock_get.return_value = mock_client
        with pytest.raises(ValueError, match="tool_use block"):
            r_interpreter.interpret_ols_results("Regress y on x", {})


def test_explain_r_error_returns_explanation_and_prompt():
    mock_response = _make_error_response("Column not found.", "Regress GDPC1 on DFF")
    with patch("app.services.r_interpreter.get_client") as mock_get:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_get.return_value = mock_client
        result = r_interpreter.explain_r_error("Regress GDP on rates", "Error: object gdp not found")
    assert "error_explanation" in result and "suggested_prompt" in result


def test_explain_r_error_uses_correct_tool_name():
    mock_response = _make_error_response("Column not found.", "Redo")
    with patch("app.services.r_interpreter.get_client") as mock_get:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_get.return_value = mock_client
        r_interpreter.explain_r_error("Regress y on x", "Error: x not found")
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["tool_choice"] == {"type": "tool", "name": "explain_r_error"}
        assert call_kwargs["temperature"] == 0.3


def test_explain_r_error_includes_stderr_in_user_message():
    mock_response = _make_error_response("Parsing error.", "Fix column")
    with patch("app.services.r_interpreter.get_client") as mock_get:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_get.return_value = mock_client
        r_interpreter.explain_r_error("Regress GDP on CPI", "Error in lm.fit: 0 (non-NA) cases")
        call_kwargs = mock_client.messages.create.call_args.kwargs
        user_message = call_kwargs["messages"][0]["content"]
        assert "0 (non-NA) cases" in user_message
        assert "Regress GDP on CPI" in user_message


def test_explain_r_error_raises_on_no_tool_use():
    response = MagicMock()
    response.content = []
    with patch("app.services.r_interpreter.get_client") as mock_get:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = response
        mock_get.return_value = mock_client
        with pytest.raises(ValueError, match="tool_use block"):
            r_interpreter.explain_r_error("Regress y on x", "Error: something failed")
