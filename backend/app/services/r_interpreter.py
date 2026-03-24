"""Stage 2 Claude services: R results -> interpretation and R error -> explanation.

Two pure functions callable from the Celery task:
  - interpret_ols_results: turns R JSON output into plain-English interpretation
    plus 2-3 context-aware follow-up suggestions.
  - explain_r_error: turns R stderr into a plain-English error explanation
    plus a suggested modified prompt the user can resubmit.

Both use Claude tool_use for guaranteed structured output — no free-form text
parsing.
"""
import json

from app.services.series_mapper import get_client

# ---------------------------------------------------------------------------
# Tool schemas
# ---------------------------------------------------------------------------

INTERPRET_TOOL = {
    "name": "interpret_ols_results",
    "description": "Produce a plain-English interpretation of OLS regression results and suggest follow-up analyses.",
    "input_schema": {
        "type": "object",
        "properties": {
            "interpretation": {
                "type": "string",
                "description": (
                    "2-4 paragraph plain-English interpretation of the OLS results. "
                    "Reference specific coefficients, p-values, and diagnostic test outcomes."
                ),
            },
            "follow_up_suggestions": {
                "type": "array",
                "maxItems": 3,
                "minItems": 2,
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Short title (3-6 words)",
                        },
                        "explanation": {
                            "type": "string",
                            "description": "One sentence explaining why this follow-up is useful",
                        },
                        "prompt_text": {
                            "type": "string",
                            "description": "Complete analysis prompt the user can submit directly",
                        },
                    },
                    "required": ["title", "explanation", "prompt_text"],
                },
            },
        },
        "required": ["interpretation", "follow_up_suggestions"],
    },
}

ERROR_INTERPRET_TOOL = {
    "name": "explain_r_error",
    "description": "Translate an R error into a plain-English explanation and suggest a fix.",
    "input_schema": {
        "type": "object",
        "properties": {
            "error_explanation": {
                "type": "string",
                "description": "1-2 sentence plain-English explanation of what went wrong",
            },
            "suggested_prompt": {
                "type": "string",
                "description": "A complete, modified analysis prompt that would avoid the error",
            },
        },
        "required": ["error_explanation", "suggested_prompt"],
    },
}

# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

_INTERPRET_SYSTEM = (
    "You are a statistical analyst explaining OLS regression results to an economist. "
    "Be precise, reference specific coefficient values and p-values. "
    "Write 2-4 paragraphs of plain-English interpretation.\n\n"
    "For follow-up suggestions, reference diagnostic failures directly:\n"
    "- If Breusch-Pagan p < 0.05, suggest using robust standard errors or transforming variables\n"
    "- If Durbin-Watson statistic < 1.5 or > 2.5, suggest adding lag terms or checking for omitted variables\n"
    "- If any VIF > 10, suggest removing highly correlated predictors\n"
    "- If Shapiro-Wilk p < 0.05, suggest log transformation of the dependent variable\n\n"
    "Always suggest 2-3 follow-up analyses. Each suggestion must include a complete, "
    "ready-to-submit prompt the user can run."
)

_ERROR_SYSTEM = (
    "You are helping a user understand why their statistical analysis failed. "
    "Given the R error output and the user's original prompt, explain in plain English "
    "what went wrong and suggest a modified prompt that would fix the issue. "
    "The explanation should be 1-2 sentences. "
    "The suggested prompt should be a complete, ready-to-submit analysis request."
)

# ---------------------------------------------------------------------------
# Stage 2: interpretation
# ---------------------------------------------------------------------------


def interpret_ols_results(prompt: str, r_result: dict) -> dict:
    """Interpret successful OLS results and produce follow-up suggestions.

    Calls Claude Stage 2 with the original user prompt and the full R JSON
    output. Returns a structured dict with a plain-English interpretation and
    2-3 context-aware follow-up analysis suggestions.

    Args:
        prompt: The original natural language analysis request.
        r_result: The parsed JSON output from the OLS R script. Typically
            contains ``coefficients``, ``model_summary``, ``diagnostics``,
            and ``plotly_charts`` keys.

    Returns:
        Dict with keys:
            - interpretation (str): 2-4 paragraph plain-English explanation.
            - follow_up_suggestions (list[dict]): 2-3 dicts, each with keys
              ``title``, ``explanation``, and ``prompt_text``.

    Raises:
        ValueError: If the Claude API call fails or returns unexpected content.
    """
    user_content = f"Original request: {prompt}\n\nResults:\n{json.dumps(r_result, indent=2)}"

    try:
        client = get_client()
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            temperature=0.3,
            system=_INTERPRET_SYSTEM,
            tools=[INTERPRET_TOOL],
            tool_choice={"type": "tool", "name": "interpret_ols_results"},
            messages=[{"role": "user", "content": user_content}],
        )
        tool_use = next(b for b in response.content if b.type == "tool_use")
        return {
            "interpretation": tool_use.input["interpretation"],
            "follow_up_suggestions": tool_use.input["follow_up_suggestions"],
        }
    except StopIteration:
        raise ValueError("Claude response did not contain a tool_use block.")
    except Exception as exc:
        raise ValueError(f"Failed to interpret OLS results: {exc}") from exc


# ---------------------------------------------------------------------------
# Stage 2: error explanation
# ---------------------------------------------------------------------------


def explain_r_error(prompt: str, r_stderr: str) -> dict:
    """Translate an R error into a plain-English explanation and a suggested fix.

    Called when the R subprocess returns a non-zero exit code. The R stderr
    text is passed alongside the original prompt so Claude can identify what
    went wrong and suggest a corrected analysis request.

    Args:
        prompt: The original natural language analysis request.
        r_stderr: The captured stderr output from the failed R subprocess run.

    Returns:
        Dict with keys:
            - error_explanation (str): 1-2 sentence plain-English explanation.
            - suggested_prompt (str): A complete, ready-to-submit analysis
              prompt that avoids the error.

    Raises:
        ValueError: If the Claude API call fails or returns unexpected content.
    """
    user_content = f"Original request: {prompt}\n\nR error output:\n{r_stderr}"

    try:
        client = get_client()
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=512,
            temperature=0.3,
            system=_ERROR_SYSTEM,
            tools=[ERROR_INTERPRET_TOOL],
            tool_choice={"type": "tool", "name": "explain_r_error"},
            messages=[{"role": "user", "content": user_content}],
        )
        tool_use = next(b for b in response.content if b.type == "tool_use")
        return {
            "error_explanation": tool_use.input["error_explanation"],
            "suggested_prompt": tool_use.input["suggested_prompt"],
        }
    except StopIteration:
        raise ValueError("Claude response did not contain a tool_use block.")
    except Exception as exc:
        raise ValueError(f"Failed to explain R error: {exc}") from exc
