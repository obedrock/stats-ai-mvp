"""Claude tool-use for prompt → series ID mapping.

Uses Claude's tool_use feature to extract structured data source information
from a natural language analysis request.
"""
import os

import anthropic

_client = None

DETECT_TOOL = {
    "name": "detect_data_sources",
    "description": "Extract all data series needed to answer the user's statistical analysis request.",
    "input_schema": {
        "type": "object",
        "properties": {
            "sources": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "source": {"type": "string", "enum": ["FRED", "YAHOO"]},
                        "series_id": {"type": "string"},
                        "display_name": {"type": "string"},
                        "rationale": {"type": "string"},
                    },
                    "required": ["source", "series_id", "display_name", "rationale"],
                },
            }
        },
        "required": ["sources"],
    },
}

SYSTEM_PROMPT = (
    "You are a statistical data source expert. Given a natural language analysis request, "
    "identify the specific data series needed. For macroeconomic data (GDP, CPI, unemployment, "
    "interest rates, etc.), use FRED as the source. For stock prices, ETFs, and market indices, "
    "use YAHOO as the source. Always return the most commonly used series ID "
    "(e.g., GDPC1 for real GDP, CPIAUCSL for CPI, DFF for fed funds rate, UNRATE for unemployment)."
)


def get_client() -> anthropic.Anthropic:
    """Lazily initialize and return the Anthropic client."""
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    return _client


def map_prompt_to_sources(prompt: str) -> list[dict]:
    """Map a natural language prompt to a list of data source descriptors.

    Uses Claude tool-use to extract structured source + series_id pairs.

    Args:
        prompt: Natural language analysis request from the user.

    Returns:
        List of dicts with keys: source, series_id, display_name, rationale.

    Raises:
        ValueError: If the Claude API call fails or returns unexpected content.
    """
    try:
        response = get_client().messages.create(
            model="claude-sonnet-4-5",
            max_tokens=512,
            temperature=0,
            system=SYSTEM_PROMPT,
            tools=[DETECT_TOOL],
            tool_choice={"type": "tool", "name": "detect_data_sources"},
            messages=[{"role": "user", "content": prompt}],
        )
        tool_use = next(b for b in response.content if b.type == "tool_use")
        return tool_use.input["sources"]
    except StopIteration:
        raise ValueError("Claude response did not contain a tool_use block.")
    except Exception as exc:
        raise ValueError(f"Failed to map prompt to data sources: {exc}") from exc
