"""Snapshot + delta engine with live (provisional) scores.

baseline.json : UEFA snapshot (4 previous seasons + current season to date, #clubs)
clubs.json    : club name (as the feed spells it) → association
matches.json  : matches since the snapshot, each with status pre | live | final
stand.json    : confirmed total (finals only), projected total (finals + live at
                current score), a ±2 window around the focus association, live list.
"""
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .rules import Match, match_points, truncate3

DATA = Path(__file__).resolve().parent.parent / "data"
WINDOW = 2
TZ = ZoneInfo("Europe/Amsterdam")
MATCH_FIELDS = {"date", "competition", "stage", "home", "away", "home_goals", "away_goals", "decided_on_penalties"}


def load_json(name):
    return json.loads((DATA / name).read_text())


def compute(baseline: dict, clubs: dict, matches: list[dict], focus: str = "NED") -> dict:
    assoc = baseline["associations"]
    confirmed = defaultdict(float)   # raw points from finished matches
    live_raw = defaultdict(float)    # raw points from matches in play (current score)
    today_raw = defaultdict(float)   # raw points (final+live) since local midnight
    log, live_list = [], []
    latest_date = max((m["date"] for m in matches if m["status"] != "pre"), default=None)
    today = datetime.now(TZ).date().isoformat()
    played_today = set()             # associations with a match today (live or final)

    for m in matches:
        if m["status"] == "pre":
            continue
        pts = match_points(Match(**{k: m[k] for k in MATCH_FIELDS}))
        for club, p in pts.items():
            a = clubs.get(club)
            if a is None or a not in assoc:
                continue
            (live_raw if m["status"] == "live" else confirmed)[a] += p
            if m["date"] == today:
                today_raw[a] += p
                played_today.add(a)
            if a == focus:
                log.append({"date": m["date"], "competition": m["competition"], "status": m["status"],
                            "match": f"{m['home']} {m['home_goals']}-{m['away_goals']} {m['away']}",
                            "club": club, "delta": truncate3(p / assoc[a]["clubs"])})
        if m["status"] == "live" and any(clubs.get(c) in assoc for c in (m["home"], m["away"])):
            live_list.append({"competition": m["competition"], "clock": m.get("clock", ""),
                              "match": f"{m['home']} {m['home_goals']}-{m['away_goals']} {m['away']}",
                              "assocs": sorted({clubs.get(c) for c in (m["home"], m["away"]) if clubs.get(c) in assoc})})

    rows = []
    for code, a in assoc.items():
        n, prev = a["clubs"], sum(a["previous"])
        season_conf = truncate3(a["season_snapshot"] + confirmed[code] / n)
        season_proj = truncate3(a["season_snapshot"] + (confirmed[code] + live_raw[code]) / n)
        rows.append({"assoc": code, "name": a["name"], "clubs": n,
                     "season": season_conf, "total": truncate3(prev + season_conf),
                     "projected": truncate3(prev + season_proj),
                     "live_delta": truncate3(live_raw[code] / n),
                     "today_delta": truncate3(today_raw[code] / n),
                     "played_today": code in played_today})
    rows.sort(key=lambda r: r["projected"], reverse=True)
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    by_conf = sorted(rows, key=lambda r: r["total"], reverse=True)
    for i, r in enumerate(by_conf, 1):
        r["rank_confirmed"] = i
    # stand om middernacht = projected minus alles van vandaag
    for r in rows:
        r["midnight_total"] = truncate3(r["projected"] - r["today_delta"])
    by_midnight = sorted(rows, key=lambda r: r["midnight_total"], reverse=True)
    for i, r in enumerate(by_midnight, 1):
        r["rank_midnight"] = i
        r["rank_change"] = r["rank_midnight"] - r["rank"]   # +1 = één plek gestegen

    idx = next(i for i, r in enumerate(rows) if r["assoc"] == focus)
    window = rows[max(0, idx - WINDOW): idx + WINDOW + 1]
    f = rows[idx]
    above = rows[idx - 1] if idx else None
    below = rows[idx + 1] if idx + 1 < len(rows) else None

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "snapshot_date": baseline["snapshot_date"], "cycle": baseline["cycle"],
        "last_match_date": latest_date or baseline["snapshot_date"],
        "today": today,
        "live": bool(live_list),
        "focus": {"assoc": focus, "rank": f["rank"], "rank_confirmed": f["rank_confirmed"],
                  "rank_midnight": f["rank_midnight"], "rank_change": f["rank_change"],
                  "total": f["total"], "projected": f["projected"], "season": f["season"], "clubs": f["clubs"],
                  "midnight_total": f["midnight_total"],
                  "live_delta": f["live_delta"], "today_delta": f["today_delta"],
                  "gap_up": truncate3(above["projected"] - f["projected"]) if above else None,
                  "gap_up_to": above["name"] if above else None,
                  "gap_down": truncate3(f["projected"] - below["projected"]) if below else None,
                  "gap_down_to": below["name"] if below else None,
                  "log": log},
        "window": window,
        "live_matches": live_list,
        "ranking": rows,
    }


def main(out=DATA.parent / "stand.json"):
    clubs = {k: v for k, v in load_json("clubs.json").items() if not k.startswith("_")}
    result = compute(load_json("baseline.json"), clubs, load_json("matches.json"))
    Path(out).write_text(json.dumps(result, indent=1, ensure_ascii=False))
    print(f"{'LIVE ' if result['live'] else ''}t/m {result['last_match_date']}")
    for r in result["window"]:
        mark = "→" if r["assoc"] == result["focus"]["assoc"] else " "
        print(f"{mark}{r['rank']:>2} {r['name']:<12} {r['projected']:8.3f}  vandaag {r['today_delta']:+.3f}  rang {r['rank_change']:+d}")
    for lm in result["live_matches"]:
        print(f"   LIVE {lm['match']} ({lm['clock']})")
    return result


if __name__ == "__main__":
    main()
