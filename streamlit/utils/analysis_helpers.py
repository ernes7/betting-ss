"""Analysis data extraction helpers with backward compatibility.

Handles both new dual-system format and legacy single-system format:
- New format: {"ai_system": {...}, "ev_system": {...}, "comparison": {...}}
- Legacy format: {"summary": {...}, "bet_results": [...]}
"""

from typing import Optional


def get_system_summary(analysis: Optional[dict], system_key: str) -> dict:
    """Extract summary for specific system with backward compatibility.

    Args:
        analysis: Analysis dictionary (new or old format)
        system_key: 'ai_system' or 'ev_system'

    Returns:
        Summary dictionary with keys like 'total_profit', 'win_rate', etc.
        Returns empty dict if not found.

    Examples:
        # New dual-system format
        >>> analysis = {"ai_system": {"summary": {"total_profit": 100}}}
        >>> get_system_summary(analysis, "ai_system")
        {'total_profit': 100}

        # Legacy single-system format (treated as AI system)
        >>> analysis = {"summary": {"total_profit": 50}}
        >>> get_system_summary(analysis, "ai_system")
        {'total_profit': 50}

        # EV system not in legacy format
        >>> analysis = {"summary": {"total_profit": 50}}
        >>> get_system_summary(analysis, "ev_system")
        {}

        # None or missing data
        >>> get_system_summary(None, "ai_system")
        {}
    """
    if not analysis:
        return {}

    # New dual-system format
    if analysis.get(system_key):
        return analysis[system_key].get('summary', {})

    # Old single-system format - only return for AI system
    if system_key == 'ai_system' and 'summary' in analysis and 'ai_system' not in analysis:
        return analysis.get('summary', {})

    return {}


def detect_analysis_format(analysis: Optional[dict]) -> dict:
    """Detect and extract analysis data from old or new format.

    Args:
        analysis: Analysis dictionary (may be new or legacy format)

    Returns:
        Dictionary with keys:
            - ai_analysis: AI system analysis dict or None
            - ev_analysis: EV system analysis dict or None
            - comparison: Comparison data dict or None
            - format: 'dual', 'legacy', or None

    Examples:
        # New dual-system format
        >>> analysis = {
        ...     "ai_system": {"summary": {}},
        ...     "ev_system": {"summary": {}},
        ...     "comparison": {"consensus_count": 2}
        ... }
        >>> result = detect_analysis_format(analysis)
        >>> result['format']
        'dual'
        >>> result['ai_analysis'] is not None
        True

        # Legacy single-system format
        >>> analysis = {"summary": {"total_profit": 100}, "bet_results": []}
        >>> result = detect_analysis_format(analysis)
        >>> result['format']
        'legacy'
        >>> result['ai_analysis'] is not None
        True
        >>> result['ev_analysis'] is None
        True

        # No analysis
        >>> result = detect_analysis_format(None)
        >>> result['format'] is None
        True
    """
    if not analysis:
        return {
            'ai_analysis': None,
            'ev_analysis': None,
            'comparison': None,
            'format': None
        }

    # New dual-system format
    if "ai_system" in analysis or "ev_system" in analysis:
        return {
            'ai_analysis': analysis.get("ai_system"),
            'ev_analysis': analysis.get("ev_system"),
            'comparison': analysis.get("comparison"),
            'format': 'dual'
        }

    # Old single-system format - treat as AI system only
    if "summary" in analysis:
        return {
            'ai_analysis': analysis,
            'ev_analysis': None,
            'comparison': None,
            'format': 'legacy'
        }

    return {
        'ai_analysis': None,
        'ev_analysis': None,
        'comparison': None,
        'format': None
    }
