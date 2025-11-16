"""Service for comparing EV calculator results with AI predictions."""

from typing import Dict, List, Tuple
from datetime import datetime


class ComparisonService:
    """Service for analyzing agreement between EV calculator and AI predictor."""

    @staticmethod
    def compare_predictions(
        ev_results: dict,
        ai_predictions: dict
    ) -> dict:
        """Compare EV calculator results with AI predictions.

        Args:
            ev_results: EV calculator results dictionary
            ai_predictions: AI predictions dictionary

        Returns:
            Comparison data dictionary with overlap analysis
        """
        ev_bets = ev_results.get("bets", [])
        ai_bets = ai_predictions.get("bets", [])

        # Find overlapping bets
        overlapping_bets = []
        ev_only_bets = []
        ai_only_bets = []

        # Track which AI bets we've matched
        matched_ai_indices = set()

        # Compare each EV bet with AI bets
        for ev_bet in ev_bets:
            match_found, ai_index = ComparisonService._find_matching_bet(
                ev_bet, ai_bets, matched_ai_indices
            )

            if match_found:
                # Create overlap record
                ai_bet = ai_bets[ai_index]
                overlap = ComparisonService._create_overlap_record(
                    ev_bet, ai_bet
                )
                overlapping_bets.append(overlap)
                matched_ai_indices.add(ai_index)
            else:
                # EV-only bet
                ev_only_bets.append({
                    "rank": ev_bet.get("rank"),
                    "description": ev_bet.get("description"),
                    "ev_percent": ev_bet.get("ev_percent"),
                    "odds": ev_bet.get("odds")
                })

        # Find AI-only bets (not matched)
        for i, ai_bet in enumerate(ai_bets):
            if i not in matched_ai_indices:
                ai_only_bets.append({
                    "rank": ai_bet.get("rank"),
                    "bet": ai_bet.get("bet"),
                    "expected_value": ai_bet.get("expected_value"),
                    "odds": ai_bet.get("odds")
                })

        # Calculate agreement metrics
        total_bets = max(len(ev_bets), len(ai_bets))
        agreement_rate = len(overlapping_bets) / total_bets if total_bets > 0 else 0

        # Calculate average EV difference on overlapping bets
        avg_ev_diff = 0
        if overlapping_bets:
            ev_diffs = [bet["ev_difference"] for bet in overlapping_bets]
            avg_ev_diff = sum(ev_diffs) / len(ev_diffs)

        # Build comparison result
        teams = ev_results.get("teams", ai_predictions.get("teams", []))
        date = ev_results.get("date", ai_predictions.get("date", ""))

        comparison = {
            "game_key": f"{date}_{ComparisonService._get_team_abbr(teams)}",
            "teams": teams,
            "date": date,
            "generated_at": datetime.now().isoformat(),
            "agreement_rate": round(agreement_rate, 3),
            "overlapping_bets": overlapping_bets,
            "ev_only_bets": ev_only_bets,
            "ai_only_bets": ai_only_bets,
            "summary": {
                "consensus_picks": len(overlapping_bets),
                "ev_unique_picks": len(ev_only_bets),
                "ai_unique_picks": len(ai_only_bets),
                "avg_ev_difference_on_overlap": round(avg_ev_diff, 2)
            }
        }

        return comparison

    @staticmethod
    def _find_matching_bet(
        ev_bet: dict,
        ai_bets: List[dict],
        matched_indices: set
    ) -> Tuple[bool, int]:
        """Find a matching AI bet for an EV bet.

        Bets are considered matching if they have the same player and market.

        Args:
            ev_bet: EV calculator bet dictionary
            ai_bets: List of AI prediction bet dictionaries
            matched_indices: Set of already matched AI bet indices

        Returns:
            Tuple of (match_found: bool, ai_bet_index: int)
        """
        ev_description = ev_bet.get("description", "").lower()
        ev_player = ev_bet.get("player", "").lower()
        ev_market = ev_bet.get("market", "")

        for i, ai_bet in enumerate(ai_bets):
            # Skip already matched bets
            if i in matched_indices:
                continue

            ai_description = ai_bet.get("bet", "").lower()

            # Match by player name and market
            if ev_player and ev_player in ai_description:
                # Check if market matches
                if ComparisonService._markets_match(ev_market, ai_description):
                    return True, i

            # Fallback: fuzzy match by description
            if ComparisonService._descriptions_match(ev_description, ai_description):
                return True, i

        return False, -1

    @staticmethod
    def _markets_match(ev_market: str, ai_description: str) -> bool:
        """Check if market types match between EV and AI bets.

        Args:
            ev_market: EV bet market (e.g., "receiving_yards", "rushing_yards")
            ai_description: AI bet description string

        Returns:
            True if markets match
        """
        # Map EV markets to keywords in AI descriptions
        market_keywords = {
            "receiving_yards": ["receiving yards", "rec yards", "receiving"],
            "rushing_yards": ["rushing yards", "rush yards"],
            "passing_yards": ["passing yards", "pass yards"],
            "receptions": ["receptions", "catches"],
            "rush_attempts": ["rush attempts", "carries"],
            "pass_attempts": ["pass attempts"],
            "pass_completions": ["completions"],
            "passing_tds": ["passing td", "pass td"],
            "rushing_tds": ["rushing td", "rush td"],
            "receiving_tds": ["receiving td", "rec td"],
            "anytime_td": ["anytime td", "anytime touchdown"]
        }

        keywords = market_keywords.get(ev_market, [])
        ai_desc_lower = ai_description.lower()

        return any(keyword in ai_desc_lower for keyword in keywords)

    @staticmethod
    def _descriptions_match(ev_desc: str, ai_desc: str) -> bool:
        """Fuzzy match bet descriptions.

        Args:
            ev_desc: EV bet description (lowercase)
            ai_desc: AI bet description (lowercase)

        Returns:
            True if descriptions are similar enough
        """
        # Extract key words (ignore common words like "over", "under")
        stop_words = {"over", "under", "vs", "at", "the", "a", "an"}

        ev_words = set(word for word in ev_desc.split() if word not in stop_words)
        ai_words = set(word for word in ai_desc.split() if word not in stop_words)

        # Check for significant overlap (at least 60% of words match)
        if not ev_words or not ai_words:
            return False

        intersection = ev_words.intersection(ai_words)
        similarity = len(intersection) / max(len(ev_words), len(ai_words))

        return similarity >= 0.6

    @staticmethod
    def _create_overlap_record(ev_bet: dict, ai_bet: dict) -> dict:
        """Create a record for an overlapping bet.

        Args:
            ev_bet: EV calculator bet dictionary
            ai_bet: AI prediction bet dictionary

        Returns:
            Overlap record dictionary
        """
        ev_percent = ev_bet.get("ev_percent", 0)
        ai_percent = ai_bet.get("expected_value", 0)

        return {
            "description": ev_bet.get("description"),
            "ev_rank": ev_bet.get("rank"),
            "ai_rank": ai_bet.get("rank"),
            "ev_percent_ev": round(ev_percent, 2),
            "ai_percent_ev": round(ai_percent, 2),
            "ev_difference": round(abs(ev_percent - ai_percent), 2),
            "odds": ev_bet.get("odds"),
            "market": ev_bet.get("market", "")
        }

    @staticmethod
    def _get_team_abbr(teams: List[str]) -> str:
        """Extract team abbreviations from team names.

        Args:
            teams: List of team names (e.g., ["New York Jets", "New England Patriots"])

        Returns:
            Team abbreviations string (e.g., "nyj_nwe")
        """
        if len(teams) < 2:
            return "unknown_unknown"

        # Simple abbreviation: first 3 letters of last word, lowercase
        def get_abbr(team_name: str) -> str:
            words = team_name.split()
            if not words:
                return "unk"
            return words[-1][:3].lower()

        return f"{get_abbr(teams[0])}_{get_abbr(teams[1])}"
