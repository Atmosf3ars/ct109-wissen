# edgar_8k_count_v1.py - Phase 0 8-K: laedt (optional) die SEC-Bulkdatei submissions.zip und ZAEHLT 8-K-Einreichungen je Item/Jahr/Uhrzeit-Klasse.
# KEINE Renditen. Nur Anzahlen. Rohdatei bleibt auf dem PC.
# Aufruf:  $env:SEC_UA = "Vorname Nachname deine-mail"   (SEC verlangt einen Kontakt im User-Agent; nicht in den Chat)
#   python -u edgar_8k_count_v1.py download D:\CT109-Data\sec-submissions
#   python -u edgar_8k_count_v1.py count D:\CT109-Data\sec-submissions\submissions.zip D:\CT109-Data\alpaca-daily
import sys, os, json, zipfile, hashlib, urllib.request
from collections import Counter, defaultdict
URL = "https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip"
START = "2016-01-01"; END = "2026-06-30"
FOCUS = ["4.02", "3.01", "2.05", "2.06", "1.03", "5.01", "1.02", "2.02", "5.02", "1.01", "8.01", "7.01"]
def download(outd):
    ua = os.environ.get("SEC_UA", "")
    if len(ua) < 8 or "@" not in ua: sys.exit("SEC_UA fehlt (Umgebungsvariable mit Name und Kontakt, siehe Kopfzeile)")
    os.makedirs(outd, exist_ok=True); p = os.path.join(outd, "submissions.zip")
    req = urllib.request.Request(URL, headers={"User-Agent": ua, "Accept-Encoding": "identity"})
    h = hashlib.sha256(); n = 0
    with urllib.request.urlopen(req, timeout=300) as r, open(p, "wb") as f:
        while True:
            b = r.read(1 << 20)
            if not b: break
            f.write(b); h.update(b); n += len(b)
            if n % (200 << 20) < (1 << 20): print("%d MB" % (n >> 20), flush=True)
    print("FERTIG %s %d Bytes sha256 %s" % (p, n, h.hexdigest()))
def rows(js):
    """liefert (form, items, filingDate, acceptance) aus recent-Block oder aus einer Folgedatei"""
    blk = js.get("filings", {}).get("recent", js) if isinstance(js, dict) else {}
    f = blk.get("form", []); it = blk.get("items", []); d = blk.get("filingDate", []); a = blk.get("acceptanceDateTime", [])
    for i in range(len(f)): yield f[i], (it[i] if i < len(it) else ""), (d[i] if i < len(d) else ""), (a[i] if i < len(a) else "")
def klass(acc):
    if len(acc) < 16: return "?"
    hh = int(acc[11:13]) * 60 + int(acc[14:16])      # UTC; ET = UTC-4/-5 -> Vorbereitung, genaue Zeitzonenpruefung vor Nutzung [A]
    return "UTC<12" if hh < 720 else ("UTC12-20" if hh < 1200 else "UTC>=20")
def count(zp, bars):
    z = zipfile.ZipFile(zp); by_item = Counter(); by_year = defaultdict(Counter); kl = Counter(); with_bars = Counter(); tot = 0; n_ciks = 0; no_ticker = 0
    focus_ciks = defaultdict(set)
    for name in z.namelist():
        if not name.endswith(".json"): continue
        js = json.loads(z.read(name))
        main = name.startswith("CIK") and "-submissions-" not in name
        tick = js.get("tickers", []) if main else []
        if main:
            n_ciks += 1
            if not tick: no_ticker += 1
            has = any(os.path.exists(os.path.join(bars, t.upper() + ".csv")) for t in tick)
        for form, items, d, acc in rows(js):
            if form != "8-K" or not (START <= d <= END): continue
            tot += 1
            for it in [x.strip() for x in items.split(",") if x.strip()]:
                by_item[it] += 1; by_year[it][d[:4]] += 1
                if it in FOCUS:
                    kl[(it, klass(acc))] += 1
                    if main and has: with_bars[it] += 1
    print("Skript-SHA256 %s" % hashlib.sha256(open(__file__, "rb").read()).hexdigest()[:16])
    print("Emittenten (CIK-Hauptdateien): %d, ohne Ticker: %d; 8-K-Einreichungen %s .. %s: %d" % (n_ciks, no_ticker, START, END, tot))
    print("Item | Anzahl gesamt | davon Hauptdatei-Emittent mit Alpaca-Bars | je Jahr 2016..2026")
    for it, n in by_item.most_common(25):
        print("%s | %d | %d | %s" % (it, n, with_bars.get(it, 0), ",".join("%s:%d" % (y, by_year[it][y]) for y in sorted(by_year[it]))))
    print("Fokus-Items nach Annahmezeit-Klasse (UTC): %s" % sorted(kl.items()))
if __name__ == "__main__":
    if sys.argv[1] == "download": download(sys.argv[2])
    elif sys.argv[1] == "count": count(sys.argv[2], sys.argv[3])
