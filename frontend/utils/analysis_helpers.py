"""Analysis data extraction helpers with backward compatibility.

Handles both new dual-system format and legacy single-system format:
- New format: {"ai_system": {...}, "ev_system": {...}, "comparison": {...}}
- Legacy format: {"summary": {...}, "bet_results": [...]}
"""

from typing import Dict, Optional


def get_system_summary(analysis: Optional[Dict], system_key: str) -> Dict:
    """Extract summary for specific system with backward compatibility.

    Args:
        analysis: Analysis dictionary (new or old format)
        system_key: 'ai_system' or 'ev_system'

    Returns:
        Summary dictionary with keys like 'total_profit', 'win_rate', etc.
        Returns empty dict if not found.

    Examples:
        >>> analysis = {"ai_system": {"summary": {"total_profit": 100}}}
        >>> get_system_summary(analysis, "ai_system")
        {'total_profit': 100}

        >>> analysis = {"summary": {"total_profit": 50}}
        >>> get_system_summary(analysis, "ai_system")
        {'total_profit': 50}
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


def detect_analysis_format(analysis: Optional[Dict]) -> Dict:
    """Detect and extract analysis data from old or new format.

    Args:
        analysis: Analysis dictionary (may be new or legacy format)

    Returns:
        Dictionary with keys:
            - ai_analysis: AI system analysis dict or None
            - ev_analysis: EV system analysis dict or None
            - comparison: Comparison data dict or None
            - format: 'dual', 'legacy', or None
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


def get_bet_results(analysis: Optional[Dict], system_key: str) -> list:
    """Extract bet results for a specific system.

    Args:
        analysis: Analysis dictionary (new or old format)
        system_key: 'ai_system' or 'ev_system'

    Returns:
        List of bet result dictionaries
    """
    if not analysis:
        return []

    # New dual-system format
    if analysis.get(system_key):
        return analysis[system_key].get('bet_results', [])

    # Old single-system format - only return for AI system
    if system_key == 'ai_system' and 'bet_results' in analysis and 'ai_system' not in analysis:
        return analysis.get('bet_results', [])

    return []


def calculate_combined_metrics(analysis: Optional[Dict]) -> Dict:
    """Calculate combined metrics from both systems.

    Args:
        analysis: Analysis dictionary with ai_system and/or ev_system

    Returns:
        Dictionary with combined metrics
    """
    ai_summary = get_system_summary(analysis, 'ai_system')
    ev_summary = get_system_summary(analysis, 'ev_system')

    total_profit = (
        ai_summary.get('total_profit', 0) +
        ev_summary.get('total_profit', 0)
    )
    total_bets = (
        ai_summary.get('total_bets', 0) +
        ev_summary.get('total_bets', 0)
    )
    total_won = (
        ai_summary.get('bets_won', 0) +
        ev_summary.get('bets_won', 0)
    )

    win_rate = (total_won / total_bets * 100) if total_bets > 0 else 0

    return {
        'total_profit': total_profit,
        'total_bets': total_bets,
        'total_won': total_won,
        'win_rate': win_rate,
        'ai_profit': ai_summary.get('total_profit', 0),
        'ev_profit': ev_summary.get('total_profit', 0),
    }
