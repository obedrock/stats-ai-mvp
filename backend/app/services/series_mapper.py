"""Claude tool-use for prompt → series ID mapping.

Uses Claude's tool_use feature to extract structured data source information
from a natural language analysis request.
"""
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
            },
            "date_range": {
                "type": "object",
                "properties": {
                    "start": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format. Use first day of the year if only year given.",
                    },
                    "end": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format. Use last day of the year if only year given.",
                    },
                },
                "required": ["start", "end"],
                "description": "Date range extracted from the user's prompt. If not specified, use 20 years back from today.",
            },
        },
        "required": ["sources", "date_range"],
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
        from app.config import settings
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


def map_prompt_to_sources(prompt: str) -> dict:
    """Map a natural language prompt to data source descriptors and date range.

    Uses Claude tool-use to extract structured source + series_id pairs and
    the date range specified in the prompt.

    Args:
        prompt: Natural language analysis request from the user.

    Returns:
        Dict with keys:
            - sources: list of dicts with keys source, series_id, display_name, rationale.
            - date_range: dict with keys start and end (YYYY-MM-DD strings), or None.

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
        return {
            "sources": tool_use.input["sources"],
            "date_range": tool_use.input.get("date_range"),
        }
    except StopIteration:
        raise ValueError("Claude response did not contain a tool_use block.")
    except Exception as exc:
        raise ValueError(f"Failed to map prompt to data sources: {exc}") from exc
