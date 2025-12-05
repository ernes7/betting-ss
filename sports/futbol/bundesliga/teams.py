"""Bundesliga team constants and metadata."""

# All 18 Bundesliga teams with metadata
TEAMS = [
    {
        "name": "Bayern Munich",
        "fbref_id": "054efa67",
        "slug": "Bayern-Munich-Stats",
    },
    {
        "name": "RB Leipzig",
        "fbref_id": "acbb6a5b",
        "slug": "RB-Leipzig-Stats",
    },
    {
        "name": "Borussia Dortmund",
        "fbref_id": "add600ae",
        "slug": "Dortmund-Stats",
    },
    {
        "name": "Bayer Leverkusen",
        "fbref_id": "c7a9f859",
        "slug": "Bayer-Leverkusen-Stats",
    },
    {
        "name": "TSG Hoffenheim",
        "fbref_id": "033ea6b8",
        "slug": "Hoffenheim-Stats",
    },
    {
        "name": "VfB Stuttgart",
        "fbref_id": "598bc722",
        "slug": "Stuttgart-Stats",
    },
    {
        "name": "Eintracht Frankfurt",
        "fbref_id": "f0ac8ee6",
        "slug": "Eintracht-Frankfurt-Stats",
    },
    {
        "name": "SC Freiburg",
        "fbref_id": "a486e511",
        "slug": "Freiburg-Stats",
    },
    {
        "name": "Werder Bremen",
        "fbref_id": "62add3bf",
        "slug": "Werder-Bremen-Stats",
    },
    {
        "name": "1. FC Koln",
        "fbref_id": "bc357bf7",
        "slug": "Koln-Stats",
    },
    {
        "name": "Union Berlin",
        "fbref_id": "7a41008f",
        "slug": "Union-Berlin-Stats",
    },
    {
        "name": "Borussia Monchengladbach",
        "fbref_id": "32f3ee20",
        "slug": "Monchengladbach-Stats",
    },
    {
        "name": "Hamburger SV",
        "fbref_id": "26790c6a",
        "slug": "Hamburger-SV-Stats",
    },
    {
        "name": "FC Augsburg",
        "fbref_id": "0cdc4311",
        "slug": "Augsburg-Stats",
    },
    {
        "name": "VfL Wolfsburg",
        "fbref_id": "4eaa11d7",
        "slug": "Wolfsburg-Stats",
    },
    {
        "name": "1. FC Heidenheim",
        "fbref_id": "18d9d2a7",
        "slug": "Heidenheim-Stats",
    },
    {
        "name": "FC St. Pauli",
        "fbref_id": "54864664",
        "slug": "St-Pauli-Stats",
    },
    {
        "name": "1. FSV Mainz 05",
        "fbref_id": "a224b06a",
        "slug": "Mainz-05-Stats",
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
