# count_insider_v1.py - reine Ereigniszaehlung Insider-Cluster (Form 4, Code P), keine Renditen, keine Kurse
# python count_insider_v1.py <Ordner mit *_form345.zip>
import sys, os, glob, csv, io, zipfile
from collections import defaultdict
from datetime import datetime, date

CUT = date(2026, 7, 1)
MON = {m: i + 1 for i, m in enumerate(["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"])}

def pdate(s):
    s = s.strip()
    try:
        d, m, y = s.split("-")
        return date(int(y), MON[m.upper()[:3]], int(d))
    except Exception:
        pass
    for f in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, f).date()
        except Exception:
            pass
    return None

def table(z, key):
    for n in z.namelist():
        if os.path.basename(n).upper().startswith(key):
            rd = csv.reader(io.TextIOWrapper(z.open(n), encoding="utf-8", errors="replace"), delimiter="\t")
            hdr = [h.strip().upper() for h in next(rd)]
            return hdr, rd
    return None, None

def col(hdr, *names):
    for n in names:
        if n in hdr:
            return hdr.index(n)
    return None

def main(folder):
    VAL = 100000.0
    WIN = 14
    COOL = 30
    purchases = []   # (issuer, filing_date, owner, value)
    nsub = nbuy = 0
    for fn in sorted(glob.glob(os.path.join(folder, "*_form345.zip"))):
        with zipfile.ZipFile(fn) as z:
            h, rd = table(z, "SUBMISSION")
            if h is None: continue
            ia = col(h, "ACCESSION_NUMBER"); idt = col(h, "FILING_DATE"); ic = col(h, "ISSUERCIK"); it = col(h, "DOCUMENT_TYPE")
            sub = {}
            for r in rd:
                try:
                    if it is not None and r[it].strip() != "4": continue
                    d = pdate(r[idt])
                    if d is None or d >= CUT: continue
                    sub[r[ia]] = (r[ic], d)
                except Exception:
                    pass
            nsub += len(sub)
            h, rd = table(z, "REPORTINGOWNER")
            oa = col(h, "ACCESSION_NUMBER"); oc = col(h, "RPTOWNERCIK"); orl = col(h, "RPTOWNER_RELATIONSHIP")
            owners = defaultdict(list)
            for r in rd:
                try:
                    rel = r[orl].upper()
                    if r[oa] in sub and ("OFFICER" in rel or "DIRECTOR" in rel):
                        owners[r[oa]].append(r[oc])
                except Exception:
                    pass
            h, rd = table(z, "NONDERIV_TRANS")
            ta = col(h, "ACCESSION_NUMBER"); tc = col(h, "TRANS_CODE"); ts = col(h, "TRANS_SHARES"); tp = col(h, "TRANS_PRICEPERSHARE"); tad = col(h, "TRANS_ACQUIRED_DISP_CD")
            val = defaultdict(float)
            for r in rd:
                try:
                    if r[ta] in owners and r[tc].strip() == "P" and r[tad].strip() == "A":
                        val[r[ta]] += float(r[ts]) * float(r[tp])
                except Exception:
                    pass
            for acc, v in val.items():
                iss, d = sub[acc]
                for o in set(owners[acc]):
                    purchases.append((iss, d, o, v / max(1, len(set(owners[acc])))))
                nbuy += 1
    print("Form-4-Einreichungen (Typ 4, bis 2026-06-30): %d, davon mit Kauf (Code P, Offizier/Direktor): %d" % (nsub, nbuy))
    by_iss = defaultdict(list)
    for iss, d, o, v in purchases:
        by_iss[iss].append((d, o, v))
    res = {k: defaultdict(lambda: [0, 0]) for k in (2, 3, 4)}   # Jahr -> [Ereignisse, Emittenten-Ereignisse zaehlt gleich]
    issuers = {k: set() for k in (2, 3, 4)}
    for iss, lst in by_iss.items():
        lst.sort()
        days = sorted(set(d for d, _, _ in lst))
        last = {k: None for k in (2, 3, 4)}
        for d in days:
            win = [(dd, o, v) for dd, o, v in lst if 0 <= (d - dd).days < WIN]
            owners = set(o for _, o, _ in win); tot = sum(v for _, _, v in win)
            for k in (2, 3, 4):
                if len(owners) >= k and tot >= VAL and (last[k] is None or (d - last[k]).days >= COOL):
                    res[k][d.year][0] += 1
                    issuers[k].add(iss)
                    last[k] = d
    print("Jahr   Cluster>=2   Cluster>=3   Cluster>=4   (Insider-Personen in 14 Tagen, Summe >= 100 000 USD, Abstand >= 30 Tage je Emittent)")
    tot = {k: 0 for k in (2, 3, 4)}
    for y in range(2006, 2027):
        cells = []
        for k in (2, 3, 4):
            c = res[k][y][0] if y in res[k] else 0
            tot[k] += c; cells.append("%8d" % c)
        print("%d  %s" % (y, "   ".join(cells)))
    print("Summe  " + "   ".join("%8d" % tot[k] for k in (2, 3, 4)))
    print("Emittenten mit >= 1 Cluster:  " + "   ".join("k>=%d: %d" % (k, len(issuers[k])) for k in (2, 3, 4)))

if __name__ == "__main__":
    main(sys.argv[1])
