# count_insider_v2.py - Insider-Cluster-LISTE (Form 4, Code P, Offizier/Direktor) fuer Idee INSIDER-ALL; KEINE Kurse, KEINE Renditen.
# python count_insider_v2.py <Ordner mit *_form345.zip> <Ausgabe-CSV>
# Schreibt je Cluster eine Zeile (CIK, Ticker laut Meldung, Cluster-Datum = Filing-Datum der Meldung, die die Schwelle erreicht,
# Personenzahl, Summe USD, mittlerer Kaufpreis je Aktie). Chat-Ausgabe: nur Zaehlungen je Jahr und Preis-/Wertklassen.
# Regeln (wie v1, vorab fest): Fenster 14 Tage, Summe >= 100 000 USD, Abstand >= 30 Tage je Emittent, k = 3 Personen (zusaetzlich k = 2 markiert).
# Nur FILING_DATE < 2026-07-01. Einstiegsregel (Spec spaeter): Open der naechsten Handelsbar NACH dem Filing-Datum (Uhrzeit unbekannt).
import sys, os, glob, csv, io, zipfile
from collections import defaultdict
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from count_insider_v1 import pdate, table, col, CUT

WIN, COOL, VAL = 14, 30, 100000.0

def load(folder):
    rows = []   # (cik, sym, filing_date, owner, value, shares, acc)
    nsub = 0
    for fn in sorted(glob.glob(os.path.join(folder, "*_form345.zip"))):
        with zipfile.ZipFile(fn) as z:
            h, rd = table(z, "SUBMISSION")
            if h is None: continue
            ia = col(h, "ACCESSION_NUMBER"); idt = col(h, "FILING_DATE"); ic = col(h, "ISSUERCIK"); it = col(h, "DOCUMENT_TYPE"); isy = col(h, "ISSUERTRADINGSYMBOL")
            sub = {}
            for r in rd:
                try:
                    if it is not None and r[it].strip() != "4": continue
                    d = pdate(r[idt])
                    if d is None or d >= CUT: continue
                    sub[r[ia]] = (r[ic].strip(), (r[isy].strip().upper() if isy is not None and isy < len(r) else ""), d)
                except Exception:
                    pass
            nsub += len(sub)
            h, rd = table(z, "REPORTINGOWNER")
            oa = col(h, "ACCESSION_NUMBER"); oc = col(h, "RPTOWNERCIK"); orl = col(h, "RPTOWNER_RELATIONSHIP")
            owners = defaultdict(set)
            for r in rd:
                try:
                    rel = r[orl].upper()
                    if r[oa] in sub and ("OFFICER" in rel or "DIRECTOR" in rel):
                        owners[r[oa]].add(r[oc])
                except Exception:
                    pass
            h, rd = table(z, "NONDERIV_TRANS")
            ta = col(h, "ACCESSION_NUMBER"); tc = col(h, "TRANS_CODE"); ts = col(h, "TRANS_SHARES"); tp = col(h, "TRANS_PRICEPERSHARE"); tad = col(h, "TRANS_ACQUIRED_DISP_CD")
            val = defaultdict(float); shs = defaultdict(float)
            for r in rd:
                try:
                    if r[ta] in owners and r[tc].strip() == "P" and r[tad].strip() == "A":
                        s = float(r[ts]); p = float(r[tp])
                        if s > 0 and p > 0:
                            val[r[ta]] += s * p; shs[r[ta]] += s
                except Exception:
                    pass
            for acc, v in val.items():
                cik, sym, d = sub[acc]
                n = max(1, len(owners[acc]))
                for o in owners[acc]:
                    rows.append((cik, sym, d, o, v / n, shs[acc] / n, acc))
    return rows, nsub

def clusters(rows, kmin):
    by = defaultdict(list)
    for cik, sym, d, o, v, s, acc in rows:
        by[cik].append((d, o, v, s, sym))
    out = []
    for cik, lst in by.items():
        lst.sort()
        last = None
        for d in sorted(set(x[0] for x in lst)):
            win = [x for x in lst if 0 <= (d - x[0]).days < WIN]
            owners = set(x[1] for x in win); tot = sum(x[2] for x in win); shs = sum(x[3] for x in win)
            if len(owners) >= kmin and tot >= VAL and (last is None or (d - last).days >= COOL):
                sym = [x[4] for x in win if x[4]][-1] if any(x[4] for x in win) else ""
                out.append((cik, sym, d, len(owners), tot, tot / shs if shs > 0 else 0.0, kmin))
                last = d
    out.sort(key=lambda r: (r[2], r[0]))
    return out

def main(folder, outp):
    rows, nsub = load(folder)
    cl2 = clusters(rows, 2); cl3 = clusters(rows, 3)
    cl = cl3
    with open(outp, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["cik", "symbol", "cluster_date", "n_owners", "total_usd", "avg_price", "kmin"])
        for r in sorted(cl2 + cl3, key=lambda r: (r[2], r[0], r[6])): w.writerow([r[0], r[1], r[2].isoformat(), r[3], "%.0f" % r[4], "%.4f" % r[5], r[6]])
    print("Form-4-Einreichungen (Typ 4, bis 2026-06-30): %d; Kaufzeilen (Person x Meldung): %d; Cluster k>=2: %d, k>=3: %d" % (
        nsub, len(rows), len(cl2), len(cl3)))
    print("Jahr | k>=3 gesamt | k>=3 & Preis>=2 USD | k>=3 & Preis>=2 & Summe>=250k | ohne Ticker")
    for y in range(2006, 2027):
        a = [r for r in cl if r[2].year == y]
        b = [r for r in a if r[5] >= 2.0]; c = [r for r in b if r[4] >= 250000]
        print("%d | %d | %d | %d | %d" % (y, len(a), len(b), len(c), sum(1 for r in a if not r[1])))
    a = [r for r in cl if r[2].year >= 2019]; b = [r for r in a if r[5] >= 2.0]
    print("seit 2019: k>=3 %d, Preis>=2 %d, Emittenten %d, Ticker-Anteil gefuellt %.1f %%" % (
        len(a), len(b), len(set(r[0] for r in b)), 100.0 * sum(1 for r in b if r[1]) / max(1, len(b))))
    print("Datei: %s (nur auf dem PC lassen)" % outp)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
