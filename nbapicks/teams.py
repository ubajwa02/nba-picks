"""Team identity. ESPN abbreviations are canonical inside NBA Picks."""
from __future__ import annotations

# canonical abbr -> nickname (used to match other providers' names)
TEAMS = {
    "ATL": "Hawks", "BOS": "Celtics", "BKN": "Nets", "CHA": "Hornets", "CHI": "Bulls",
    "CLE": "Cavaliers", "DAL": "Mavericks", "DEN": "Nuggets", "DET": "Pistons", "GS": "Warriors",
    "HOU": "Rockets", "IND": "Pacers", "LAC": "Clippers", "LAL": "Lakers", "MEM": "Grizzlies",
    "MIA": "Heat", "MIL": "Bucks", "MIN": "Timberwolves", "NO": "Pelicans", "NY": "Knicks",
    "OKC": "Thunder", "ORL": "Magic", "PHI": "76ers", "PHX": "Suns", "POR": "Trail Blazers",
    "SAC": "Kings", "SA": "Spurs", "TOR": "Raptors", "UTAH": "Jazz", "WSH": "Wizards",
}
_BY_NICK = {v.lower(): k for k, v in TEAMS.items()}
_ALIASES = {"NOP": "NO", "NYK": "NY", "GSW": "GS", "SAS": "SA", "UTA": "UTAH", "WAS": "WSH",
            "BRK": "BKN", "PHO": "PHX", "CHO": "CHA", "NJ": "BKN", "NOH": "NO", "SEA": "OKC"}


def canon(abbr: str) -> str:
    a = (abbr or "").upper().strip()
    return _ALIASES.get(a, a)


def from_name(name: str) -> str | None:
    """'BOS Celtics', 'Boston Celtics', 'Celtics', 'POR Trail Blazers' -> canonical abbr."""
    n = (name or "").lower().strip()
    for nick, abbr in _BY_NICK.items():
        if n.endswith(nick):
            return abbr
    return None
