// Scriptable widget: UEFA-landencoëfficiënt Nederland
// Setup: Scriptable → nieuw script → plak dit → homescreen-widget (small of medium)
//        → Script: dit script, Parameter: URL van stand.json
//        (bijv. https://raw.githubusercontent.com/<user>/<repo>/main/stand.json)

const URL = args.widgetParameter || "https://example.com/stand.json";
const CACHE = FileManager.local().joinPath(FileManager.local().cacheDirectory(), "uefa_stand.json");

async function loadStand() {
  const fm = FileManager.local();
  try {
    const req = new Request(URL);
    req.timeoutInterval = 10;
    const data = await req.loadJSON();
    fm.writeString(CACHE, JSON.stringify(data));
    return { data, stale: false };
  } catch (e) {
    if (fm.fileExists(CACHE)) return { data: JSON.parse(fm.readString(CACHE)), stale: true };
    throw e;
  }
}

function fmt(x) { return x == null ? "–" : x.toFixed(3).replace(".", ","); }

function buildWidget(stand, stale) {
  const f = stand.focus;
  const w = new ListWidget();
  w.setPadding(14, 14, 12, 14);
  w.backgroundGradient = (() => {
    const g = new LinearGradient();
    g.colors = [new Color("#101a2e"), new Color("#1d2b4a")];
    g.locations = [0, 1];
    return g;
  })();

  const head = w.addStack();
  head.centerAlignContent();
  const t = head.addText("UEFA coëfficiënt · NED");
  t.font = Font.semiboldSystemFont(11); t.textColor = new Color("#9fb3d9");
  head.addSpacer();
  const rank = head.addText("#" + f.rank);
  rank.font = Font.boldSystemFont(16); rank.textColor = Color.white();

  w.addSpacer(4);
  const total = w.addText(fmt(f.total));
  total.font = Font.boldMonospacedSystemFont(30); total.textColor = Color.white();
  total.minimumScaleFactor = 0.6;

  const season = w.addText("seizoen " + fmt(f.season) + " · " + f.clubs + " clubs");
  season.font = Font.systemFont(10); season.textColor = new Color("#9fb3d9");

  w.addSpacer(6);
  const up = w.addText("↑ " + f.gap_up_to + "  −" + fmt(f.gap_up));
  up.font = Font.mediumSystemFont(11); up.textColor = new Color("#ffb86b");
  const down = w.addText("↓ " + f.gap_down_to + "  +" + fmt(f.gap_down));
  down.font = Font.mediumSystemFont(11); down.textColor = new Color("#7ee787");

  const last = f.log[f.log.length - 1];
  if (last && config.widgetFamily !== "small") {
    w.addSpacer(6);
    const l = w.addText("Laatst: " + last.match + "  +" + fmt(last.delta));
    l.font = Font.systemFont(10); l.textColor = new Color("#c9d4ea"); l.lineLimit = 1;
  }

  w.addSpacer();
  const foot = w.addText((stale ? "⚠︎ cache · " : "") + "t/m " + stand.last_match_date);
  foot.font = Font.systemFont(8); foot.textColor = new Color("#6f82a8");
  w.refreshAfterDate = new Date(Date.now() + 60 * 60 * 1000); // ~ieder uur
  return w;
}

let widget;
try {
  const { data, stale } = await loadStand();
  widget = buildWidget(data, stale);
} catch (e) {
  widget = new ListWidget();
  const t = widget.addText("stand.json niet bereikbaar\n" + URL);
  t.font = Font.systemFont(10);
}

if (config.runsInWidget) Script.setWidget(widget);
else await widget.presentMedium();
Script.complete();
