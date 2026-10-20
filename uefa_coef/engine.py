"""Snapshot + delta engine.

baseline.json  : UEFA snapshot (previous 4 seasons + current-season points so far,
                 number of clubs per association, club→association map).
matches.json   : matches played AFTER the snapshot date.
Output         : full ranking with per-match deltas for the Netherlands.

Later the baseline's current-season value can be replaced by a full
computation from all matches of the season (same engine, empty baseline season).
"""
import json
from collections import defaultdict
from pathlib import Path

from .rules import Match, match_points, truncate3

DATA = Path(__file__).resolve().parent.parent / "data"


def load_baseline(path=DATA / "baseline.json") -> dict:
    return json.loads(Path(path).read_text())


def load_matches(path=DATA / "matches.json") -> list[Match]:
    return [Match(**m) for m in json.loads(Path(path).read_text())]


def compute(baseline: dict, matches: list[Match], focus: str = "NED") -> dict:
    assoc = baseline["associations"]
    club_to_assoc = baseline["clubs"]

    raw_added = defaultdict(float)     # association → raw points added since snapshot
    focus_log = []

    for m in matches:
        pts = match_points(m)
        for club, p in pts.items():
            a = club_to_assoc.get(club)
            if a is None:
                raise KeyError(f"club '{club}' not in baseline club map")
            raw_added[a] += p
            if a == focus:
                n = assoc[a]["clubs"]
                focus_log.append({
                    "date": m.date, "competition": m.competition, "stage": m.stage,
                    "match": f"{m.home} {m.home_goals}-{m.away_goals} {m.away}",
                    "club": club, "raw": p, "delta": truncate3(p / n),
                })

    rows = []
    for code, a in assoc.items():
        n = a["clubs"]
        season = truncate3(a["season_snapshot"] + raw_added[code] / n)
        total = truncate3(sum(a["previous"]) + season)
        rows.append({
            "assoc": code, "name": a["name"], "clubs": n,
            "previous": a["previous"], "season": season, "total": total,
            "added_since_snapshot": truncate3(raw_added[code] / n),
        })
    rows.sort(key=lambda r: r["total"], reverse=True)
    for i, r in enumerate(rows, 1):
        r["rank"] = i

    idx = next(i for i, r in enumerate(rows) if r["assoc"] == focus)
    f = rows[idx]
    above = rows[idx - 1] if idx > 0 else None
    below = rows[idx + 1] if idx + 1 < len(rows) else None

    return {
        "snapshot_date": baseline["snapshot_date"],
        "cycle": baseline["cycle"],
        "last_match_date": max((m.date for m in matches), default=baseline["snapshot_date"]),
        "focus": {
            "assoc": focus, "rank": f["rank"], "total": f["total"], "season": f["season"],
            "clubs": f["clubs"],
            "gap_up": truncate3(above["total"] - f["total"]) if above else None,
            "gap_up_to": above["name"] if above else None,
            "gap_down": truncate3(f["total"] - below["total"]) if below else None,
            "gap_down_to": below["name"] if below else None,
            "log": focus_log,
        },
        "ranking": rows,
    }


def main(out=DATA.parent / "stand.json"):
    result = compute(load_baseline(), load_matches())
    Path(out).write_text(json.dumps(result, indent=2, ensure_ascii=False))
    f = result["focus"]
    print(f"{f['assoc']}  #{f['rank']}  total {f['total']:.3f}  season {f['season']:.3f}")
    for e in f["log"]:
        print(f"  {e['date']} {e['match']:<34} {e['club']:<10} +{e['delta']:.3f}")
    print(f"  gap to #{f['rank']-1} {f['gap_up_to']}: {f['gap_up']:.3f} | "
          f"lead on #{f['rank']+1} {f['gap_down_to']}: {f['gap_down']:.3f}")
    return result


if __name__ == "__main__":
    main()
