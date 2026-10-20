"""Fetch UCL/UEL/UECL results (incl. live scores) from ESPN's public scoreboard
and merge them into data/matches.json.

Usage: python3 -m uefa_coef.fetch [YYYYMMDD ...]   (default: baseline 'since' .. today)
No API key needed. Unofficial feed → a stage is inferred from the date
(league phase until end of January); override per match in matches.json if needed.
"""
import json
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
ESPN = "https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard?dates={d}"
LEAGUES = {"uefa.champions": "UCL", "uefa.europa": "UEL", "uefa.europa.conf": "UECL"}


def infer_stage(d: str) -> str:
    m = int(d[5:7])
    if m in (7, 8):
        return "Q3"            # summer = qualifying (halved); adjust manually if PO/Q1/Q2
    if m >= 9 or m == 1:
        return "LP"
    if m == 2:
        return "KPO"
    return {3: "R16", 4: "QF", 5: "SF", 6: "F"}.get(m, "LP")


def get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "uefa-coef-poc/0.1"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def fetch_day(yyyymmdd: str, clubs: dict) -> tuple[list[dict], set[str]]:
    out, unmapped = [], set()
    for league, comp in LEAGUES.items():
        try:
            data = get(ESPN.format(league=league, d=yyyymmdd))
        except Exception as e:  # feed hiccup → skip this league for now
            print(f"  warn {comp} {yyyymmdd}: {e}", file=sys.stderr)
            continue
        for ev in data.get("events", []):
            c = ev["competitions"][0]
            home = next(t for t in c["competitors"] if t["homeAway"] == "home")
            away = next(t for t in c["competitors"] if t["homeAway"] == "away")
            hn, an = home["team"]["displayName"], away["team"]["displayName"]
            if hn not in clubs and an not in clubs:
                continue                      # nobody we track
            for n in (hn, an):
                if n not in clubs:
                    unmapped.add(n)
            st = c["status"]["type"]
            status = "final" if st.get("completed") else ("live" if st["state"] == "in" else "pre")
            d = ev["date"][:10]
            out.append({
                "id": ev["id"], "date": d, "competition": comp, "stage": infer_stage(d),
                "home": hn, "away": an,
                "home_goals": int(home.get("score") or 0), "away_goals": int(away.get("score") or 0),
                "status": status, "clock": st.get("shortDetail", ""),
                "decided_on_penalties": False,
            })
    return out, unmapped


def main(days: list[str] | None = None):
    clubs = {k: v for k, v in json.loads((DATA / "clubs.json").read_text()).items() if not k.startswith("_")}
    baseline = json.loads((DATA / "baseline.json").read_text())
    path = DATA / "matches.json"
    existing = {m["id"]: m for m in json.loads(path.read_text()) if "id" in m} if path.exists() else {}

    if not days:
        start = date.fromisoformat(baseline["since"])
        today = datetime.now(timezone.utc).date()
        days = [(start + timedelta(i)).strftime("%Y%m%d") for i in range((today - start).days + 1)]

    unmapped_all = set()
    for d in days:
        matches, unmapped = fetch_day(d, clubs)
        unmapped_all |= unmapped
        for m in matches:
            old = existing.get(m["id"])
            if old and old.get("stage_override"):
                m["stage"] = old["stage"]; m["stage_override"] = True
            if old and old.get("decided_on_penalties"):
                m["decided_on_penalties"] = True
            existing[m["id"]] = m

    rows = sorted(existing.values(), key=lambda m: (m["date"], m["id"]))
    path.write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    (DATA / "unmapped.json").write_text(json.dumps(sorted(unmapped_all), indent=1, ensure_ascii=False))
    live = [m for m in rows if m["status"] == "live"]
    print(f"{len(rows)} matches stored, {len(live)} live, {len(unmapped_all)} unmapped clubs")
    for m in live:
        print(f"  LIVE {m['home']} {m['home_goals']}-{m['away_goals']} {m['away']} ({m['clock']})")


if __name__ == "__main__":
    main(sys.argv[1:] or None)
