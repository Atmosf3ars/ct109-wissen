# alpaca_day5_v1.py - ORB Phase 0c: Ganztags-5-Min-Bars (09:30-16:00 ET) nur fuer die ausgewaehlten Symbol-Tage. Daten bleiben auf dem PC.
# Aufruf: python -u alpaca_day5_v1.py <auswahl-csv> --out <Ausgabe-Ordner> [--rate 150] [--chunk 60]
# Auswahl-csv aus orb_select_v1.py (date,symbol,rank,rv5). Entwicklungsfenster: Tage > 2019-12-31 werden abgelehnt (--allow-test erst nach Freeze/GO).
# adjustment=split, feed=sip. Ausgabe: <out>\day5_<YYYY-MM>.csv (date,symbol,t,open,high,low,close,volume,trade_count,vwap; t = UTC-Zeitstempel der Bar);
# <out>\_done_days.txt (Wiederaufnahme). Chat: nur Zaehlungen.
import sys, os, csv, time, urllib.request, urllib.error, urllib.parse
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from alpaca_daily_v1 import keys, http_get, Throttle
from alpaca_intraday_v1 import et_offset, TEST_START, CUT
DATA = "https://data.alpaca.markets/v2/stocks/bars"

def fetch_day(day, syms, hdr, thr, getter=http_get):
    y, m, dd = map(int, day.split("-")); off = et_offset(date(y, m, dd))
    rows = []; token = None; bad = 0
    for _ in range(50):
        q = {"symbols": ",".join(syms), "timeframe": "5Min", "start": "%sT09:30:00%s" % (day, off), "end": "%sT15:59:59%s" % (day, off),
             "adjustment": "split", "feed": "sip", "limit": "10000", "sort": "asc"}
        if token: q["page_token"] = token
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
                    a, ea = fetch_day(day, syms[:mid], hdr, thr, getter); b, eb = fetch_day(day, syms[mid:], hdr, thr, getter)
                    if a is None or b is None: return None, 0
                    return a + b, ea + eb
                if e.code in (401, 403): sys.exit("Alpaca-Authentifizierung fehlgeschlagen (HTTP %d) - Abbruch." % e.code)
                time.sleep(3 * (attempt + 1))
            except Exception:
                time.sleep(3 * (attempt + 1))
        if js is None: return None, 0
        for sym, bars in (js.get("bars") or {}).items():
            for b in bars or []:
                rows.append((day, sym, b["t"], b["o"], b["h"], b["l"], b["c"], b["v"], b.get("n", 0), b.get("vw", 0)))
        token = js.get("next_page_token")
        if not token: break
    return rows, bad

def main(selp, outd, rate=150.0, chunk=60, allow_test=False, getter=http_get, hdr=None):
    sel = {}
    with open(selp, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f): sel.setdefault(r["date"], []).append(r["symbol"])
    if not allow_test and any(d >= TEST_START for d in sel):
        sys.exit("Auswahl enthaelt Tage ab %s (Testfenster) - gesperrt bis Freeze/GO (--allow-test)." % TEST_START)
    if hdr is None:
        k, s = keys(); hdr = {"APCA-API-KEY-ID": k, "APCA-API-SECRET-KEY": s, "accept": "application/json"}
    os.makedirs(outd, exist_ok=True)
    donep = os.path.join(outd, "_done_days.txt")
    done = set(x.strip() for x in open(donep, encoding="utf-8")) if os.path.exists(donep) else set()
    todo = [d for d in sorted(sel) if d not in done and d < CUT]
    print("Tage in Auswahl %d | erledigt %d | zu holen %d | Symbol-Tage %d" % (len(sel), len(sel) - len(todo), len(todo), sum(len(v) for v in sel.values())), flush=True)
    thr = Throttle(rate); t0 = time.time(); nb = 0; nfail = 0; nbad = 0; byyear = {}
    for di, day in enumerate(todo, 1):
        syms = sel[day]; rows = []; ok = True
        for ci in range(0, len(syms), chunk):
            r, e = fetch_day(day, syms[ci:ci + chunk], hdr, thr, getter)
            if r is None: ok = False; break
            rows += r; nbad += e
        if not ok: nfail += 1; continue
        with open(os.path.join(outd, "day5_%s.csv" % day[:7]), "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if f.tell() == 0: w.writerow(["date", "symbol", "t", "open", "high", "low", "close", "volume", "trade_count", "vwap"])
            w.writerows(sorted(rows))
        with open(donep, "a", encoding="utf-8") as f: f.write(day + "\n")
        nb += len(rows); byyear[day[:4]] = byyear.get(day[:4], 0) + len(rows)
        if di % 50 == 0: print("[%5d s] Tage %d/%d Bars %d ungueltige Symbole %d Fehltage %d" % (time.time() - t0, di, len(todo), nb, nbad, nfail), flush=True)
    print("FERTIG: Tage geholt %d, Bars %d, ungueltige Einzelsymbole %d, Fehltage (erneut starten) %d, Dauer %d s" % (len(todo) - nfail, nb, nbad, nfail, time.time() - t0))
    print("Bars je Jahr:", ", ".join("%s %d" % (k, v) for k, v in sorted(byyear.items())))

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    def opt(k, d, f=str): return f(a[a.index(k) + 1]) if k in a else d
    main(a[0], opt("--out", ""), opt("--rate", 150.0, float), opt("--chunk", 60, int), "--allow-test" in a)
