"""NFL team constants and metadata."""

# All 32 NFL teams with metadata
TEAMS = [
    {"name": "Arizona Cardinals", "abbreviation": "ARI", "pfr_abbr": "crd", "city": "Arizona", "mascot": "Cardinals"},
    {"name": "Atlanta Falcons", "abbreviation": "ATL", "pfr_abbr": "atl", "city": "Atlanta", "mascot": "Falcons"},
    {"name": "Baltimore Ravens", "abbreviation": "BAL", "pfr_abbr": "rav", "city": "Baltimore", "mascot": "Ravens"},
    {"name": "Buffalo Bills", "abbreviation": "BUF", "pfr_abbr": "buf", "city": "Buffalo", "mascot": "Bills"},
    {"name": "Carolina Panthers", "abbreviation": "CAR", "pfr_abbr": "car", "city": "Carolina", "mascot": "Panthers"},
    {"name": "Chicago Bears", "abbreviation": "CHI", "pfr_abbr": "chi", "city": "Chicago", "mascot": "Bears"},
    {"name": "Cincinnati Bengals", "abbreviation": "CIN", "pfr_abbr": "cin", "city": "Cincinnati", "mascot": "Bengals"},
    {"name": "Cleveland Browns", "abbreviation": "CLE", "pfr_abbr": "cle", "city": "Cleveland", "mascot": "Browns"},
    {"name": "Dallas Cowboys", "abbreviation": "DAL", "pfr_abbr": "dal", "city": "Dallas", "mascot": "Cowboys"},
    {"name": "Denver Broncos", "abbreviation": "DEN", "pfr_abbr": "den", "city": "Denver", "mascot": "Broncos"},
    {"name": "Detroit Lions", "abbreviation": "DET", "pfr_abbr": "det", "city": "Detroit", "mascot": "Lions"},
    {"name": "Green Bay Packers", "abbreviation": "GB", "pfr_abbr": "gnb", "city": "Green Bay", "mascot": "Packers"},
    {"name": "Houston Texans", "abbreviation": "HOU", "pfr_abbr": "htx", "city": "Houston", "mascot": "Texans"},
    {"name": "Indianapolis Colts", "abbreviation": "IND", "pfr_abbr": "clt", "city": "Indianapolis", "mascot": "Colts"},
    {"name": "Jacksonville Jaguars", "abbreviation": "JAX", "pfr_abbr": "jax", "city": "Jacksonville", "mascot": "Jaguars"},
    {"name": "Kansas City Chiefs", "abbreviation": "KC", "pfr_abbr": "kan", "city": "Kansas City", "mascot": "Chiefs"},
    {"name": "Las Vegas Raiders", "abbreviation": "LV", "pfr_abbr": "rai", "city": "Las Vegas", "mascot": "Raiders"},
    {"name": "Los Angeles Chargers", "abbreviation": "LAC", "pfr_abbr": "sdg", "city": "Los Angeles", "mascot": "Chargers"},
    {"name": "Los Angeles Rams", "abbreviation": "LAR", "pfr_abbr": "ram", "city": "Los Angeles", "mascot": "Rams"},
    {"name": "Miami Dolphins", "abbreviation": "MIA", "pfr_abbr": "mia", "city": "Miami", "mascot": "Dolphins"},
    {"name": "Minnesota Vikings", "abbreviation": "MIN", "pfr_abbr": "min", "city": "Minnesota", "mascot": "Vikings"},
    {"name": "New England Patriots", "abbreviation": "NE", "pfr_abbr": "nwe", "city": "New England", "mascot": "Patriots"},
    {"name": "New Orleans Saints", "abbreviation": "NO", "pfr_abbr": "nor", "city": "New Orleans", "mascot": "Saints"},
    {"name": "New York Giants", "abbreviation": "NYG", "pfr_abbr": "nyg", "city": "New York", "mascot": "Giants"},
    {"name": "New York Jets", "abbreviation": "NYJ", "pfr_abbr": "nyj", "city": "New York", "mascot": "Jets"},
    {"name": "Philadelphia Eagles", "abbreviation": "PHI", "pfr_abbr": "phi", "city": "Philadelphia", "mascot": "Eagles"},
    {"name": "Pittsburgh Steelers", "abbreviation": "PIT", "pfr_abbr": "pit", "city": "Pittsburgh", "mascot": "Steelers"},
    {"name": "San Francisco 49ers", "abbreviation": "SF", "pfr_abbr": "sfo", "city": "San Francisco", "mascot": "49ers"},
    {"name": "Seattle Seahawks", "abbreviation": "SEA", "pfr_abbr": "sea", "city": "Seattle", "mascot": "Seahawks"},
    {"name": "Tampa Bay Buccaneers", "abbreviation": "TB", "pfr_abbr": "tam", "city": "Tampa Bay", "mascot": "Buccaneers"},
    {"name": "Tennessee Titans", "abbreviation": "TEN", "pfr_abbr": "oti", "city": "Tennessee", "mascot": "Titans"},
    {"name": "Washington Commanders", "abbreviation": "WAS", "pfr_abbr": "was", "city": "Washington", "mascot": "Commanders"},
]

# Team names only (sorted alphabetically)
TEAM_NAMES = sorted([team["name"] for team in TEAMS])

# Abbreviation to full name mapping
TEAM_ABBR_MAP = {team["abbreviation"]: team["name"] for team in TEAMS}

# Full name to abbreviation mapping
TEAM_NAME_TO_ABBR = {team["name"]: team["abbreviation"] for team in TEAMS}
