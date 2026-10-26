# orb_select_v2.py - ORB: Kandidatenliste Top-K je Tag nach relativem Eroeffnungsvolumen RV5 fuer ein waehlbares Fenster (Testfenster nach Freeze). KEIN Ergebnis, nur Auswahl.
# Aufruf: python -u orb_select_v2.py <first5-Ordner> <Ausgabe-csv> --from 2020-01-02 --to 2026-06-30 [--k 20]
# Regel wie orb_select_v1.py: RV5 = Volumen der ersten 5-Min-Kerze / Mittel der ersten-Kerze-Volumina der 14 Vortage (>= 10 vorhanden; Vortage duerfen vor --from liegen);
# Doji ausgeschlossen; Rang je Tag nach RV5 absteigend, Gleichstand nach Symbol. Hartes Datenende 2026-06-30. Ausgabe-csv: date,symbol,rank,rv5. Chat: nur Zaehlungen.
import sys, os, csv, glob
import numpy as np
NWIN = 14; NMIN = 10; HARD = "2026-06-30"
def main(fol, outp, dfrom, dto, K):
    if dto > HARD: sys.exit("Datenende 2026-06-30")
    D, S, O, C, V = [], [], [], [], []
    for fn in sorted(glob.glob(os.path.join(fol, "first5_*.csv"))):
        with open(fn, newline="") as f:
            r = csv.reader(f); next(r, None)
            for row in r:
                if row[0] > dto: continue
                D.append(row[0]); S.append(row[1]); O.append(float(row[2])); C.append(float(row[5])); V.append(float(row[6]))
    D = np.array(D, dtype="datetime64[D]"); O = np.array(O); C = np.array(C); V = np.array(V)
    days = np.unique(D); di = np.searchsorted(days, D); syms, si = np.unique(np.array(S), return_inverse=True)
    nd, ns = len(days), len(syms)
    M = np.zeros((ns, nd)); Kc = np.zeros((ns, nd)); M[si, di] = V; Kc[si, di] = 1.0
    cs = np.concatenate([np.zeros((ns, 1)), np.cumsum(M, axis=1)], axis=1); ck = np.concatenate([np.zeros((ns, 1)), np.cumsum(Kc, axis=1)], axis=1)
    lo = np.maximum(di - NWIN, 0); sm = cs[si, di] - cs[si, lo]; cnt = ck[si, di] - ck[si, lo]
    inwin = (D >= np.datetime64(dfrom)) & (D <= np.datetime64(dto))
    valid = (cnt >= NMIN) & (di >= NMIN) & (C != O) & inwin
    avg = np.where(valid, sm / np.maximum(cnt, 1), np.nan); rv = np.where(valid & (avg > 0), V / avg, np.nan)
    ok = np.nonzero(np.isfinite(rv))[0]
    order = ok[np.lexsort((si[ok], -rv[ok], di[ok]))]
    ds = di[order]; start = np.concatenate([[0], np.nonzero(np.diff(ds))[0] + 1])
    rank = np.arange(len(order)) - np.repeat(start, np.diff(np.concatenate([start, [len(order)]]))) + 1
    sel = order[rank <= K]; rk = rank[rank <= K]
    with open(outp, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["date", "symbol", "rank", "rv5"])
        for a, r_ in zip(sel, rk): w.writerow([str(days[di[a]]), syms[si[a]], int(r_), "%.4f" % rv[a]])
    print("Auswahl K=%d %s..%s: Symbol-Tage %d | Tage %d | verschiedene Symbole %d | Datei %s" % (K, dfrom, dto, len(sel), len(np.unique(di[sel])), len(np.unique(si[sel])), outp))
if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) < 2 or "--from" not in a or "--to" not in a: sys.exit(__doc__)
    main(a[0], a[1], a[a.index("--from") + 1], a[a.index("--to") + 1], int(a[a.index("--k") + 1]) if "--k" in a else 20)
