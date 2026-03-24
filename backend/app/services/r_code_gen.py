"""Stage 1 Claude service: prompt + column names -> OLS slot values + R script.

Uses Claude tool_use to extract structured OLS model specification from a
natural language prompt given a list of available column names. Also renders
the filled OLS R script from a template.
"""
from pathlib import Path

from app.services.series_mapper import get_client

# ---------------------------------------------------------------------------
# Tool schema
# ---------------------------------------------------------------------------

CODE_GEN_TOOL = {
    "name": "generate_ols_slots",
    "description": "Extract OLS model specification from a natural language prompt given known column names.",
    "input_schema": {
        "type": "object",
        "properties": {
            "dep_var": {
                "type": "string",
                "description": "Column name of the dependent variable from the provided column list.",
            },
            "indep_vars": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Column names of independent variables from the provided column list.",
            },
            "transformations": {
                "type": "string",
                "description": "R code block for any transformations (log, lag, pct_change). Empty string if none.",
            },
        },
        "required": ["dep_var", "indep_vars", "transformations"],
    },
}

# ---------------------------------------------------------------------------
# Stage 1: slot generation
# ---------------------------------------------------------------------------

def generate_ols_slots(prompt: str, column_names: list[str]) -> dict:
    """Extract OLS model specification from a natural language prompt.

    Uses Claude tool_use with a forced tool call to guarantee structured output.
    The system prompt includes the exact column names available in the cleaned
    dataset so Claude never hallucinates column names that do not exist.

    Args:
        prompt: Natural language analysis request from the user.
        column_names: Exact column names present in the cleaned/merged dataset
            (case-sensitive). The ``date`` index column should be excluded.

    Returns:
        Dict with keys:
            - dep_var (str): dependent variable column name.
            - indep_vars (list[str]): independent variable column names.
            - transformations (str): R code block or empty string.

    Raises:
        ValueError: If the Claude API call fails or returns unexpected content.
    """
    columns_str = ", ".join(column_names)
    system_prompt = (
        f"You are an econometrician configuring an OLS regression. "
        f"Available columns (exact case, from cleaned data): {columns_str}. "
        "Identify the dependent variable, independent variables, and any required "
        "transformations (log, lag, percent change). Only use column names from the "
        "list above. If the user's prompt implies a transformation not directly "
        "available as a column, write the R code for it in the transformations field. "
        "If no transformations are needed, return an empty string for transformations."
    )

    try:
        client = get_client()
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=512,
            temperature=0,
            system=system_prompt,
            tools=[CODE_GEN_TOOL],
            tool_choice={"type": "tool", "name": "generate_ols_slots"},
            messages=[{"role": "user", "content": prompt}],
        )
        tool_use = next(b for b in response.content if b.type == "tool_use")
        return {
            "dep_var": tool_use.input["dep_var"],
            "indep_vars": tool_use.input["indep_vars"],
            "transformations": tool_use.input["transformations"],
        }
    except StopIteration:
        raise ValueError("Claude response did not contain a tool_use block.")
    except Exception as exc:
        raise ValueError(f"Failed to generate OLS slots: {exc}") from exc


# ---------------------------------------------------------------------------
# Stage 1: R script rendering
# ---------------------------------------------------------------------------

def render_ols_script(
    dep_var: str,
    indep_vars: list[str],
    transformations: str,
) -> str:
    """Render the OLS R script by filling the template slots.

    Reads ``backend/app/templates/ols_template.R`` and replaces the three
    placeholder tokens with the values produced by :func:`generate_ols_slots`.
    The data path is hardcoded to ``/data/data.csv`` in the template (mounted
    into the Docker container by the Celery task).

    Args:
        dep_var: Dependent variable column name.
        indep_vars: Independent variable column names.
        transformations: R code block for variable transformations, or empty string.

    Returns:
        The filled R script as a string, ready to write to a temp file and
        pass to ``Rscript``.
    """
    template_path = Path(__file__).parent.parent / "templates" / "ols_template.R"
    template = template_path.read_text(encoding="utf-8")

    indep_vars_str = " + ".join(indep_vars)

    script = template.replace("{{DEP_VAR}}", dep_var)
    script = script.replace("{{INDEP_VARS}}", indep_vars_str)
    script = script.replace("{{TRANSFORMATIONS}}", transformations)

    return script
