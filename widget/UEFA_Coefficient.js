// Scriptable widget: UEFA-landencoëfficiënt — Nederland en de 2 landen erboven/eronder.
// Leest stand.json uit de repo (wordt op wedstrijdavonden elke paar minuten ververst).
// Widget-parameter is optioneel (alternatieve URL).

const URL = args.widgetParameter || "https://raw.githubusercontent.com/micmaas2/uefa-coef/main/stand.json";
const fm = FileManager.local();
const CACHE = fm.joinPath(fm.cacheDirectory(), "uefa_stand.json");

const C = {
  bg1: new Color("#101a2e"), bg2: new Color("#1d2b4a"),
  text: Color.white(), dim: new Color("#9fb3d9"), faint: new Color("#6f82a8"),
  up: new Color("#7ee787"), down: new Color("#ff8a80"), live: new Color("#ff4d4f"),
  nl: new Color("#ff7a00"),
};

async function loadStand() {
  try {
    const req = new Request(URL + "?t=" + Date.now());   // omzeil CDN-cache
    req.timeoutInterval = 10;
    const data = await req.loadJSON();
    fm.writeString(CACHE, JSON.stringify(data));
    return { data, stale: false };
  } catch (e) {
    if (fm.fileExists(CACHE)) return { data: JSON.parse(fm.readString(CACHE)), stale: true };
    throw e;
  }
}

const f3 = x => (x == null ? "–" : x.toFixed(3).replace(".", ","));
const signed = x => (x > 0 ? "+" : "") + f3(x);

function row(stack, r, isFocus, live) {
  const s = stack.addStack();
  s.centerAlignContent();
  const arrow = r.rank_change > 0 ? "▲" : r.rank_change < 0 ? "▼" : " ";
  const rank = s.addText(String(r.rank).padStart(2, " ") + arrow);
  rank.font = Font.boldMonospacedSystemFont(11);
  rank.textColor = r.rank_change > 0 ? C.up : r.rank_change < 0 ? C.down : (isFocus ? C.nl : C.dim);
  s.addSpacer(6);
  const name = s.addText(r.name);
  name.font = isFocus ? Font.boldSystemFont(12) : Font.systemFont(12);
  name.textColor = isFocus ? C.nl : C.text;
  name.lineLimit = 1;
  s.addSpacer();
  const delta = r.today_delta;           // t.o.v. stand om middernacht
  if (r.played_today) {                  // gespeeld → altijd tonen, ook +0,000
    const d = s.addText(signed(delta));
    d.font = Font.mediumMonospacedSystemFont(10);
    d.textColor = delta > 0 ? C.up : delta < 0 ? C.down : C.dim;
    s.addSpacer(6);
  }
  const tot = s.addText(f3(r.projected));   // = total als er niets live is
  tot.font = Font.boldMonospacedSystemFont(12);
  tot.textColor = isFocus ? C.nl : C.text;
}

function build(stand, stale) {
  const f = stand.focus, live = stand.live;
  const w = new ListWidget();
  w.setPadding(12, 14, 10, 14);
  const g = new LinearGradient();
  g.colors = [C.bg1, C.bg2]; g.locations = [0, 1];
  w.backgroundGradient = g;

  // kop
  const head = w.addStack(); head.centerAlignContent();
  const t = head.addText("UEFA coëfficiënt");
  t.font = Font.semiboldSystemFont(11); t.textColor = C.dim;
  head.addSpacer();
  if (live) {
    const dot = head.addText("● LIVE");
    dot.font = Font.boldSystemFont(10); dot.textColor = C.live;
  } else {
    const d = head.addText(stand.focus.today_delta ? "Δ vs 0:00" : "t/m " + stand.last_match_date);
    d.font = Font.systemFont(9); d.textColor = C.faint;
  }

  w.addSpacer(6);
  const small = config.widgetFamily === "small";
  const rows = small ? stand.window.filter(r => Math.abs(r.rank - f.rank) <= 1) : stand.window;
  for (const r of rows) {
    row(w, r, r.assoc === f.assoc, live);
    w.addSpacer(2);
  }

  // voet: NL-regel van vanavond + gaten
  w.addSpacer(4);
  if (live && stand.live_matches.length) {
    const nlLive = stand.live_matches.filter(m => m.assocs.includes(f.assoc));
    const pick = (nlLive.length ? nlLive : stand.live_matches)[0];
    const l = w.addText(pick.match + "  " + pick.clock);
    l.font = Font.systemFont(9); l.textColor = C.dim; l.lineLimit = 1;
  } else {
    const l = w.addText("achterstand op " + f.gap_up_to + " " + f3(f.gap_up) + " · voorsprong op " + f.gap_down_to + " " + f3(f.gap_down));
    l.font = Font.systemFont(9); l.textColor = C.dim; l.lineLimit = 1;
  }
  if (stale) {
    const s = w.addText("⚠︎ cache"); s.font = Font.systemFont(8); s.textColor = C.faint;
  }
  // iOS bepaalt het echte interval; dit is een verzoek.
  w.refreshAfterDate = new Date(Date.now() + (live ? 5 : 60) * 60 * 1000);
  return w;
}

let widget;
try {
  const { data, stale } = await loadStand();
  widget = build(data, stale);
} catch (e) {
  widget = new ListWidget();
  const t = widget.addText("stand.json niet bereikbaar\n" + e);
  t.font = Font.systemFont(10);
}
if (config.runsInWidget) Script.setWidget(widget);
else await widget.presentMedium();
Script.complete();
