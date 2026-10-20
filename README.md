# UEFA-coëfficiënt tracker (PoC)

Drie lagen: **data → rekenkern → UI**. De UI (eerst Scriptable-widget, later SwiftUI)
leest alleen `stand.json`; de rekenkern weet niets van de UI.

```
uefa_coef/rules.py    UEFA-puntenregels (2/1/0, halvering voorrondes, bonustabel, afkappen op 3 dec.)
uefa_coef/fetch.py    haalt uitslagen + live scores (ESPN-scorebord, geen key) → data/matches.json
uefa_coef/engine.py   snapshot + delta → stand.json (confirmed + projected, venster NL ±2, live-lijst)
data/baseline.json    UEFA-snapshot 15-10-2026 (4 vorige seizoenen + lopend seizoen, #clubs)
data/clubs.json       clubnaam (zoals de feed hem spelt) → land; onbekende clubs komen in data/unmapped.json
data/matches.json     wedstrijden sinds de snapshot, status pre | live | final (auto-beheerd)
widget/UEFA_Coefficient.js   Scriptable-widget: tabel NL ±2, live-delta, ● LIVE
.github/workflows/update.yml  draait fetch+engine elke 5 min op speelavonden, commit bij wijziging
```

## Draaien
```
python3 -m uefa_coef.fetch       # uitslagen sinds baseline.since ophalen (of: fetch 20261022)
python3 -m uefa_coef.engine      # schrijft stand.json, print venster NL ±2
```
Live: een wedstrijd met status `live` telt mee in `projected` op basis van de huidige stand,
`total` bevat alleen afgelopen wedstrijden. De widget toont `projected` zolang er iets live is.

Stage wordt uit de datum afgeleid (LP t/m januari). Correctie: zet in matches.json
`"stage": "PO", "stage_override": true` of `"decided_on_penalties": true`; fetch bewaart dat.

## Widget
1. Host `stand.json` ergens met een https-URL (GitHub raw, thuisserver, S3 …).
2. Scriptable → nieuw script → plak `widget/UEFA_Coefficient.js`.
3. Homescreen-widget (small/medium) → Script = dit script, **Parameter = URL van stand.json**.
Widget cachet de laatste goede versie en toont ⚠︎ als de fetch mislukt.

## Bekende beperkingen / TODO
- Baseline bevat top-12 landen; rest aanvullen uit uefa.com als je volledige stand wilt.
- clubs.json is een startset; check `data/unmapped.json` na een speelronde en vul aan.
- ESPN-feed is onofficieel; bij wijziging van het JSON-formaat breekt fetch.py (engine en widget niet).
- iOS bepaalt zelf hoe vaak een widget ververst (vaak 15–30 min, soms langer). Echt live op je
  scherm = Live Activity / Dynamic Island, en dat is precies waar de SwiftUI-stap voor is.
- Bonuspunten (league-phase-ranking, knockout-rondes) zitten in `rules.py` maar worden nog niet
  automatisch toegepast; dat hoort bij seizoenseinde / na de league phase.
- Daarna: SwiftUI-app + WidgetKit op dezelfde `stand.json` (Codable-struct is 1-op-1 het JSON-schema).
