# edgar_13d_count_v1.py - Phase 0 13D-ERST: zaehlt Schedule-13D-Einreichungen (SC 13D, SC 13D/A, SCHEDULE 13D, SCHEDULE 13D/A) aus der SEC-Bulkdatei submissions.zip
# je Jahr, mit Alpaca-Bars (Emittent = Hauptdatei-CIK mit Ticker-Bars), Erstmeldungen vs. Aenderungen, unabhaengige Erst-Episoden (je Emittent, Abstand >= 180 Tage) und Annahmezeit-Klasse (UTC).
# KEINE Renditen. Hinweis: Die Einreichung steht in den Listen von Filer UND Subject; es wird je Hauptdatei des Emittenten gezaehlt, ob die Filings dort erscheinen, ist Teil der Pruefung (Gesamtzahl pro Jahr).
# Aufruf: python -u edgar_13d_count_v1.py <submissions.zip> <alpaca-daily>
import sys, os, json, zipfile, re, hashlib
from collections import Counter, defaultdict
from datetime import date
START = "2016-01-01"; END = "2026-06-30"
FORMS = {"SC 13D": "erst", "SCHEDULE 13D": "erst", "SC 13D/A": "aend", "SCHEDULE 13D/A": "aend", "SC 13G": "13G", "SCHEDULE 13G": "13G", "SC 13G/A": "13G/A", "SCHEDULE 13G/A": "13G/A"}
def rows(js):
    blk = js.get("filings", {}).get("recent", js) if isinstance(js, dict) else {}
    f = blk.get("form", []); d = blk.get("filingDate", []); a = blk.get("acceptanceDateTime", [])
    for i in range(len(f)): yield f[i], (d[i] if i < len(d) else ""), (a[i] if i < len(a) else "")
def klass(acc):
    if len(acc) < 16: return "?"
    hh = int(acc[11:13]) * 60 + int(acc[14:16])
    return "UTC<12" if hh < 720 else ("UTC12-20" if hh < 1200 else "UTC>=20")
def main(zp, bars):
    z = zipfile.ZipFile(zp); have = set(os.path.splitext(x)[0].upper() for x in os.listdir(bars) if x.lower().endswith(".csv"))
    ev = defaultdict(list); cik_bars = {}; tot = Counter(); totyear = defaultdict(Counter); nfiles = 0
    for name in z.namelist():
        m = re.match(r"CIK(\d{10})(-submissions-\d+)?\.json$", os.path.basename(name))
        if not m: continue
        cik = m.group(1); main_ = m.group(2) is None; js = json.loads(z.read(name)); nfiles += 1
        if main_: cik_bars[cik] = any(t.upper() in have for t in js.get("tickers", []))
        for form, d, acc in rows(js):
            if form in FORMS and START <= d <= END:
                tot[form] += 1; totyear[FORMS[form]][d[:4]] += 1; ev[(cik, FORMS[form])].append((d, klass(acc)))
    print("Skript-SHA256 %s; Dateien %d; Emittenten mit Bars %d" % (hashlib.sha256(open(__file__, "rb").read()).hexdigest()[:16], nfiles, sum(cik_bars.values())))
    print("Formulartyp gesamt (alle Emittenten 2016..2026-06): %s" % dict(tot))
    for k in ("erst", "aend", "13G", "13G/A"):
        print("%s je Jahr (alle Emittenten): %s" % (k, ",".join("%s:%d" % (y, totyear[k][y]) for y in sorted(totyear[k]))))
    for k in ("erst", "aend"):
        n = 0; iss = set(); epi = 0; yr = Counter(); kl = Counter()
        for (cik, kk), lst in ev.items():
            if kk != k or not cik_bars.get(cik, False): continue
            lst.sort(); iss.add(cik); last = None
            for d, c in lst:
                n += 1; yr[d[:4]] += 1; kl[c] += 1; dd = date.fromisoformat(d)
                if last is None or (dd - last).days >= 180: epi += 1
                last = dd
        print("13D %s mit Bars: Einreichungen %d, Emittenten %d, Episoden (Abstand >= 180 d) %d; je Jahr %s; Klassen (UTC<12/12-20/>=20) %d/%d/%d" % (k, n, len(iss), epi, ",".join("%s:%d" % (y, yr[y]) for y in sorted(yr)), kl["UTC<12"], kl["UTC12-20"], kl["UTC>=20"]))
if __name__ == "__main__": main(sys.argv[1], sys.argv[2])
