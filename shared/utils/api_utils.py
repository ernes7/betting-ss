"""API utilities for Claude AI cost calculations."""

from config import settings


def calculate_api_cost(input_tokens: int, output_tokens: int, model: str | None = None) -> float:
    """Calculate total API cost based on token usage.

    Args:
        input_tokens: Number of input tokens used
        output_tokens: Number of output tokens generated
        model: Claude model name (e.g., "claude-sonnet-4-5-20250929" or "claude-haiku-...")

    Returns:
        Total cost in dollars
    """
    # Get default model from settings if not provided
    if model is None:
        model = settings['api']['claude']['model']

    # Determine pricing based on model
    # Claude Haiku 4.5: $0.80/MTok input, $4/MTok output
    # Claude Sonnet 4.5: $3/MTok input, $15/MTok output
    if "haiku" in model.lower():
        input_cost_per_mtok = 0.80
        output_cost_per_mtok = 4.0
    else:  # Sonnet (default)
        input_cost_per_mtok = settings['api']['claude']['input_cost_per_mtok']
        output_cost_per_mtok = settings['api']['claude']['output_cost_per_mtok']

    input_cost = (input_tokens / 1_000_000) * input_cost_per_mtok
    output_cost = (output_tokens / 1_000_000) * output_cost_per_mtok
    return input_cost + output_cost


def format_cost_display(cost: float) -> str:
    """Format cost for display.

    Args:
        cost: Cost in dollars

    Returns:
        Formatted cost string (e.g., "$0.1234" or "$0.0001")
    """
    if cost >= 1:
        return f"${cost:.2f}"
    elif cost >= 0.01:
        return f"${cost:.4f}"
    else:
        return f"${cost:.6f}"
