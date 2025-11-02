"""API configuration constants for Claude AI integration."""

# Claude API Model Configuration
CLAUDE_MODEL = "claude-sonnet-4-5-20250929"
CLAUDE_MODEL_ALIAS = "Sonnet 4.5"

# API Cost per Million Tokens (in dollars)
CLAUDE_INPUT_COST_PER_MTOK = 3.0  # $3 per MTok input
CLAUDE_OUTPUT_COST_PER_MTOK = 15.0  # $15 per MTok output

# API Request Configuration
MAX_TOKENS = 16000  # Maximum tokens for response
TEMPERATURE = 0.7  # Temperature for text generation


def calculate_api_cost(input_tokens: int, output_tokens: int, model: str = CLAUDE_MODEL) -> float:
    """Calculate total API cost based on token usage.

    Args:
        input_tokens: Number of input tokens used
        output_tokens: Number of output tokens generated
        model: Claude model name (e.g., "claude-sonnet-4-5-20250929" or "claude-haiku-...")

    Returns:
        Total cost in dollars
    """
    # Determine pricing based on model
    # Claude Haiku 4.5: $0.80/MTok input, $4/MTok output
    # Claude Sonnet 4.5: $3/MTok input, $15/MTok output
    if "haiku" in model.lower():
        input_cost_per_mtok = 0.80
        output_cost_per_mtok = 4.0
    else:  # Sonnet (default)
        input_cost_per_mtok = CLAUDE_INPUT_COST_PER_MTOK
        output_cost_per_mtok = CLAUDE_OUTPUT_COST_PER_MTOK

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
