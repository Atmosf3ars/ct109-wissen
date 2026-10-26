# orb_first5_count_v1.py - ORB Phase 0c: Zaehlungen und Betraege aus der ersten 5-Min-Kerze (Entwicklungsfenster). KEIN Test, KEIN alpha, kein Freeze.
# Aufruf: python -u orb_first5_count_v1.py <first5-Ordner> [<_assets_us.csv>]
# Eingabe: <first5-Ordner>\first5_<YYYY-MM>.csv (aus alpaca_intraday_v1.py first). Nur Tage <= 2019-12-31 werden gelesen (Entwicklungsfenster).
# Ausgabe NUR Zaehlungen/Verteilungen von Betraegen: relatives Eroeffnungsvolumen, Kerzenspanne (= Risiko je Trade) in %, Provision in R, Kandidaten je Tag.
# KEINE Kursrendite nach der ersten Kerze, KEIN Ergebnis eines Trades. Die Kerzenrichtung wird nur benutzt, um den Risikoabstand
# (Close bis gegenueberliegendes Kerzenende) zu bestimmen; ausgegeben wird nur dessen Betrag.
# Paper-Regel (Zarattini/Barbon/Aziz, Working Paper): relatives Volumen der ersten 5 Minuten = Volumen / Mittel der 14 Vortage; hier: Mittel ueber die
# vorhandenen Vortage (>= 10 von 14), Doji (Close = Open) ausgeschlossen.
import sys, os, csv, glob, re, math
import numpy as np

LAST = "2019-12-31"; NWIN = 14; NMIN = 10
ETFRE = re.compile(r"\b(ETF|ETN|FUND|FUNDS|TRUST|ISHARES|SPDR|PROSHARES|INVESCO|VANECK|WISDOMTREE|DIREXION|INDEX|ADR|ADS|DEPOSITARY|SHARES)\b", re.I)

def q(a, ps=(10, 50, 90)):
    return "n/a" if len(a) == 0 else " ".join("p%d=%.3g" % (p, np.percentile(a, p)) for p in ps)

def main():
    if len(sys.argv) < 2: sys.exit(__doc__)
    fol = sys.argv[1]; assets = sys.argv[2] if len(sys.argv) > 2 else ""
    D, S, O, H, L, C, V = [], [], [], [], [], [], []
    for fn in sorted(glob.glob(os.path.join(fol, "first5_*.csv"))):
        with open(fn, newline="") as f:
            r = csv.reader(f); next(r, None)
            for row in r:
                if row[0] > LAST: continue
                D.append(row[0]); S.append(row[1]); O.append(float(row[2])); H.append(float(row[3])); L.append(float(row[4])); C.append(float(row[5])); V.append(float(row[6]))
    D = np.array(D, dtype="datetime64[D]"); O = np.array(O); H = np.array(H); L = np.array(L); C = np.array(C); V = np.array(V)
    days = np.unique(D); di = np.searchsorted(days, D)
    syms, si = np.unique(np.array(S), return_inverse=True)
    nd, ns = len(days), len(syms)
    print("Skript: orb_first5_count_v1.py | Zeilen (Symbol-Tage mit erster Kerze): %d | Handelstage %d | Symbole %d | Fenster bis %s" % (len(D), nd, ns, LAST))
    M = np.zeros((ns, nd), dtype=np.float32); K = np.zeros((ns, nd), dtype=np.float32)
    M[si, di] = V; K[si, di] = 1.0
    cs = np.concatenate([np.zeros((ns, 1), dtype=np.float64), np.cumsum(M, axis=1, dtype=np.float64)], axis=1)
    ck = np.concatenate([np.zeros((ns, 1), dtype=np.float64), np.cumsum(K, axis=1, dtype=np.float64)], axis=1)
    # Mittel der 14 Vortage: Tage j-14 .. j-1 -> Summen cs[j]-cs[j-14]
    j = di; lo = np.maximum(j - NWIN, 0)
    sm = cs[si, j] - cs[si, lo]; cnt = ck[si, j] - ck[si, lo]
    valid = (cnt >= NMIN) & (j >= NMIN)
    avg = np.where(valid, sm / np.maximum(cnt, 1), np.nan)
    rv = np.where(valid & (avg > 0), V / avg, np.nan)
    doji = C == O
    risk = np.where(C > O, (C - L) / C, np.where(C < O, (H - C) / C, np.nan))      # Betrag; Richtung geht nicht in die Ausgabe ein
    rng = (H - L) / O
    yrs = D.astype("datetime64[Y]").astype(int) + 1970
    print("Mit gueltigem Volumen-Mittel (>= %d von %d Vortagen): %d (%.1f%%) | Doji: %.2f%% | Kerzen mit Volumen 0: %d" % (NMIN, NWIN, valid.sum(), 100.0 * valid.mean(), 100.0 * doji.mean(), (V == 0).sum()))
    ok = valid & ~doji & np.isfinite(rv) & (risk > 0)
    print("\n[A] Relatives Eroeffnungsvolumen RV5 (Betrag, nur gueltige): %s" % q(rv[ok], (10, 50, 90, 99)))
    # Kandidaten je Tag
    print("[B] Kandidaten je Tag nach RV5-Schwelle (Median der Tage / Tage mit >= 20):")
    for th in (1.0, 2.0, 3.0, 5.0):
        c = np.bincount(di[ok & (rv >= th)], minlength=nd)
        print("  RV5 >= %.1f: Median %d/Tag, p10 %d, p90 %d | Tage mit >=20: %d von %d | Symbol-Tage %d" % (th, np.median(c), np.percentile(c, 10), np.percentile(c, 90), (c >= 20).sum(), nd, c.sum()))
    # Top-K je Tag nach RV5
    idx = np.nonzero(ok)[0]
    order = idx[np.lexsort((-rv[idx], di[idx]))]
    ds = di[order]; start = np.concatenate([[0], np.nonzero(np.diff(ds))[0] + 1])
    rank = np.arange(len(order)) - np.repeat(start, np.diff(np.concatenate([start, [len(order)]])))
    print("\n[C] Top-K je Tag nach RV5 (Symbol-Tage / Tage / Symbole / Anteil mit RV5 < 1):")
    selK = {}
    for Kk in (60, 20, 10, 5):
        s = order[rank < Kk]; selK[Kk] = s
        print("  K=%2d: %6d | Tage %4d | Symbole %4d | RV5<1: %.1f%%" % (Kk, len(s), len(np.unique(di[s])), len(np.unique(si[s])), 100.0 * (rv[s] < 1).mean()))
    s20 = selK[20]
    print("\n[D] K=20 Eigenschaften (Betraege):")
    print("  RV5: %s" % q(rv[s20], (10, 50, 90)))
    print("  Kerzenspanne (H-L)/O in %%: %s" % q(100 * rng[s20], (10, 50, 90)))
    print("  Risiko je Trade (Close bis Gegenende) in %%: %s" % q(100 * risk[s20], (10, 50, 90)))
    print("  Kerzen-Dollarvolumen (Mio USD): %s" % q(V[s20] * C[s20] / 1e6, (10, 50, 90)))
    print("  Je Jahr K=20: " + " | ".join("%d: %d" % (y, (yrs[s20] == y).sum()) for y in (2016, 2017, 2018, 2019)))
    print("\n[E] Provision in R (0,70 USD Round-Trip / (Ticket x Risiko%)), K=20-Kandidaten:")
    for tk in (750, 1500, 3000):
        cr = 0.70 / (tk * risk[s20])
        print("  Ticket %4d USD: %s | Anteil > 0,10 R: %.1f%% | Anteil > 0,25 R: %.1f%%" % (tk, q(cr, (10, 50, 90)), 100 * (cr > 0.10).mean(), 100 * (cr > 0.25).mean()))
    # Namensflag
    flag = {}
    if assets and os.path.exists(assets):
        with open(assets, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f): flag[r["symbol"]] = bool(ETFRE.search(r["name"]))
    if flag:
        names = syms[si[s20]]
        known = np.array([x in flag for x in names]); isetf = np.array([flag.get(x, False) for x in names])
        print("\n[F] Namensregel (grob, Assets-Liste; ETF/Fonds/Trust/ADR/ADS-aehnliche Namen): bekannt %.1f%% der K=20-Symbol-Tage, davon ETF/ADR-aehnlich %.1f%%" % (100 * known.mean(), 100 * isetf[known].mean() if known.any() else 0))
    cs_ = np.bincount(si[s20], minlength=ns); srt = np.sort(cs_)[::-1]
    print("[G] Konzentration K=20: Top-10-Symbole %.1f%%, Top-100 %.1f%%, Top-500 %.1f%% der Symbol-Tage; haeufigste 5: %s"
          % (100 * srt[:10].sum() / srt.sum(), 100 * srt[:100].sum() / srt.sum(), 100 * srt[:500].sum() / srt.sum(), ", ".join("%s %d" % (syms[t], cs_[t]) for t in np.argsort(-cs_)[:5])))
    # Power-Zeile
    print("\n[H] Power-Zeile (ANNAHMEN sigma 1,5/2,0/2,5 R, rho_Tag 0,05/0,10/0,20; MDE70 = 3,34*sigma/sqrt(n_eff)):")
    for lab, nn, dd in (("Entwicklung 2016-2019", len(s20), nd), ("Test 2020-2026H1 (hochgerechnet, 1 632 Tage)", 20 * 1632, 1632)):
        m = nn / dd
        for sig in (1.5, 2.0, 2.5):
            row = []
            for rho in (0.05, 0.10, 0.20):
                ne = nn / (1 + (m - 1) * rho); row.append("rho %.2f: n_eff %5.0f MDE70 %.3f R" % (rho, ne, 3.34 * sig / math.sqrt(ne)))
            print("  %-44s n=%6d sigma %.1f | %s" % (lab, nn, sig, " | ".join(row)))

if __name__ == "__main__":
    main()
