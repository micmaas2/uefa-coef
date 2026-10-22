"""Decide what the long-running job should do next.

Prints one line:  poll        → matches today still live/scheduled: keep polling
                  sleep N     → nothing pending; sleep N seconds (≤ MAX_SLEEP) then re-check
Exit code is always 0. The workflow chains a new run when it runs out of time, so the
system no longer depends on GitHub's (unreliable) cron to start on time.
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

DATA = Path(__file__).resolve().parent.parent / "data"
TZ = ZoneInfo("Europe/Amsterdam")
MAX_SLEEP = 4 * 3600          # keep well inside the 6 h job limit
LEAD = 10 * 60                # wake up 10 min before kick-off
DAILY_REFRESH_HOUR = 9        # once a day re-fetch fixtures (3 days ahead)


def next_action(now: datetime | None = None) -> tuple[str, int]:
    now = now or datetime.now(TZ)
    matches = json.loads((DATA / "matches.json").read_text())
    today = now.date().isoformat()
    if any(m["date"] == today and m["status"] != "final" for m in matches):
        return "poll", 0
    upcoming = []
    for m in matches:
        if m["status"] != "pre" or not m.get("time"):
            continue
        ko = datetime.fromisoformat(f"{m['date']}T{m['time']}").replace(tzinfo=TZ)
        if ko > now:
            upcoming.append(ko)
    refresh = now.replace(hour=DAILY_REFRESH_HOUR, minute=30, second=0, microsecond=0)
    if refresh <= now:
        refresh += timedelta(days=1)
    wake = min(upcoming + [refresh]) - timedelta(seconds=LEAD)
    secs = max(60, int((wake - now).total_seconds()))
    return "sleep", min(secs, MAX_SLEEP)


if __name__ == "__main__":
    a, n = next_action()
    print(a, n)
