# edgar_8k_count_v2.py - Phase 0 8-K (Korrektur zu v1): Folgedateien (CIK..-submissions-NNN.json) werden dem Hauptemittenten zugeordnet;
# zaehlt je Item: Einreichungen, Einreichungen mit Alpaca-Bars, unabhaengige Episoden (je Emittent+Item, Abstand >= 28 Kalendertage),
# Emittenten, je Jahr (nur mit Bars). KEINE Renditen. Nur Anzahlen.
# Aufruf: python -u edgar_8k_count_v2.py count <submissions.zip> <alpaca-daily>
import sys, os, json, zipfile, hashlib, re
from collections import Counter, defaultdict
from datetime import date
START = "2016-01-01"; END = "2026-06-30"
FOCUS = ["4.02", "3.01", "2.05", "2.06", "1.03", "5.01", "1.02", "2.02", "5.02", "1.01", "8.01", "7.01"]
def rows(js):
    blk = js.get("filings", {}).get("recent", js) if isinstance(js, dict) else {}
    f = blk.get("form", []); it = blk.get("items", []); d = blk.get("filingDate", []); a = blk.get("acceptanceDateTime", [])
    for i in range(len(f)): yield f[i], (it[i] if i < len(it) else ""), (d[i] if i < len(d) else ""), (a[i] if i < len(a) else "")
def klass(acc):
    if len(acc) < 16: return "?"
    hh = int(acc[11:13]) * 60 + int(acc[14:16])
    return "UTC<12" if hh < 720 else ("UTC12-20" if hh < 1200 else "UTC>=20")
def count(zp, bars):
    z = zipfile.ZipFile(zp)
    have = set(os.path.splitext(x)[0].upper() for x in os.listdir(bars) if x.lower().endswith(".csv"))
    ev = defaultdict(list)      # (cik,item) -> [(date, klass)]
    cik_bars = {}; n_main = 0; nfiles = 0
    for name in z.namelist():
        if not name.endswith(".json"): continue
        m = re.match(r"CIK(\d{10})(-submissions-\d+)?\.json$", os.path.basename(name))
        if not m: continue
        cik = m.group(1); main = m.group(2) is None
        js = json.loads(z.read(name)); nfiles += 1
        if main:
            n_main += 1
            cik_bars[cik] = any(t.upper() in have for t in js.get("tickers", []))
        for form, items, d, acc in rows(js):
            if form != "8-K" or not (START <= d <= END): continue
            for it in [x.strip() for x in items.split(",") if x.strip()]:
                if it in FOCUS: ev[(cik, it)].append((d, klass(acc)))
    print("Skript-SHA256 %s; Dateien %d, Hauptdateien %d, Emittenten mit Alpaca-Bars: %d, Bars-Tickerdateien: %d" % (hashlib.sha256(open(__file__, "rb").read()).hexdigest()[:16], nfiles, n_main, sum(cik_bars.values()), len(have)))
    print("Item | Einreichungen gesamt | mit Bars | Emittenten mit Bars | Episoden (Abstand>=28d) mit Bars | je Jahr mit Bars | Klassen mit Bars (UTC<12/12-20/>=20)")
    for it in FOCUS:
        tot = nb = 0; issuers = set(); epi = 0; yr = Counter(); kl = Counter()
        for (cik, i2), lst in ev.items():
            if i2 != it: continue
            tot += len(lst)
            if not cik_bars.get(cik, False): continue
            lst.sort(); nb += len(lst); issuers.add(cik); last = None
            for d, k in lst:
                dd = date.fromisoformat(d)
                if last is None or (dd - last).days >= 28: epi += 1
                last = dd; yr[d[:4]] += 1; kl[k] += 1
        print("%s | %d | %d | %d | %d | %s | %d/%d/%d" % (it, tot, nb, len(issuers), epi, ",".join("%s:%d" % (y, yr[y]) for y in sorted(yr)), kl["UTC<12"], kl["UTC12-20"], kl["UTC>=20"]))
if __name__ == "__main__":
    if sys.argv[1] == "count": count(sys.argv[2], sys.argv[3])
