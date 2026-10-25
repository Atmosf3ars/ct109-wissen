# alpaca_daily_v1.py - Tagesbars (SIP, adjustment=all) fuer die Symbole der Insider-Cluster-Liste; Daten bleiben auf dem PC.
# Aufruf:  python alpaca_daily_v1.py <cluster-csv> <Ausgabe-Ordner> [--from 2016-01-01] [--kmin 3] [--minprice 2.0] [--rate 150] [--extra SPY,IWM]
# Schluessel NUR aus Umgebungsvariablen (Namen werden ausgegeben, Werte nie): APCA_API_KEY_ID / APCA_API_SECRET_KEY
# (alternativ ALPACA_API_KEY / ALPACA_API_SECRET oder ALPACA_KEY_ID / ALPACA_SECRET_KEY). Rate-Limit Basic 200/min: Standard 150/min.
# Hartes Ende: keine Bars ab 2026-07-01 (Anfrage endet 2026-06-30, zusaetzlich beim Schreiben verworfen). Wiederaufnahme: vorhandene Dateien werden uebersprungen.
# Chat-Ausgabe: nur Zaehlungen (Symbole, ok, leer, Fehler). Eine Datei <SYMBOL>.csv: date,open,high,low,close,volume,trade_count,vwap
import sys, os, csv, json, time, urllib.request, urllib.error, urllib.parse
from datetime import date

CUT = "2026-07-01"
BASE = "https://data.alpaca.markets/v2/stocks/%s/bars"
KEYS = [("APCA_API_KEY_ID", "APCA_API_SECRET_KEY"), ("ALPACA_API_KEY", "ALPACA_API_SECRET"), ("ALPACA_KEY_ID", "ALPACA_SECRET_KEY")]

def keys():
    for a, b in KEYS:
        if os.environ.get(a) and os.environ.get(b):
            print("Schluessel aus Umgebungsvariablen: %s / %s (Werte nicht ausgegeben)" % (a, b))
            return os.environ[a], os.environ[b]
    sys.exit("Keine Alpaca-Schluessel in den Umgebungsvariablen gefunden (erwartet: APCA_API_KEY_ID + APCA_API_SECRET_KEY).")

def http_get(url, hdr):
    req = urllib.request.Request(url, headers=hdr)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))

class Throttle:
    def __init__(self, per_min): self.gap = 60.0 / per_min; self.t = 0.0
    def wait(self):
        d = self.t + self.gap - time.time()
        if d > 0: time.sleep(d)
        self.t = time.time()

def fetch_symbol(sym, start, hdr, thr, getter=http_get):
    """liefert (Zeilen, Status); Status 'ok' | 'leer' | 'fehler:<Code>'"""
    rows = []; token = None
    for _ in range(50):
        q = {"timeframe": "1Day", "start": start + "T00:00:00Z", "end": "2026-06-30T23:59:59Z", "adjustment": "all", "feed": "sip", "limit": "10000", "sort": "asc"}
        if token: q["page_token"] = token
        url = BASE % urllib.parse.quote(sym) + "?" + urllib.parse.urlencode(q)
        for attempt in range(6):
            thr.wait()
            try:
                js = getter(url, hdr); break
            except urllib.error.HTTPError as e:
                if e.code == 429: time.sleep(5 * (attempt + 1)); continue
                if e.code in (400, 404, 422): return rows, "fehler:%d" % e.code
                if e.code in (401, 403): sys.exit("Alpaca-Authentifizierung fehlgeschlagen (HTTP %d) - Abbruch." % e.code)
                time.sleep(3 * (attempt + 1))
            except Exception:
                time.sleep(3 * (attempt + 1))
        else:
            return rows, "fehler:wiederholt"
        for b in js.get("bars") or []:
            d = b["t"][:10]
            if d >= CUT: continue
            rows.append((d, b["o"], b["h"], b["l"], b["c"], b["v"], b.get("n", 0), b.get("vw", 0)))
        token = js.get("next_page_token")
        if not token: break
    return rows, ("ok" if rows else "leer")

def symbols(csvp, since, kmin, minprice):
    syms = {}
    with open(csvp, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if int(r["kmin"]) != kmin or r["cluster_date"] < since: continue
            if float(r["avg_price"]) < minprice: continue
            s = r["symbol"].strip().upper()
            if not s or " " in s or s in ("NONE", "N/A", "NA"): continue
            syms.setdefault(s, []).append(r["cluster_date"])
    return syms

def main(csvp, outd, since="2016-01-01", kmin=3, minprice=2.0, rate=150, extra=""):
    os.makedirs(outd, exist_ok=True)
    k, s = keys(); hdr = {"APCA-API-KEY-ID": k, "APCA-API-SECRET-KEY": s, "accept": "application/json"}
    syms = symbols(csvp, since, kmin, minprice)
    for e in [x.strip().upper() for x in extra.split(",") if x.strip()]: syms.setdefault(e, [])
    print("Symbole mit Cluster (k>=%d, ab %s, Preis>=%.1f): %d; Cluster gesamt %d" % (kmin, since, minprice, len(syms), sum(len(v) for v in syms.values())), flush=True)
    thr = Throttle(rate); cnt = {"ok": 0, "leer": 0, "uebersprungen": 0}; err = {}; t0 = time.time(); alt = 0
    for i, sym in enumerate(sorted(syms), 1):
        path = os.path.join(outd, sym.replace("/", "_") + ".csv")
        if os.path.exists(path): cnt["uebersprungen"] += 1; continue
        rows, st = fetch_symbol(sym, "2016-01-01", hdr, thr)
        if st.startswith("fehler") and "-" in sym:
            rows, st = fetch_symbol(sym.replace("-", "."), "2016-01-01", hdr, thr); alt += 1
        if st == "ok":
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f); w.writerow(["date", "open", "high", "low", "close", "volume", "trade_count", "vwap"]); w.writerows(rows)
            cnt["ok"] += 1
        elif st == "leer": cnt["leer"] += 1
        else: err[st] = err.get(st, 0) + 1
        if i % 100 == 0:
            print("[%5d s] %d/%d ok %d leer %d fehler %s" % (time.time() - t0, i, len(syms), cnt["ok"], cnt["leer"], err), flush=True)
    print("FERTIG: Symbole %d, ok %d, leer %d, uebersprungen %d, Fehler %s, mit Punkt-Ersatz versucht %d, Dauer %d s" % (len(syms), cnt["ok"], cnt["leer"], cnt["uebersprungen"], err, alt, time.time() - t0))

if __name__ == "__main__":
    a = sys.argv[1:]
    def opt(k, d, f=str): return f(a[a.index(k) + 1]) if k in a else d
    main(a[0], a[1], opt("--from", "2016-01-01"), opt("--kmin", 3, int), opt("--minprice", 2.0, float), opt("--rate", 150, float), opt("--extra", ""))
