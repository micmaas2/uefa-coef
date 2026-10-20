# UEFA-coëfficiënt tracker (PoC)

Drie lagen: **data → rekenkern → UI**. De UI (eerst Scriptable-widget, later SwiftUI)
leest alleen `stand.json`; de rekenkern weet niets van de UI.

```
uefa_coef/rules.py    UEFA-puntenregels (2/1/0, halvering voorrondes, bonustabel, afkappen op 3 dec.)
uefa_coef/engine.py   snapshot + delta → stand.json
data/baseline.json    UEFA-snapshot 15-10-2026 (4 vorige seizoenen + lopend seizoen, #clubs, club→land)
data/matches.json     wedstrijden ná de snapshot
widget/UEFA_Coefficient.js   Scriptable-widget
```

## Draaien
```
python3 -m uefa_coef.engine      # schrijft stand.json en print NL-regel
```

## Nieuwe uitslag toevoegen
Voeg een regel toe aan `data/matches.json`:
```json
{"date": "2026-10-23", "competition": "UEL", "stage": "LP",
 "home": "Feyenoord", "away": "Braga", "home_goals": 2, "away_goals": 0}
```
Stages: `Q1 Q2 Q3 PO` (halve punten) · `LP KPO R16 QF SF F`. Strafschoppen → `"decided_on_penalties": true`.
Onbekende club → KeyError; voeg hem toe aan `clubs` in baseline.json.

## Widget
1. Host `stand.json` ergens met een https-URL (GitHub raw, thuisserver, S3 …).
2. Scriptable → nieuw script → plak `widget/UEFA_Coefficient.js`.
3. Homescreen-widget (small/medium) → Script = dit script, **Parameter = URL van stand.json**.
Widget cachet de laatste goede versie en toont ⚠︎ als de fetch mislukt.

## Bekende beperkingen / TODO
- Baseline bevat top-12 landen; rest aanvullen uit uefa.com als je volledige stand wilt.
- Clubmap NED is een aanname (PSV, Ajax, Feyenoord, FC Twente, AZ, NEC) — check welke 6 clubs
  dit seizoen daadwerkelijk Europees spelen en pas `clubs` aan. Het aantal (6) is wel juist.
- Bonuspunten (league-phase-ranking, knockout-rondes) zitten in `rules.py` maar worden nog niet
  automatisch toegepast; dat hoort bij seizoenseinde / na de league phase.
- Volgende stap: `fetch.py` die uitslagen uit football-data.org haalt → matches.json, cron op thuisserver.
- Daarna: SwiftUI-app + WidgetKit op dezelfde `stand.json` (Codable-struct is 1-op-1 het JSON-schema).
