# orb_select_v1.py - ORB Phase 0c: Kandidatenliste Top-K je Tag nach relativem Eroeffnungsvolumen RV5 (Entwicklungsfenster). KEIN Test, KEIN alpha.
# Aufruf: python -u orb_select_v1.py <first5-Ordner> <Ausgabe-csv> [--k 60]
# Regel (Paper-Naehe, ex ante vor 09:35 bekannt): RV5 = Volumen der ersten 5-Min-Kerze / Mittel der ersten-Kerze-Volumina der 14 Vortage (>= 10 vorhanden);
# Doji (Close = Open) ausgeschlossen; Rang je Tag nach RV5 absteigend, Gleichstand nach Symbol. Hartes Ende der Auswahl: 2019-12-31 (Entwicklungsfenster).
# Ausgabe-csv: date,symbol,rank,rv5. Chat: nur Zaehlungen.
import sys, os, csv, glob
import numpy as np
LAST = "2019-12-31"; NWIN = 14; NMIN = 10
def main(fol, outp, K):
    D, S, O, C, V = [], [], [], [], []
    for fn in sorted(glob.glob(os.path.join(fol, "first5_*.csv"))):
        with open(fn, newline="") as f:
            r = csv.reader(f); next(r, None)
            for row in r:
                if row[0] > LAST: continue
                D.append(row[0]); S.append(row[1]); O.append(float(row[2])); C.append(float(row[5])); V.append(float(row[6]))
    D = np.array(D, dtype="datetime64[D]"); O = np.array(O); C = np.array(C); V = np.array(V)
    days = np.unique(D); di = np.searchsorted(days, D); syms, si = np.unique(np.array(S), return_inverse=True)
    nd, ns = len(days), len(syms)
    M = np.zeros((ns, nd)); Kc = np.zeros((ns, nd)); M[si, di] = V; Kc[si, di] = 1.0
    cs = np.concatenate([np.zeros((ns, 1)), np.cumsum(M, axis=1)], axis=1); ck = np.concatenate([np.zeros((ns, 1)), np.cumsum(Kc, axis=1)], axis=1)
    lo = np.maximum(di - NWIN, 0); sm = cs[si, di] - cs[si, lo]; cnt = ck[si, di] - ck[si, lo]
    valid = (cnt >= NMIN) & (di >= NMIN) & (C != O)
    avg = np.where(valid, sm / np.maximum(cnt, 1), np.nan); rv = np.where(valid & (avg > 0), V / avg, np.nan)
    ok = np.nonzero(np.isfinite(rv))[0]
    # Sortierung: Tag, RV5 absteigend, Symbol
    order = ok[np.lexsort((si[ok], -rv[ok], di[ok]))]
    ds = di[order]; start = np.concatenate([[0], np.nonzero(np.diff(ds))[0] + 1])
    rank = np.arange(len(order)) - np.repeat(start, np.diff(np.concatenate([start, [len(order)]]))) + 1
    sel = order[rank <= K]; rk = rank[rank <= K]
    with open(outp, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["date", "symbol", "rank", "rv5"])
        for a, r_ in zip(sel, rk): w.writerow([str(days[di[a]]), syms[si[a]], int(r_), "%.4f" % rv[a]])
    print("Auswahl K=%d bis %s: Symbol-Tage %d | Tage %d | verschiedene Symbole %d | Datei %s" % (K, LAST, len(sel), len(np.unique(di[sel])), len(np.unique(si[sel])), outp))
if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2: sys.exit(__doc__)
    main(a[0], a[1], int(a[a.index("--k") + 1]) if "--k" in a else 60)
