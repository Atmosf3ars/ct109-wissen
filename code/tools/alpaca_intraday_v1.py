# alpaca_intraday_v1.py - ORB Phase 0c: erste 5-Minuten-Kerze (09:30-09:35 ET) aller Eligible-Symbole je Handelstag. Daten bleiben auf dem PC.
# Aufruf:
#   python -u alpaca_intraday_v1.py first --daily <Ordner1> [--daily <Ordner2> ...] --out <Ausgabe-Ordner> [--from 2016-01-04] [--to 2019-12-31] [--rate 150] [--chunk 400]
#   python -u alpaca_intraday_v1.py elig  --daily <Ordner1> [--daily <Ordner2> ...]      (nur Zaehlung der Eligible-Symbol-Tage, kein Abruf)
# Eligible = gleiche Vorab-Filter wie orb_count_v2.py (Vortagesschluss >= 5 USD, ATR14 >= 0,5 USD, Vol14 >= 1 Mio., Luecke zum Vortag <= 5 Kalendertage).
# Standard-Fenster ist das ENTWICKLUNGSFENSTER (bis 2019-12-31). Das Testfenster ab 2020-01-01 wird erst nach Freeze geholt (--to > 2019-12-31 verlangt --allow-test).
# Hartes Datenende 2026-06-30. Preise/Volumen split-bereinigt (adjustment=split), SIP-Feed. Schluessel nur aus Umgebungsvariablen (Werte nie ausgegeben).
# Ausgabe: <out>\first5_<YYYY-MM>.csv (date,symbol,open,high,low,close,volume,trade_count,vwap); <out>\_done_days.txt (Wiederaufnahme).
# Chat-Ausgabe: nur Zaehlungen (Tage, Symbole, Bars je Jahr). Keine Rendite, kein Vorzeichen einer Zielgroesse.
import sys, os, csv, time, urllib.request, urllib.error, urllib.parse
from datetime import date, timedelta
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from alpaca_daily_v1 import keys, http_get, Throttle

CUT = "2026-07-01"; TEST_START = "2020-01-01"
P_MIN, ATR_MIN, VOL_MIN, NATR = 5.0, 0.5, 1_000_000.0, 14
DATA = "https://data.alpaca.markets/v2/stocks/bars"

def nth_sunday(y, m, n):
    d = date(y, m, 1)
    d += timedelta(days=(6 - d.weekday()) % 7)
    return d + timedelta(weeks=n - 1)

def et_offset(d):
    """UTC-Offset der US-Ostkueste am Datum d (Sommerzeit: 2. Sonntag im Maerz bis 1. Sonntag im November, ab 2007)."""
    return "-04:00" if nth_sunday(d.year, 3, 2) <= d < nth_sunday(d.year, 11, 1) else "-05:00"

def load_daily(path):
    ds, o, h, l, c, v = [], [], [], [], [], []
    with open(path, newline="") as f:
        r = csv.reader(f); next(r, None)
        for row in r:
            if len(row) < 6 or row[0] >= CUT: continue
            try: oo, hh, ll, cc, vv = float(row[1]), float(row[2]), float(row[3]), float(row[4]), float(row[5])
            except ValueError: continue
            if not (oo > 0 and hh > 0 and ll > 0 and cc > 0): continue
            ds.append(row[0]); o.append(oo); h.append(hh); l.append(ll); c.append(cc); v.append(vv)
    return np.array(ds, dtype="datetime64[D]"), np.array(o), np.array(h), np.array(l), np.array(c), np.array(v)

def eligible(folders):
    """liefert {datum(str): [symbol, ...]} (Reihenfolge deterministisch); erster Ordner gewinnt bei doppelten Symbolen."""
    seen = set(); out = {}
    for fo in folders:
        for fn in sorted(os.listdir(fo)):
            if not fn.lower().endswith(".csv") or fn.startswith("_") or fn.upper() in seen: continue
            seen.add(fn.upper()); sym = fn[:-4]
            d, o, h, l, c, v = load_daily(os.path.join(fo, fn)); n = len(c)
            if n < NATR + 3: continue
            pc = c[:-1]
            tr = np.maximum.reduce([h[1:] - l[1:], np.abs(h[1:] - pc), np.abs(l[1:] - pc)])
            cs = np.concatenate([[0.0], np.cumsum(tr)]); cv = np.concatenate([[0.0], np.cumsum(v)])
            i = np.arange(NATR + 1, n)
            atr = (cs[i - 1] - cs[i - 1 - NATR]) / NATR; avgv = (cv[i] - cv[i - NATR]) / NATR
            ok = (c[i - 1] >= P_MIN) & (atr >= ATR_MIN) & (avgv >= VOL_MIN) & ((d[i] - d[i - 1]).astype(int) <= 5) & (atr > 0)
            for k in np.nonzero(ok)[0]:
                out.setdefault(str(d[i][k]), []).append(sym)
    return out

def fetch_first(day, syms, hdr, thr, getter=http_get):
    """erste 5-Min-Bar je Symbol; teilt bei HTTP 400/422 die Liste (ein ungueltiges Symbol soll nicht alles blockieren)."""
    y, m, dd = map(int, day.split("-")); off = et_offset(date(y, m, dd))
    q = {"symbols": ",".join(syms), "timeframe": "5Min", "start": "%sT09:30:00%s" % (day, off), "end": "%sT09:34:59%s" % (day, off),
         "adjustment": "split", "feed": "sip", "limit": "10000", "sort": "asc"}
    url = DATA + "?" + urllib.parse.urlencode(q); js = None
    for attempt in range(6):
        thr.wait()
        try:
            js = getter(url, hdr); break
        except urllib.error.HTTPError as e:
            if e.code == 429: time.sleep(5 * (attempt + 1)); continue
            if e.code in (400, 404, 422):
                if len(syms) == 1: return [], 1
                mid = len(syms) // 2
                a, ea = fetch_first(day, syms[:mid], hdr, thr, getter); b, eb = fetch_first(day, syms[mid:], hdr, thr, getter)
                return a + b, ea + eb
            if e.code in (401, 403): sys.exit("Alpaca-Authentifizierung fehlgeschlagen (HTTP %d) - Abbruch." % e.code)
            time.sleep(3 * (attempt + 1))
        except Exception:
            time.sleep(3 * (attempt + 1))
    if js is None: return None, 0
    rows = []
    for sym, bars in (js.get("bars") or {}).items():
        for b in bars or []:
            rows.append((day, sym, b["o"], b["h"], b["l"], b["c"], b["v"], b.get("n", 0), b.get("vw", 0)))
    token = js.get("next_page_token")
    if token: return None, 0   # sollte bei <= chunk Symbolen nicht vorkommen; Tag wird nicht als erledigt markiert
    return rows, 0

def cmd_first(folders, outd, dfrom, dto, rate=150.0, chunk=400, allow_test=False, getter=http_get, hdr=None):
    if dto >= TEST_START and not allow_test:
        sys.exit("Testfenster (ab %s) gesperrt bis zum Freeze: --to <= 2019-12-31 oder --allow-test erst nach GO." % TEST_START)
    if hdr is None:
        k, s = keys(); hdr = {"APCA-API-KEY-ID": k, "APCA-API-SECRET-KEY": s, "accept": "application/json"}
    os.makedirs(outd, exist_ok=True)
    el = eligible(folders)
    days = sorted(d for d in el if dfrom <= d <= dto and d < CUT)
    donep = os.path.join(outd, "_done_days.txt")
    done = set(x.strip() for x in open(donep, encoding="utf-8")) if os.path.exists(donep) else set()
    todo = [d for d in days if d not in done]
    print("Handelstage im Fenster %s..%s: %d | schon erledigt %d | zu holen %d | Eligible-Symbol-Tage gesamt %d"
          % (dfrom, dto, len(days), len(days) - len(todo), len(todo), sum(len(el[d]) for d in days)), flush=True)
    thr = Throttle(rate); t0 = time.time(); nb = 0; ne = 0; nfail = 0; byyear = {}
    for di, day in enumerate(todo, 1):
        syms = el[day]; rows = []; ok = True
        for ci in range(0, len(syms), chunk):
            r, e = fetch_first(day, syms[ci:ci + chunk], hdr, thr, getter)
            if r is None: ok = False; break
            rows += r; ne += e
        if not ok: nfail += 1; continue
        ym = day[:7]
        with open(os.path.join(outd, "first5_%s.csv" % ym), "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if f.tell() == 0: w.writerow(["date", "symbol", "open", "high", "low", "close", "volume", "trade_count", "vwap"])
            w.writerows(sorted(rows))
        with open(donep, "a", encoding="utf-8") as f: f.write(day + "\n")
        nb += len(rows); byyear[day[:4]] = byyear.get(day[:4], 0) + len(rows)
        if di % 50 == 0: print("[%5d s] Tage %d/%d Bars %d ungueltige Symbole %d Fehltage %d" % (time.time() - t0, di, len(todo), nb, ne, nfail), flush=True)
    print("FERTIG: Tage geholt %d, Bars %d, ungueltige Einzelsymbole %d, Fehltage (erneut starten) %d, Dauer %d s" % (len(todo) - nfail, nb, ne, nfail, time.time() - t0))
    print("Bars je Jahr:", ", ".join("%s %d" % (k, v) for k, v in sorted(byyear.items())))

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] not in ("first", "elig"): sys.exit(__doc__)
    folders = [a[i + 1] for i, x in enumerate(a) if x == "--daily"]
    def opt(k, d, f=str): return f(a[a.index(k) + 1]) if k in a else d
    if a[0] == "elig":
        el = eligible(folders); ys = {}
        for d, s in el.items(): ys[d[:4]] = ys.get(d[:4], 0) + len(s)
        print("Eligible-Symbol-Tage gesamt %d, Tage %d" % (sum(len(v) for v in el.values()), len(el)))
        print("je Jahr:", ", ".join("%s %d" % (k, v) for k, v in sorted(ys.items())))
    else:
        cmd_first(folders, opt("--out", ""), opt("--from", "2016-01-04"), opt("--to", "2019-12-31"), opt("--rate", 150.0, float), opt("--chunk", 400, int), "--allow-test" in a)
