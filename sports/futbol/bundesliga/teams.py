"""Bundesliga team constants and metadata."""

# All 18 Bundesliga teams with metadata
# aliases: Alternative names used by DraftKings and other sources
TEAMS = [
    {
        "name": "Bayern Munich",
        "fbref_id": "054efa67",
        "slug": "Bayern-Munich-Stats",
        "profile_folder": "bayern_munich",
        "aliases": ["Bayern Munchen", "Bayern", "FC Bayern", "FC Bayern Munchen", "bayern_mun", "bayern_munich"],
    },
    {
        "name": "RB Leipzig",
        "fbref_id": "acbb6a5b",
        "slug": "RB-Leipzig-Stats",
        "profile_folder": "rb_leipzig",
        "aliases": ["Leipzig", "Red Bull Leipzig", "rb_leipzig"],
    },
    {
        "name": "Borussia Dortmund",
        "fbref_id": "add600ae",
        "slug": "Dortmund-Stats",
        "profile_folder": "dortmund",
        "aliases": ["Dortmund", "BVB"],
    },
    {
        "name": "Bayer Leverkusen",
        "fbref_id": "c7a9f859",
        "slug": "Bayer-Leverkusen-Stats",
        "profile_folder": "bayer_leverkusen",
        "aliases": ["Leverkusen", "Bayer 04 Leverkusen"],
    },
    {
        "name": "TSG Hoffenheim",
        "fbref_id": "033ea6b8",
        "slug": "Hoffenheim-Stats",
        "profile_folder": "hoffenheim",
        "aliases": ["Hoffenheim", "TSG 1899 Hoffenheim"],
    },
    {
        "name": "VfB Stuttgart",
        "fbref_id": "598bc722",
        "slug": "Stuttgart-Stats",
        "profile_folder": "stuttgart",
        "aliases": ["Stuttgart"],
    },
    {
        "name": "Eintracht Frankfurt",
        "fbref_id": "f0ac8ee6",
        "slug": "Eintracht-Frankfurt-Stats",
        "profile_folder": "eintracht_frankfurt",
        "aliases": ["Frankfurt", "SGE", "eintracht_", "eintracht", "Eint Frankfurt", "eint_frankfurt"],
    },
    {
        "name": "SC Freiburg",
        "fbref_id": "a486e511",
        "slug": "Freiburg-Stats",
        "profile_folder": "freiburg",
        "aliases": ["Freiburg"],
    },
    {
        "name": "Werder Bremen",
        "fbref_id": "62add3bf",
        "slug": "Werder-Bremen-Stats",
        "profile_folder": "werder_bremen",
        "aliases": ["Bremen", "SV Werder Bremen"],
    },
    {
        "name": "1. FC Koln",
        "fbref_id": "bc357bf7",
        "slug": "Koln-Stats",
        "profile_folder": "koln",
        "aliases": ["Koln", "Cologne", "FC Koln"],
    },
    {
        "name": "Union Berlin",
        "fbref_id": "7a41008f",
        "slug": "Union-Berlin-Stats",
        "profile_folder": "union_berlin",
        "aliases": ["Union", "1. FC Union Berlin", "union_berl", "union_berlin"],
    },
    {
        "name": "Borussia Monchengladbach",
        "fbref_id": "32f3ee20",
        "slug": "Monchengladbach-Stats",
        "profile_folder": "monchengladbach",
        "aliases": ["Monchengladbach", "Gladbach", "BMG"],
    },
    {
        "name": "Hamburger SV",
        "fbref_id": "26790c6a",
        "slug": "Hamburger-SV-Stats",
        "profile_folder": "hamburger_sv",
        "aliases": ["Hamburg", "HSV"],
    },
    {
        "name": "FC Augsburg",
        "fbref_id": "0cdc4311",
        "slug": "Augsburg-Stats",
        "profile_folder": "augsburg",
        "aliases": ["Augsburg"],
    },
    {
        "name": "VfL Wolfsburg",
        "fbref_id": "4eaa11d7",
        "slug": "Wolfsburg-Stats",
        "profile_folder": "wolfsburg",
        "aliases": ["Wolfsburg"],
    },
    {
        "name": "1. FC Heidenheim",
        "fbref_id": "18d9d2a7",
        "slug": "Heidenheim-Stats",
        "profile_folder": "heidenheim",
        "aliases": ["Heidenheim", "FC Heidenheim", "fc_heidenh", "fc_heidenheim"],
    },
    {
        "name": "FC St. Pauli",
        "fbref_id": "54864664",
        "slug": "St-Pauli-Stats",
        "profile_folder": "st_pauli",
        "aliases": ["St. Pauli", "St Pauli", "Sankt Pauli", "st_pauli"],
    },
    {
        "name": "1. FSV Mainz 05",
        "fbref_id": "a224b06a",
        "slug": "Mainz-05-Stats",
        "profile_folder": "mainz",
        "aliases": ["Mainz", "Mainz 05"],
    },
    {
        "name": "Holstein Kiel",
        "fbref_id": "4fcb3c66",
        "slug": "Holstein-Kiel-Stats",
        "profile_folder": "holstein_kiel",
        "aliases": ["Kiel"],
    },
    {
        "name": "VfL Bochum",
        "fbref_id": "b42c6323",
        "slug": "Bochum-Stats",
        "profile_folder": "bochum",
        "aliases": ["Bochum"],
    },
]

# Team names only (sorted alphabetically)
TEAM_NAMES = sorted([team["name"] for team in TEAMS])

# FBRef ID to full name mapping
FBREF_ID_TO_NAME = {team["fbref_id"]: team["name"] for team in TEAMS}

# Full name to FBRef ID mapping
NAME_TO_FBREF_ID = {team["name"]: team["fbref_id"] for team in TEAMS}

# Full name to slug mapping
NAME_TO_SLUG = {team["name"]: team["slug"] for team in TEAMS}

# FBRef ID to slug mapping
FBREF_ID_TO_SLUG = {team["fbref_id"]: team["slug"] for team in TEAMS}


def find_team_by_name(name: str) -> dict | None:
    """Find team by name or alias (case-insensitive).

    Args:
        name: Team name to search for (e.g., "Bayern Munchen", "Stuttgart")

    Returns:
        Team dict with name, fbref_id, slug, aliases or None if not found
    """
    name_lower = name.lower().strip()

    for team in TEAMS:
        # Check exact match on primary name
        if name_lower == team["name"].lower():
            return team

        # Check aliases
        for alias in team.get("aliases", []):
            if name_lower == alias.lower():
                return team

    # Fallback: partial match on primary name or aliases
    for team in TEAMS:
        if name_lower in team["name"].lower():
            return team
        for alias in team.get("aliases", []):
            if name_lower in alias.lower():
                return team

    return None
