"""UEFA association-coefficient rules (2024/25 – 2026/27 cycle).

Source: UEFA 'How the association coefficients are calculated' + competition
regulations (bonus points). Only what is needed for the PoC is modelled.
"""
from dataclasses import dataclass

COMPETITIONS = ("UCL", "UEL", "UECL")

# Stages. Qualifying rounds score half points.
QUALIFYING = {"Q1", "Q2", "Q3", "PO"}
MAIN = {"LP", "KPO", "R16", "QF", "SF", "F"}   # KPO = knockout play-off

WIN, DRAW = 2.0, 1.0

# League-phase participation bonus (UCL only)
LP_PARTICIPATION_BONUS = {"UCL": 6.0, "UEL": 0.0, "UECL": 0.0}

# Bonus per ascending final league-phase rank (applied from rank 24 upward)
LP_RANK_STEP_9_24 = {"UCL": 0.25, "UEL": 0.25, "UECL": 0.125}
LP_RANK_STEP_1_8 = {"UCL": 0.25, "UEL": 0.25, "UECL": 0.25}

# Per knockout round reached (R16, QF, SF, F)
KO_ROUND_BONUS = {"UCL": 1.5, "UEL": 1.0, "UECL": 0.5}


@dataclass(frozen=True)
class Match:
    date: str
    competition: str   # UCL / UEL / UECL
    stage: str         # Q1..PO, LP, KPO, R16, QF, SF, F
    home: str          # club name
    away: str
    home_goals: int
    away_goals: int
    decided_on_penalties: bool = False  # then counts as a draw


def match_points(m: Match) -> dict[str, float]:
    """Points per club for one match (before dividing by #clubs)."""
    if m.decided_on_penalties or m.home_goals == m.away_goals:
        h = a = DRAW
    elif m.home_goals > m.away_goals:
        h, a = WIN, 0.0
    else:
        h, a = 0.0, WIN
    if m.stage in QUALIFYING:
        h, a = h / 2, a / 2
    return {m.home: h, m.away: a}


def league_phase_rank_bonus(competition: str, final_rank: int) -> float:
    """Bonus for final league-phase ranking (1–36)."""
    if final_rank > 24:
        return 0.0
    steps_9_24 = min(16, 25 - final_rank)   # rank 24→1 step … rank 9→16 steps
    steps_1_8 = max(0, 9 - final_rank)       # rank 8→1 … rank 1→8
    return steps_9_24 * LP_RANK_STEP_9_24[competition] \
        + steps_1_8 * LP_RANK_STEP_1_8[competition]


def truncate3(x: float) -> float:
    """UEFA truncates (not rounds) to three decimals."""
    return int(x * 1000 + 1e-9) / 1000
