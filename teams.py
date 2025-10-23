"""NFL team constants and metadata."""

# All 32 NFL teams with metadata
TEAMS = [
    {"name": "Arizona Cardinals", "abbreviation": "ARI", "city": "Arizona", "mascot": "Cardinals"},
    {"name": "Atlanta Falcons", "abbreviation": "ATL", "city": "Atlanta", "mascot": "Falcons"},
    {"name": "Baltimore Ravens", "abbreviation": "BAL", "city": "Baltimore", "mascot": "Ravens"},
    {"name": "Buffalo Bills", "abbreviation": "BUF", "city": "Buffalo", "mascot": "Bills"},
    {"name": "Carolina Panthers", "abbreviation": "CAR", "city": "Carolina", "mascot": "Panthers"},
    {"name": "Chicago Bears", "abbreviation": "CHI", "city": "Chicago", "mascot": "Bears"},
    {"name": "Cincinnati Bengals", "abbreviation": "CIN", "city": "Cincinnati", "mascot": "Bengals"},
    {"name": "Cleveland Browns", "abbreviation": "CLE", "city": "Cleveland", "mascot": "Browns"},
    {"name": "Dallas Cowboys", "abbreviation": "DAL", "city": "Dallas", "mascot": "Cowboys"},
    {"name": "Denver Broncos", "abbreviation": "DEN", "city": "Denver", "mascot": "Broncos"},
    {"name": "Detroit Lions", "abbreviation": "DET", "city": "Detroit", "mascot": "Lions"},
    {"name": "Green Bay Packers", "abbreviation": "GB", "city": "Green Bay", "mascot": "Packers"},
    {"name": "Houston Texans", "abbreviation": "HOU", "city": "Houston", "mascot": "Texans"},
    {"name": "Indianapolis Colts", "abbreviation": "IND", "city": "Indianapolis", "mascot": "Colts"},
    {"name": "Jacksonville Jaguars", "abbreviation": "JAX", "city": "Jacksonville", "mascot": "Jaguars"},
    {"name": "Kansas City Chiefs", "abbreviation": "KC", "city": "Kansas City", "mascot": "Chiefs"},
    {"name": "Las Vegas Raiders", "abbreviation": "LV", "city": "Las Vegas", "mascot": "Raiders"},
    {"name": "Los Angeles Chargers", "abbreviation": "LAC", "city": "Los Angeles", "mascot": "Chargers"},
    {"name": "Los Angeles Rams", "abbreviation": "LAR", "city": "Los Angeles", "mascot": "Rams"},
    {"name": "Miami Dolphins", "abbreviation": "MIA", "city": "Miami", "mascot": "Dolphins"},
    {"name": "Minnesota Vikings", "abbreviation": "MIN", "city": "Minnesota", "mascot": "Vikings"},
    {"name": "New England Patriots", "abbreviation": "NE", "city": "New England", "mascot": "Patriots"},
    {"name": "New Orleans Saints", "abbreviation": "NO", "city": "New Orleans", "mascot": "Saints"},
    {"name": "New York Giants", "abbreviation": "NYG", "city": "New York", "mascot": "Giants"},
    {"name": "New York Jets", "abbreviation": "NYJ", "city": "New York", "mascot": "Jets"},
    {"name": "Philadelphia Eagles", "abbreviation": "PHI", "city": "Philadelphia", "mascot": "Eagles"},
    {"name": "Pittsburgh Steelers", "abbreviation": "PIT", "city": "Pittsburgh", "mascot": "Steelers"},
    {"name": "San Francisco 49ers", "abbreviation": "SF", "city": "San Francisco", "mascot": "49ers"},
    {"name": "Seattle Seahawks", "abbreviation": "SEA", "city": "Seattle", "mascot": "Seahawks"},
    {"name": "Tampa Bay Buccaneers", "abbreviation": "TB", "city": "Tampa Bay", "mascot": "Buccaneers"},
    {"name": "Tennessee Titans", "abbreviation": "TEN", "city": "Tennessee", "mascot": "Titans"},
    {"name": "Washington Commanders", "abbreviation": "WAS", "city": "Washington", "mascot": "Commanders"},
]

# Team names only (sorted alphabetically)
TEAM_NAMES = sorted([team["name"] for team in TEAMS])

# Abbreviation to full name mapping
TEAM_ABBR_MAP = {team["abbreviation"]: team["name"] for team in TEAMS}

# Full name to abbreviation mapping
TEAM_NAME_TO_ABBR = {team["name"]: team["abbreviation"] for team in TEAMS}
