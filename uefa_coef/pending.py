"""Exit 0 when nothing is live or scheduled for today anymore (loop may stop), else 1."""
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

DATA = Path(__file__).resolve().parent.parent / "data"
now = datetime.now(ZoneInfo("Europe/Amsterdam"))
today = now.date().isoformat()
matches = json.loads((DATA / "matches.json").read_text())
pending = [m for m in matches if m["date"] == today and m["status"] != "final"]
for m in pending:
    print(f"pending: {m['home']} - {m['away']} {m.get('time','')} [{m['status']}]")
raise SystemExit(0 if not pending else 1)
