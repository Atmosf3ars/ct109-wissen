# alpaca_universe_v1.py - volles US-Aktien-Universum fuer Tagesbars (inkl. inaktiver/gestrichener Titel, soweit Alpaca sie fuehrt). Daten bleiben auf dem PC.
# Aufruf:
#   python -u alpaca_universe_v1.py assets <Ausgabe-Ordner>                       -> schreibt <Ordner>\_assets_us.csv, druckt NUR Zaehlungen
#   python -u alpaca_universe_v1.py bars   <Ausgabe-Ordner> [--have <alpaca-daily>] [--group 40] [--rate 150] [--limit N]
#        -> laedt Tagesbars (SIP, adjustment=all, ab 2016-01-01, Ende hart 2026-06-30) fuer alle Symbole aus _assets_us.csv, die weder im Ausgabe-Ordner
#           noch im --have-Ordner (vorhandener Bestand) schon als <SYMBOL>.csv liegen; Wiederaufnahme: vorhandene Dateien/_nobars.txt werden uebersprungen.
# Schluessel NUR aus Umgebungsvariablen (APCA_API_KEY_ID / APCA_API_SECRET_KEY o. ae., Werte werden nie ausgegeben). Trading-API-Basis (Assets):
#   Standard https://paper-api.alpaca.markets, ueberschreibbar mit ALPACA_TRADING_BASE. Daten-API: data.alpaca.markets (Basic-Plan, 200 Aufrufe/min; Standard 150).
# Ausschluss: Boerse OTC, Namen mit Warrant/Right/Unit(s). Hartes Datenende 2026-06-30 (Bars ab 2026-07-01 werden verworfen).
# Chat-Ausgabe: nur Zaehlungen.  Eine Datei <SYMBOL>.csv: date,open,high,low,close,volume,trade_count,vwap
import sys, os, csv, json, time, re, urllib.request, urllib.error, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from alpaca_daily_v1 import keys, http_get, Throttle, fetch_symbol, CUT

DATA = "https://data.alpaca.markets/v2/stocks/bars"
EXCL_NAME = re.compile(r"\b(warrants?|rights?|units?)\b", re.I)

def trading_base():
    return os.environ.get("ALPACA_TRADING_BASE", "https://paper-api.alpaca.markets").rstrip("/")

def cmd_assets(outd, getter=http_get, hdr=None):
    os.makedirs(outd, exist_ok=True)
    if hdr is None:
        k, s = keys(); hdr = {"APCA-API-KEY-ID": k, "APCA-API-SECRET-KEY": s, "accept": "application/json"}
    allrows = {}
    for st in ("active", "inactive"):
        url = trading_base() + "/v2/assets?" + urllib.parse.urlencode({"status": st, "asset_class": "us_equity"})
        js = getter(url, hdr)
        print("Assets status=%s: %d" % (st, len(js)), flush=True)
        for a in js:
            sym = (a.get("symbol") or "").strip().upper()
            if not sym or " " in sym: continue
            allrows.setdefault(sym, a)
    keep = []; ex = {}; exc_otc = 0; exc_name = 0
    for sym, a in sorted(allrows.items()):
        exch = a.get("exchange") or ""
        if exch.upper() == "OTC": exc_otc += 1; continue
        if EXCL_NAME.search(a.get("name") or ""): exc_name += 1; continue
        keep.append((sym, exch, a.get("status", ""), a.get("tradable", ""), (a.get("name") or "").replace(",", " ")[:60]))
        ex[exch] = ex.get(exch, 0) + 1
    with open(os.path.join(outd, "_assets_us.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["symbol", "exchange", "status", "tradable", "name"]); w.writerows(keep)
    n_act = sum(1 for r in keep if r[2] == "active")
    print("Symbole gesamt (eindeutig): %d | ausgeschlossen OTC: %d, Warrant/Right/Unit: %d | behalten: %d (aktiv %d, inaktiv %d)"
          % (len(allrows), exc_otc, exc_name, len(keep), n_act, len(keep) - n_act))
    print("Boersen:", ", ".join("%s %d" % (k, v) for k, v in sorted(ex.items(), key=lambda x: -x[1])))
    return keep

def fetch_group(syms, hdr, thr, getter=http_get):
    """Mehrsymbol-Abruf; liefert {sym: rows} oder None bei 400/422 (dann Einzelabruf)."""
    out = {}; token = None
    for _ in range(400):
        q = {"symbols": ",".join(syms), "timeframe": "1Day", "start": "2016-01-01T00:00:00Z", "end": "2026-06-30T23:59:59Z",
             "adjustment": "all", "feed": "sip", "limit": "10000", "sort": "asc"}
        if token: q["page_token"] = token
        url = DATA + "?" + urllib.parse.urlencode(q)
        for attempt in range(6):
            thr.wait()
            try:
                js = getter(url, hdr); break
            except urllib.error.HTTPError as e:
                if e.code == 429: time.sleep(5 * (attempt + 1)); continue
                if e.code in (400, 404, 422): return None
                if e.code in (401, 403): sys.exit("Alpaca-Authentifizierung fehlgeschlagen (HTTP %d) - Abbruch." % e.code)
                time.sleep(3 * (attempt + 1))
            except Exception:
                time.sleep(3 * (attempt + 1))
        else:
            return None
        for sym, bars in (js.get("bars") or {}).items():
            for b in bars or []:
                d = b["t"][:10]
                if d >= CUT: continue
                out.setdefault(sym, []).append((d, b["o"], b["h"], b["l"], b["c"], b["v"], b.get("n", 0), b.get("vw", 0)))
        token = js.get("next_page_token")
        if not token: break
    return out

def write_sym(outd, sym, rows):
    with open(os.path.join(outd, sym.replace("/", "_") + ".csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["date", "open", "high", "low", "close", "volume", "trade_count", "vwap"]); w.writerows(rows)

def cmd_bars(outd, have="", group=40, rate=150.0, limit=0, getter=http_get, hdr=None):
    if hdr is None:
        k, s = keys(); hdr = {"APCA-API-KEY-ID": k, "APCA-API-SECRET-KEY": s, "accept": "application/json"}
    with open(os.path.join(outd, "_assets_us.csv"), newline="", encoding="utf-8") as f:
        syms = [r["symbol"] for r in csv.DictReader(f)]
    def have_set(p):
        return set(os.path.splitext(x)[0].upper() for x in os.listdir(p) if x.lower().endswith(".csv")) if p and os.path.isdir(p) else set()
    skip = have_set(outd) | have_set(have)
    nb = os.path.join(outd, "_nobars.txt")
    if os.path.exists(nb):
        with open(nb, encoding="utf-8") as f: skip |= set(x.strip() for x in f if x.strip())
    todo = [x for x in syms if x.replace("/", "_") not in skip]
    if limit: todo = todo[:limit]
    print("Symbole in Liste %d | schon vorhanden/leer %d | zu laden %d | Gruppen a %d" % (len(syms), len(syms) - len(todo), len(todo), group), flush=True)
    thr = Throttle(rate); ok = leer = fb = 0; t0 = time.time()
    for gi in range(0, len(todo), group):
        g = todo[gi:gi + group]
        res = fetch_group(g, hdr, thr, getter)
        if res is None:
            fb += 1; res = {}
            for sym in g:
                rows, st = fetch_symbol(sym, "2016-01-01", hdr, thr, getter)
                if st == "ok": res[sym] = rows
        for sym in g:
            rows = res.get(sym)
            if rows: write_sym(outd, sym, sorted(rows)); ok += 1
            else:
                leer += 1
                with open(nb, "a", encoding="utf-8") as f: f.write(sym + "\n")
        if (gi // group) % 10 == 9:
            print("[%5d s] %d/%d ok %d leer %d Einzel-Fallback-Gruppen %d" % (time.time() - t0, gi + len(g), len(todo), ok, leer, fb), flush=True)
    print("FERTIG: zu laden %d, ok %d, ohne Bars %d, Einzel-Fallback-Gruppen %d, Dauer %d s" % (len(todo), ok, leer, fb, time.time() - t0))

if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2 or a[0] not in ("assets", "bars"): sys.exit(__doc__)
    def opt(k, d, f=str): return f(a[a.index(k) + 1]) if k in a else d
    if a[0] == "assets": cmd_assets(a[1])
    else: cmd_bars(a[1], opt("--have", ""), opt("--group", 40, int), opt("--rate", 150.0, float), opt("--limit", 0, int))
