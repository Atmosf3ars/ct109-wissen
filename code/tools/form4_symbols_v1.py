# form4_symbols_v1.py - alle Emittenten-Ticker aus den Form-4-Einreichungen (SUBMISSION.tsv) 2015-Q4 ... 2026-Q2 als Symbolliste (inkl. gestrichener Titel).
# Zweck: Ergaenzung der Alpaca-Assets-Liste um Titel, die nicht mehr als Asset gefuehrt werden (Ueberlebensverzerrung verkleinern). Nur Zaehlungen im Chat.
# Aufruf: python -u form4_symbols_v1.py <sec-form345-Ordner> <Ausgabe-csv> [<Bars-Ordner1> <Bars-Ordner2> ...]
# Ausgabe-csv: symbol,exchange,status,tradable,name,first_filing,last_filing,filings (exchange/status/name leer -> kein Boersenfilter in alpaca_universe_v1 --list)
import sys, os, glob, zipfile, csv, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from count_insider_v1 import pdate, table, col, CUT
OK = re.compile(r"^[A-Z][A-Z0-9.\-]{0,9}$")

def main(folder, outp, bars):
    d = {}; nsub = 0; nempty = 0
    for fn in sorted(glob.glob(os.path.join(folder, "*_form345.zip"))):
        base = os.path.basename(fn)
        if base[:4] < "2015" or (base[:4] == "2015" and base[4:6] != "q4"): continue
        with zipfile.ZipFile(fn) as z:
            h, rd = table(z, "SUBMISSION")
            if h is None: continue
            idt = col(h, "FILING_DATE"); isy = col(h, "ISSUERTRADINGSYMBOL"); it = col(h, "DOCUMENT_TYPE")
            for r in rd:
                try:
                    if it is not None and r[it].strip() not in ("4", "4/A", "3", "5"): continue
                    dt = pdate(r[idt])
                    if dt is None or dt >= CUT: continue
                    nsub += 1
                    s = r[isy].strip().upper() if isy is not None and isy < len(r) else ""
                    if not OK.match(s): nempty += 1; continue
                    e = d.get(s)
                    if e is None: d[s] = [dt, dt, 1]
                    else: e[0] = min(e[0], dt); e[1] = max(e[1], dt); e[2] += 1
                except Exception:
                    pass
    have = set()
    for b in bars:
        if os.path.isdir(b): have |= set(os.path.splitext(x)[0].upper() for x in os.listdir(b) if x.lower().endswith(".csv"))
    with open(outp, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["symbol", "exchange", "status", "tradable", "name", "first_filing", "last_filing", "filings"])
        for s in sorted(d): w.writerow([s, "", "", "", "", d[s][0], d[s][1], d[s][2]])
    miss = [s for s in d if s not in have]
    old = [s for s in miss if d[s][1].year < 2026]
    print("Einreichungen (Form 3/4/5, 2015Q4..2026Q2): %d | ohne verwertbaren Ticker: %d | verschiedene Ticker: %d" % (nsub, nempty, len(d)))
    print("davon mit Bars in den angegebenen Ordnern: %d | ohne Bars (zu laden): %d (davon letzte Meldung vor 2026: %d)" % (len(d) - len(miss), len(miss), len(old)))
    ys = {}
    for s in miss: ys[d[s][1].year] = ys.get(d[s][1].year, 0) + 1
    print("fehlende Ticker nach Jahr der letzten Meldung:", ", ".join("%d: %d" % (k, ys[k]) for k in sorted(ys)))

if __name__ == "__main__":
    if len(sys.argv) < 3: sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
