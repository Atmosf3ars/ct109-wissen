# orb_count_v1.py - ORB Phase 0 (Opening Range Breakout): Kandidatentage aus Alpaca-Tagesbars zaehlen. KEIN Test, KEIN alpha, kein Freeze.
# Aufruf: python -u orb_count_v1.py <alpaca-daily-Ordner>
# Eingabe: <SYMBOL>.csv (date,open,high,low,close,volume,trade_count,vwap; SIP, adjustment=all; Daten ab 2026-07-01 werden verworfen).
# Ausgabe NUR Zaehlungen, Betraege (Kursniveau, ATR, Luecke als Betrag) und Verteilungen. KEINE Rendite, KEIN Vorzeichen einer Zielgroesse
# (keine Close-Open-Rendite, kein Richtungsvergleich). Die Luecke wird nur als Betrag |open/Vortagesschluss-1| verwendet.
# Vorab festgelegte Filter (aus Zarattini/Barbon/Aziz, Working Paper; hier nur ex ante aus Tagesbars): Vortagesschluss >= 5 USD,
# ATR(14) aus den 14 Vortagen >= 0,5 USD, mittleres Volumen der 14 Vortage >= 1 Mio. Stueck.
# Ranking-Proxy S1 = |Luecke| / (ATR14 / Vortagesschluss) (Luecke in ATR-Einheiten; vor 09:35 bekannt). Das Paper rankt nach dem relativen
# Volumen der ersten 5 Minuten - das braucht Intraday-Daten (Phase 0b), daher hier nur Proxy-Funnel K = 60 / 20 / 10 / 5 / 2.
# Achtung: Bars sind split-/dividendenbereinigt (adjustment=all): Preis- und Volumenfilter sind fuer weit zurueckliegende Splits Naeherungen [A].
import sys, os, csv, math
import numpy as np

CUT = "2026-07-01"
P_MIN, ATR_MIN, VOL_MIN, NATR = 5.0, 0.5, 1_000_000.0, 14
KS = [60, 20, 10, 5, 2]
END_ALIVE = np.datetime64("2026-06-15")

def load(path):
    ds, o, h, l, c, v = [], [], [], [], [], []
    with open(path, newline="") as f:
        r = csv.reader(f); next(r, None)
        for row in r:
            if len(row) < 6 or row[0] >= CUT: continue
            try:
                oo, hh, ll, cc, vv = float(row[1]), float(row[2]), float(row[3]), float(row[4]), float(row[5])
            except ValueError:
                continue
            if not (oo > 0 and hh > 0 and ll > 0 and cc > 0): continue
            ds.append(row[0]); o.append(oo); h.append(hh); l.append(ll); c.append(cc); v.append(vv)
    return (np.array(ds, dtype="datetime64[D]"), np.array(o), np.array(h), np.array(l), np.array(c), np.array(v))

def q(a, ps=(10, 50, 90)):
    if len(a) == 0: return "n/a"
    return " ".join("p%d=%.3g" % (p, np.percentile(a, p)) for p in ps)

def main():
    if len(sys.argv) < 2: sys.exit(__doc__)
    folder = sys.argv[1]
    files = sorted(x for x in os.listdir(folder) if x.lower().endswith(".csv"))
    D, SY, S1, AG, ATRP, PC, DV, ENDED = [], [], [], [], [], [], [], []
    nsym = 0; nbar = 0; first_after = 0; ended_syms = 0
    syms = []
    for si, fn in enumerate(files):
        d, o, h, l, c, v = load(os.path.join(folder, fn))
        n = len(c)
        if n < NATR + 3: continue
        nsym += 1; nbar += n; syms.append(fn[:-4])
        ended = bool(d[-1] < END_ALIVE); ended_syms += ended
        if d[0] > np.datetime64("2016-03-01"): first_after += 1
        pc = c[:-1]
        tr = np.maximum.reduce([h[1:] - l[1:], np.abs(h[1:] - pc), np.abs(l[1:] - pc)])  # tr[k] gehoert zu Tag k+1
        cs = np.concatenate([[0.0], np.cumsum(tr)]); cv = np.concatenate([[0.0], np.cumsum(v)])
        i = np.arange(NATR + 1, n)
        atr = (cs[i - 1] - cs[i - 1 - NATR]) / NATR            # Tage i-14 .. i-1
        avgv = (cv[i] - cv[i - NATR]) / NATR                  # Tage i-14 .. i-1
        prevc = c[i - 1]
        span = (d[i] - d[i - 1]).astype(int)
        gap = np.abs(o[i] / prevc - 1.0)
        ok = (prevc >= P_MIN) & (atr >= ATR_MIN) & (avgv >= VOL_MIN) & (span <= 5) & (atr > 0)
        if not ok.any(): continue
        k = np.nonzero(ok)[0]
        D.append(d[i][k]); S1.append(gap[k] * prevc[k] / atr[k]); AG.append(gap[k]); ATRP.append(atr[k] / prevc[k])
        PC.append(prevc[k]); DV.append(avgv[k] * prevc[k]); SY.append(np.full(len(k), len(syms) - 1)); ENDED.append(np.full(len(k), ended))
    D = np.concatenate(D); S1 = np.concatenate(S1); AG = np.concatenate(AG); ATRP = np.concatenate(ATRP)
    PC = np.concatenate(PC); DV = np.concatenate(DV); SY = np.concatenate(SY); ENDED = np.concatenate(ENDED)
    print("Skript: orb_count_v1.py | Bars-Dateien mit >= %d Tagen: %d | Tagesbars gesamt: %d | Symbole mit Endbar vor 2026-06-15: %d | Symbole mit erster Bar nach 2016-03-01: %d"
          % (NATR + 3, nsym, nbar, ended_syms, first_after))
    print("Filter: Vortagesschluss>=%.1f, ATR14>=%.2f USD, Vol14>=%.0f Stk | Eligible Symbol-Tage: %d" % (P_MIN, ATR_MIN, VOL_MIN, len(D)))
    yrs = D.astype("datetime64[Y]").astype(int) + 1970
    # --- A) Eligible je Tag
    ud, inv, cnt = np.unique(D, return_inverse=True, return_counts=True)
    uy = ud.astype("datetime64[Y]").astype(int) + 1970
    print("\n[A] Eligible Symbole je Handelstag (Alpaca-Bestand, NICHT das volle US-Universum):")
    print("  Handelstage mit >=1 Eligible: %d | Tage mit >=60: %d, >=20: %d, >=10: %d, >=5: %d, >=2: %d"
          % (len(ud), (cnt >= 60).sum(), (cnt >= 20).sum(), (cnt >= 10).sum(), (cnt >= 5).sum(), (cnt >= 2).sum()))
    for y in range(2016, 2027):
        m = uy == y
        if m.any(): print("  %d: Tage %3d | Eligible/Tag %s" % (y, m.sum(), q(cnt[m])))
    # --- B) Funnel
    order = np.lexsort((-S1, inv))          # nach Tag, dann S1 absteigend
    inv_s = inv[order]
    start = np.concatenate([[0], np.nonzero(np.diff(inv_s))[0] + 1])
    rank = np.arange(len(order)) - np.repeat(start, np.diff(np.concatenate([start, [len(order)]])))
    print("\n[B] Funnel nach Proxy S1 (|Luecke| in ATR-Einheiten); Symbol-Tage / Handelstage / Symbole / Anteil Endbar-vor-2026-06-15-Symbole:")
    sel_by_k = {}
    for K in KS:
        sel = order[rank < K]
        sel_by_k[K] = sel
        print("  K=%2d: Symbol-Tage %7d | Tage %4d | verschiedene Symbole %4d | Anteil beendeter Symbole %.1f%%"
              % (K, len(sel), len(np.unique(D[sel])), len(np.unique(SY[sel])), 100.0 * ENDED[sel].mean()))
    sel = sel_by_k[20]
    print("\n[C] Eigenschaften der K=20-Kandidaten (Betraege):")
    print("  |Luecke| (Anteil): %s" % q(AG[sel], (10, 50, 90, 99)))
    print("  S1 (Luecke in ATR): %s" % q(S1[sel], (10, 50, 90, 99)))
    print("  ATR14 in %% des Kurses: %s" % q(100 * ATRP[sel], (10, 50, 90)))
    print("  Vortagesschluss USD: %s" % q(PC[sel], (10, 50, 90)))
    print("  Dollarvolumen14 (Mio USD): %s" % q(DV[sel] / 1e6, (10, 50, 90)))
    print("  Je Jahr K=20: ", " | ".join("%d: %d" % (y, (yrs[sel] == y).sum()) for y in range(2016, 2027)))
    # Konzentration
    cs_ = np.bincount(SY[sel], minlength=len(syms)); srt = np.sort(cs_)[::-1]
    print("[D] Konzentration K=20: Top-10-Symbole %.1f%% der Symbol-Tage, Top-100 %.1f%%, Top-300 %.1f%%"
          % (100 * srt[:10].sum() / srt.sum(), 100 * srt[:100].sum() / srt.sum(), 100 * srt[:300].sum() / srt.sum()))
    top = np.argsort(-cs_)[:5]
    print("    haeufigste 5 Symbole (Tage): " + ", ".join("%s %d" % (syms[t], cs_[t]) for t in top))
    # --- E) Kosten in R (Rechnung, keine Messung)
    print("\n[E] Kosten (Rechnung): Provision 2 Orders x 0,35 USD je Round-Trip in Einheiten R = Risiko je Trade = Ticket x Stopabstand")
    print("  Ticket USD | Stopabstand 0,5%% / 1%% / 2%% -> Provision in R | Provision je Seite in bp des Tickets")
    for tk in (750, 1500, 3000):
        print("  %5d | %s | %.1f bp" % (tk, " / ".join("%.3f R" % (0.70 / (tk * s)) for s in (0.005, 0.01, 0.02)), 0.35 / tk * 1e4))
    # --- F) Power-Zeile (Annahmen!)
    print("\n[F] Power-Zeile je Trade in R (ANNAHMEN, nichts gemessen): MDE_p = (2,807 + z_p) * sigma / sqrt(n_eff), n_eff = n / (1 + (m-1) * rho_Tag)")
    for K in (20, 10):
        s = sel_by_k[K]; n = len(s); days = len(np.unique(D[s])); m = n / max(days, 1)
        for sig in (1.5, 2.0, 2.5):
            row = []
            for rho in (0.05, 0.10, 0.20):
                neff = n / (1 + (m - 1) * rho)
                row.append("rho %.2f: n_eff %6.0f MDE70 %.3f R / MDE80 %.3f R" % (rho, neff, 3.34 * sig / math.sqrt(neff), 3.65 * sig / math.sqrt(neff)))
            print("  K=%2d n=%d (%.1f/Tag) sigma %.1f R | %s" % (K, n, m, sig, " | ".join(row)))
    # --- G) Datenbedarf Intraday
    print("\n[G] Intraday-Bedarf (5-Min-Bars, 78 je Symbol-Tag; Alpaca Mehrsymbol-Abruf, <= 10 000 Punkte je Seite, 150 Aufrufe/min):")
    for K in (60, 20):
        s = sel_by_k[K]; days = len(np.unique(D[s])); pts = K * 78
        print("  K=%2d: %d Tage ~ %d Aufrufe (%.0f min), %d Punkte je Tag-Aufruf %s" % (K, days, days, days / 150.0, pts, "(> 10 000: Seiten noetig)" if pts > 10000 else "(ok)"))
    print("\nHinweis: Universum = Alpaca-Bestand dieser Dateien (Insider-Cluster-Symbole + SPY/IWM), nicht das volle US-Universum.")

if __name__ == "__main__":
    main()
