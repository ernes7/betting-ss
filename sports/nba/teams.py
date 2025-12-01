"""NBA team constants and metadata."""

# All 30 NBA teams with metadata
TEAMS = [
    {"name": "Atlanta Hawks", "abbreviation": "ATL", "pbr_abbr": "ATL", "mascot": "Hawks"},
    {"name": "Boston Celtics", "abbreviation": "BOS", "pbr_abbr": "BOS", "mascot": "Celtics"},
    {"name": "Brooklyn Nets", "abbreviation": "BKN", "pbr_abbr": "BRK", "mascot": "Nets"},
    {"name": "Charlotte Hornets", "abbreviation": "CHA", "pbr_abbr": "CHO", "mascot": "Hornets"},
    {"name": "Chicago Bulls", "abbreviation": "CHI", "pbr_abbr": "CHI", "mascot": "Bulls"},
    {"name": "Cleveland Cavaliers", "abbreviation": "CLE", "pbr_abbr": "CLE", "mascot": "Cavaliers"},
    {"name": "Dallas Mavericks", "abbreviation": "DAL", "pbr_abbr": "DAL", "mascot": "Mavericks"},
    {"name": "Denver Nuggets", "abbreviation": "DEN", "pbr_abbr": "DEN", "mascot": "Nuggets"},
    {"name": "Detroit Pistons", "abbreviation": "DET", "pbr_abbr": "DET", "mascot": "Pistons"},
    {"name": "Golden State Warriors", "abbreviation": "GSW", "pbr_abbr": "GSW", "mascot": "Warriors"},
    {"name": "Houston Rockets", "abbreviation": "HOU", "pbr_abbr": "HOU", "mascot": "Rockets"},
    {"name": "Indiana Pacers", "abbreviation": "IND", "pbr_abbr": "IND", "mascot": "Pacers"},
    {"name": "Los Angeles Clippers", "abbreviation": "LAC", "pbr_abbr": "LAC", "mascot": "Clippers"},
    {"name": "Los Angeles Lakers", "abbreviation": "LAL", "pbr_abbr": "LAL", "mascot": "Lakers"},
    {"name": "Memphis Grizzlies", "abbreviation": "MEM", "pbr_abbr": "MEM", "mascot": "Grizzlies"},
    {"name": "Miami Heat", "abbreviation": "MIA", "pbr_abbr": "MIA", "mascot": "Heat"},
    {"name": "Milwaukee Bucks", "abbreviation": "MIL", "pbr_abbr": "MIL", "mascot": "Bucks"},
    {"name": "Minnesota Timberwolves", "abbreviation": "MIN", "pbr_abbr": "MIN", "mascot": "Timberwolves"},
    {"name": "New Orleans Pelicans", "abbreviation": "NOP", "pbr_abbr": "NOP", "mascot": "Pelicans"},
    {"name": "New York Knicks", "abbreviation": "NYK", "pbr_abbr": "NYK", "mascot": "Knicks"},
    {"name": "Oklahoma City Thunder", "abbreviation": "OKC", "pbr_abbr": "OKC", "mascot": "Thunder"},
    {"name": "Orlando Magic", "abbreviation": "ORL", "pbr_abbr": "ORL", "mascot": "Magic"},
    {"name": "Philadelphia 76ers", "abbreviation": "PHI", "pbr_abbr": "PHI", "mascot": "76ers"},
    {"name": "Phoenix Suns", "abbreviation": "PHX", "pbr_abbr": "PHO", "mascot": "Suns"},
    {"name": "Portland Trail Blazers", "abbreviation": "POR", "pbr_abbr": "POR", "mascot": "Trail Blazers"},
    {"name": "Sacramento Kings", "abbreviation": "SAC", "pbr_abbr": "SAC", "mascot": "Kings"},
    {"name": "San Antonio Spurs", "abbreviation": "SAS", "pbr_abbr": "SAS", "mascot": "Spurs"},
    {"name": "Toronto Raptors", "abbreviation": "TOR", "pbr_abbr": "TOR", "mascot": "Raptors"},
    {"name": "Utah Jazz", "abbreviation": "UTA", "pbr_abbr": "UTA", "mascot": "Jazz"},
    {"name": "Washington Wizards", "abbreviation": "WAS", "pbr_abbr": "WAS", "mascot": "Wizards"},
]

# Team names only (sorted alphabetically)
TEAM_NAMES = sorted([team["name"] for team in TEAMS])

# Abbreviation to full name mapping
TEAM_ABBR_MAP = {team["abbreviation"]: team["name"] for team in TEAMS}

# Full name to abbreviation mapping
TEAM_NAME_TO_ABBR = {team["name"]: team["abbreviation"] for team in TEAMS}

# DraftKings to Pro-Basketball-Reference abbreviation mapping
DK_TO_PBR_ABBR = {team["abbreviation"]: team["pbr_abbr"] for team in TEAMS}

# Pro-Basketball-Reference to DraftKings abbreviation mapping
PBR_TO_DK_ABBR = {team["pbr_abbr"]: team["abbreviation"] for team in TEAMS}

# Additional helper mappings
DK_ABBR_TO_NAME = {team["abbreviation"]: team["name"] for team in TEAMS}
PBR_ABBR_TO_NAME = {team["pbr_abbr"]: team["name"] for team in TEAMS}
