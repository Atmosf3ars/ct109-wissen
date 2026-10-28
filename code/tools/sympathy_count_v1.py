# sympathy_count_v1.py - SYMPATHY-REVERSION Phase 0: Zaehlung unabhaengiger Ereignis-Episoden und Power-Zeile (NUR Entwicklungsfenster 2016-2019). KEIN Test, KEIN alpha, kein Freeze.
# Aufruf: python -u sympathy_count_v1.py <day5-Ordner mit Sektor-Universum> [--k 4.0] [--calm 0.5] [--sigdays 20]
# Eingabe: day5_<YYYY-MM>.csv (aus alpaca_day5_v1.py mit der Auswahl von sympathy_sel_v1.py). Tage > 2019-12-31 werden verworfen.
# Ereignis (ENTWURF, Parameter vor dem Freeze fest): Leader-Residual J = Summe der Bar-Renditen (Leader - Sektor-ETF) ueber 3 aufeinanderfolgende 5-Min-Bars (15 min);
#   |J| >= k * sqrt(3) * sigma5 (sigma5 = Streuung der Residual-Barrenditen der VORHERGEHENDEN sigdays Tage, ex ante) UND ETF ruhig: |Summe ETF-Bars| < calm * sqrt(3) * sigmaETF5.
#   Pro Leader und Tag das erste Ereignis; letzte Sprungbar <= 14:25 (Slot 70), damit nach dem Einstieg >= 35 min bleiben. Einstieg Mitlaeufer erst NACH dem Fenster (Bar s+1).
# Ausgabe NUR Zaehlungen des Ereignisses (Betrag des Leader-Sprungs, nicht das Vorzeichen); KEINE Rendite der Mitlaeufer nach dem Ereignis.
# Unabhaengige Episoden = Sektor-Tage (mehrere Leader/Ereignisse am selben Sektor-Tag zaehlen einmal); untere Schranke = verschiedene Handelstage ueber alle Sektoren.
import sys, os, csv, glob, math
from datetime import date
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from alpaca_intraday_v1 import et_offset
from sympathy_sel_v1 import SECTORS

LAST = "2019-12-31"; NS = 78

def load(fol):
    rows = {}
    for fn in sorted(glob.glob(os.path.join(fol, "day5_*.csv"))):
        with open(fn, newline="") as f:
            r = csv.reader(f); next(r, None)
            for row in r:
                if row[0] > LAST: continue
                rows.setdefault(row[1], []).append((row[0], row[2], float(row[3]), float(row[6])))
    days = sorted(set(x[0] for v in rows.values() for x in v)); dix = {d: i for i, d in enumerate(days)}
    offs = {}
    R = {}
    for sym, v in rows.items():
        a = np.full((len(days), NS), np.nan)
        for d, t, o, c in v:
            if d not in offs:
                y, m, dd = map(int, d.split("-")); offs[d] = 4 if et_offset(date(y, m, dd)) == "-04:00" else 5
            s = (int(t[11:13]) * 60 + int(t[14:16]) - offs[d] * 60 - 570) // 5
            if 0 <= s < NS and o > 0 and c > 0: a[dix[d], s] = math.log(c / o)
        R[sym] = a
    return days, R

def roll_sigma(x, w):
    """sigma5 je Tag aus den w Vortagen (ex ante); nan wenn < 10 Vortage mit >= 60 Bars"""
    nd = x.shape[0]; m = np.isfinite(x)
    s2 = np.where(m, x * x, 0.0).sum(1); n = m.sum(1)
    cs = np.concatenate([[0.0], np.cumsum(s2)]); cn = np.concatenate([[0], np.cumsum(n)]); cd = np.concatenate([[0], np.cumsum(n >= 60)])
    j = np.arange(nd); lo = np.maximum(j - w, 0)
    S = cs[j] - cs[lo]; N = cn[j] - cn[lo]; ND = cd[j] - cd[lo]
    return np.where((ND >= 10) & (N > 0), np.sqrt(S / np.maximum(N, 1)), np.nan)

def events(days, R, k=4.0, calm=0.5, w=20):
    out = []   # (sektor, leader, tagindex, slot, n_follower, etfsigma)
    for etf, d in SECTORS.items():
        if etf not in R: continue
        e = R[etf]; se = roll_sigma(e, w)
        je = e[:, 2:] + e[:, 1:-1] + e[:, :-2]
        for l in d["leaders"]:
            if l not in R: continue
            res = R[l] - e; sr = roll_sigma(res, w)
            j = res[:, 2:] + res[:, 1:-1] + res[:, :-2]       # Index i entspricht Sprungbar s = i + 2
            thr = k * math.sqrt(3) * sr[:, None]; cth = calm * math.sqrt(3) * se[:, None]
            cond = np.isfinite(j) & np.isfinite(je) & (np.abs(j) >= thr) & (np.abs(je) < cth)
            cond[:, 69:] = False                                # s = i+2 <= 70 -> i <= 68
            fol = [R[f] for f in d["followers"] if f in R]
            for di in np.nonzero(cond.any(1))[0]:
                i = int(cond[di].argmax()); s = i + 2
                nf = sum(1 for a in fol if np.isfinite(a[di, s + 1]))
                if nf >= 3: out.append((etf, l, int(di), s, nf, se[di]))
    return out

def main():
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    def opt(k, d, f=str): return f(a[a.index(k) + 1]) if k in a else d
    k = opt("--k", 4.0, float); calm = opt("--calm", 0.5, float); w = opt("--sigdays", 20, int)
    days, R = load(a[0]); nd = len(days)
    have = [s for s in R]; miss = [s for etf, d in SECTORS.items() for s in [etf] + d["leaders"] + d["followers"] if s not in R]
    print("Skript: sympathy_count_v1.py | Tage %d | Symbole mit Daten %d | ohne Daten %d (%s) | Fenster bis %s | k=%.1f calm=%.2f sigdays=%d" % (nd, len(have), len(miss), ",".join(sorted(set(miss))) or "-", LAST, k, calm, w))
    ev = events(days, R, k, calm, w)
    yrs = np.array([int(days[e[2]][:4]) for e in ev]); sec = np.array([e[0] for e in ev]); dd = np.array([e[2] for e in ev]); sl = np.array([e[3] for e in ev]); nf = np.array([e[4] for e in ev])
    lead_days = sum(1 for etf, d in SECTORS.items() for l in d["leaders"] if l in R) * nd
    print("\n[A] Ereignisse (Leader-Tage mit Sprung): %d von %d Leader-Tagen (%.2f%%); Gauss-Erwartung 4 sigma zweiseitig ~0,006%% je Fenster (Schwanzlastigkeit erwartet)" % (len(ev), lead_days, 100.0 * len(ev) / max(lead_days, 1)))
    if not ev: print("0 Ereignisse = INSUFFICIENT (kein Nullbefund)"); return
    sd = set(zip(sec, dd)); dist_days = set(dd)
    print("[B] Unabhaengige Episoden: Sektor-Tage %d | verschiedene Handelstage %d (untere Schranke) | Mitlaeufer je Ereignis: Median %d" % (len(sd), len(dist_days), int(np.median(nf))))
    print("[C] Je Jahr (Sektor-Tage): " + " | ".join("%d: %d" % (y, len(set(zip(sec[yrs == y], dd[yrs == y])))) for y in sorted(set(yrs))))
    print("[D] Je Sektor (Sektor-Tage): " + " | ".join("%s: %d" % (s, len(set(dd[sec == s]))) for s in SECTORS))
    early = sl <= 11
    print("[E] Zeitpunkt: Sprung endet bis 10:30 ET: %d Ereignisse (%.0f%%) | spaeter: %d" % (early.sum(), 100.0 * early.mean(), (~early).sum()))
    # Zustand: ETF-sigma der Vortage (ex ante) hoch/niedrig relativ zum Median ueber die Fenster-Tage
    se_all = np.concatenate([roll_sigma(R[etf], w) for etf in SECTORS if etf in R]); med = np.nanmedian(se_all)
    hi = np.array([e[5] >= med for e in ev])
    print("[F] Zustand (ETF-sigma der Vortage >= Median): hoch %d | niedrig %d Ereignisse; Sektor-Tage hoch %d | niedrig %d" % (hi.sum(), (~hi).sum(), len(set(zip(sec[hi], dd[hi]))), len(set(zip(sec[~hi], dd[~hi])))))
    for kk in (3.0, 5.0):
        e2 = events(days, R, kk, calm, w); print("    Sensitivitaet k=%.1f: Ereignisse %d, Sektor-Tage %d" % (kk, len(e2), len(set((x[0], x[2]) for x in e2))))
    E = len(sd); D = len(dist_days); ext = 1632.0 / nd
    print("\n[G] Power-Zeile (ANNAHMEN: sigma des Mitlaeufer-Rueckkehr-Ertrags 60/80/100 bp je Ereignis; MDE70 = 3,34*sigma/sqrt(n_eff)):")
    for lab, nn in (("Entwicklung, Sektor-Tage", E), ("Entwicklung, nur verschiedene Tage", D), ("Test 2020-2026H1 hochgerechnet (x%.2f), Sektor-Tage" % ext, E * ext), ("Test hochgerechnet, verschiedene Tage", D * ext)):
        print("  %-52s n_eff %6.0f | " % (lab, nn) + " | ".join("sigma %3d bp: MDE70 %5.1f bp" % (s, 3.34 * s / math.sqrt(nn)) for s in (60, 80, 100)))
    print("[H] Kosten (Ticket 1500 USD, Round-Trip): Provision 0,70 USD = %.1f bp; Slippage 2/3/5 bp je Seite => Hurdle brutto %.1f / %.1f / %.1f bp" % (0.70 / 1500 * 1e4, 0.70 / 1500 * 1e4 + 4, 0.70 / 1500 * 1e4 + 6, 0.70 / 1500 * 1e4 + 10))
    print("[I] Autor-Annahme (Quelle ungeprueft): netto +15 bp. Vergleich mit MDE70 oben entscheidet: Erwartung < MDE70 => HINWEIS-Klasse (kein alpha).")
    print("\nHinweis: Ereignisse enthalten Nachrichten-/Ergebnistage (Fortsetzung statt Rueckkehr moeglich); Universum ist eine feste Ueberlebenden-Auswahl (ANNAHME).")

if __name__ == "__main__":
    main()
