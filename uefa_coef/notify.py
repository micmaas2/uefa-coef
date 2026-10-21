"""Push notifications via ntfy.sh when something happens to the focus association.

Usage: python3 -m uefa_coef.notify OLD_STAND.json NEW_STAND.json
Topic comes from env NTFY_TOPIC (GitHub secret); no topic → prints what it would send.
Events: NL match kicks off, NL goal (score change), NL full time, NL rank change.
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

NTFY = os.environ.get("NTFY_SERVER", "https://ntfy.sh")


def f3(x):
    return f"{x:+.3f}".replace(".", ",")


def key(m):
    return m["date"] + "|" + m["club"] + "|" + m["competition"]


def score(m):
    # "FC Porto 0-1 PSV Eindhoven" → "0-1"
    return next(t for t in m["match"].split() if "-" in t and t.replace("-", "").isdigit())


def events(old: dict, new: dict) -> list[tuple[str, str, str]]:
    """→ [(title, body, priority)]"""
    out = []
    f_old, f_new = old["focus"], new["focus"]
    nl = f_new["assoc"]
    old_m = {key(m): m for m in old.get("week_matches", [])}
    for m in new.get("week_matches", []):
        o = old_m.get(key(m))
        short = m["match"]
        if o is None or o["status"] == "pre":
            if m["status"] == "live":
                out.append(("⚽ Afgetrapt", f"{short}", "default"))
            elif m["status"] == "final":
                out.append(("🏁 Afgelopen", f"{short}  {nl} {f3(m['delta'])}", "default"))
            continue
        if score(o) != score(m):
            out.append(("⚽ GOAL" if m["status"] == "live" else "⚽ Score", f"{short} ({m['clock']})  {nl} nu {f3(m['delta'])}", "high"))
        if o["status"] == "live" and m["status"] == "final":
            out.append(("🏁 Afgelopen", f"{short}  {nl} {f3(m['delta'])}", "default"))
    if f_old["rank"] != f_new["rank"]:
        arrow = "▲" if f_new["rank"] < f_old["rank"] else "▼"
        out.append((f"{arrow} {nl} naar plek {f_new['rank']}",
                    f"was {f_old['rank']} · totaal {f_new['projected']:.3f}".replace(".", ","), "high"))
    # samenvatting bij laatste eindsignaal van de dag
    if any(t.startswith("🏁") for t, _, _ in out) and all(m["status"] == "final" for m in new.get("week_matches", [])):
        up, down = f_new.get("gap_up_to"), f_new.get("gap_down_to")
        out.append((f"Stand {nl}: #{f_new['rank']} · {f_new['projected']:.3f}".replace(".", ","),
                    f"deze week {f3(f_new['week_delta'])} · achter {up} {f_new['gap_up']:.3f} · voor {down} {f_new['gap_down']:.3f}".replace(".", ","),
                    "default"))
    return out


def send(topic: str, title: str, body: str, priority: str):
    req = urllib.request.Request(f"{NTFY}/{topic}", data=body.encode(), method="POST",
                                 headers={"Title": title, "Priority": priority, "Tags": "soccer",
                                          "Click": "https://github.com/micmaas2/uefa-coef/blob/main/stand.json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.status


def main(old_path: str, new_path: str):
    old = json.loads(Path(old_path).read_text())
    new = json.loads(Path(new_path).read_text())
    topic = os.environ.get("NTFY_TOPIC")
    for title, body, prio in events(old, new):
        # emoji zijn niet toegestaan in HTTP-headers → naar de body
        ascii_title = title.encode("ascii", "ignore").decode().strip() or "UEFA coef"
        emoji = title[:1] if not title[:1].isascii() else ""
        text = (emoji + " " if emoji else "") + body
        if topic:
            send(topic, ascii_title, text, prio)
            print("sent:", ascii_title, "|", text)
        else:
            print("would send:", ascii_title, "|", text)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
