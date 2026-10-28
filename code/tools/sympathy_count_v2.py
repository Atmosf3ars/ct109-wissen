# sympathy_count_v2.py - SYMPATHY-REVERSION Phase 0b: Zaehlung mit TAGESZEIT-ANGEPASSTEM sigma (NUR Entwicklungsfenster 2016-2019). KEIN Test, KEIN alpha, kein Freeze.
# Aufruf: python -u sympathy_count_v2.py <day5-Ordner> [--k 4.0] [--calm 0.5] [--sigdays 40] [--start 8]
# Anlass: v1 (Ergebnis `register/results/sympathy_count_v1_out.txt`) zaehlte 4,51 % der Leader-Tage als 4-sigma-Ereignisse, 89 % davon endeten bis 10:30 ET.
#   Ursache (ANNAHME, hier zu pruefen): sigma5 wurde ueber alle Bars des Tages gemittelt und unterschaetzt die Eroeffnungsstunde (Tageszeit-Saisonalitaet der Streuung).
# v2: sigma je SLOT (Bar-Streuung zur gleichen Tageszeit aus den sigdays Vortagen, ex ante); sigma15^2 = Summe der drei Slot-Varianzen der Sprungbars.
#   Sprungfenster darf erst ab Slot --start-2 beginnen (Standard --start 8: Sprungbar >= Slot 8 = 10:10 ET, Fenster ab 09:55 ET; Eroeffnungsauktion/Overnight-Nachrichten ausgeschlossen).
# Sonst wie v1: Leader-Residual (Leader - Sektor-ETF) ueber 3 Bars >= k*sigma15 bei ruhigem ETF (< calm*sigmaETF15), erstes Ereignis je Leader-Tag, letzte Sprungbar <= Slot 70.
# Ausgabe NUR Zaehlungen des Leader-Sprungs; KEINE Rendite der Mitlaeufer nach dem Ereignis.
import sys, os, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sympathy_count_v1 import load, NS, LAST
from sympathy_sel_v1 import SECTORS

def slot_sigma(x, w, nmin=25):
    """sigma5 je (Tag, Slot) aus den w Vortagen zur gleichen Tageszeit (ex ante); nan wenn < nmin gueltige Vortage"""
    nd = x.shape[0]; m = np.isfinite(x)
    sq = np.where(m, x * x, 0.0); cs = np.vstack([np.zeros((1, NS)), np.cumsum(sq, 0)]); cn = np.vstack([np.zeros((1, NS)), np.cumsum(m, 0)])
    j = np.arange(nd); lo = np.maximum(j - w, 0)
    S = cs[j] - cs[lo]; N = cn[j] - cn[lo]
    return np.where(N >= min(nmin, w), np.sqrt(S / np.maximum(N, 1)), np.nan)

def events(days, R, k=4.0, calm=0.5, w=40, start=8):
    out = []
    for etf, d in SECTORS.items():
        if etf not in R: continue
        e = R[etf]; se = slot_sigma(e, w); je = e[:, 2:] + e[:, 1:-1] + e[:, :-2]
        se15 = np.sqrt(se[:, 2:] ** 2 + se[:, 1:-1] ** 2 + se[:, :-2] ** 2)
        for l in d["leaders"]:
            if l not in R: continue
            res = R[l] - e; sr = slot_sigma(res, w)
            j = res[:, 2:] + res[:, 1:-1] + res[:, :-2]
            s15 = np.sqrt(sr[:, 2:] ** 2 + sr[:, 1:-1] ** 2 + sr[:, :-2] ** 2)
            cond = np.isfinite(j) & np.isfinite(je) & np.isfinite(s15) & np.isfinite(se15) & (np.abs(j) >= k * s15) & (np.abs(je) < calm * se15)
            cond[:, 69:] = False; cond[:, :max(start - 2, 0)] = False
            fol = [R[f] for f in d["followers"] if f in R]
            for di in np.nonzero(cond.any(1))[0]:
                i = int(cond[di].argmax()); s = i + 2
                nf = sum(1 for a in fol if np.isfinite(a[di, s + 1]))
                if nf >= 3: out.append((etf, l, int(di), s, nf, float(np.nanmean(se[di]))))
    return out

def main():
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    def opt(k, d, f=str): return f(a[a.index(k) + 1]) if k in a else d
    k = opt("--k", 4.0, float); calm = opt("--calm", 0.5, float); w = opt("--sigdays", 40, int); start = opt("--start", 8, int)
    days, R = load(a[0]); nd = len(days)
    print("Skript: sympathy_count_v2.py | Tage %d | Symbole %d | Fenster bis %s | k=%.1f calm=%.2f sigdays=%d start-Slot=%d (Sprungbar >= %02d:%02d ET)" % (nd, len(R), LAST, k, calm, w, start, 9 + (30 + 5 * start) // 60, (30 + 5 * start) % 60))
    nl = sum(1 for etf, d in SECTORS.items() for l in d["leaders"] if l in R)
    ev = events(days, R, k, calm, w, start)
    if not ev: print("0 Ereignisse = INSUFFICIENT (kein Nullbefund)"); return
    yrs = np.array([int(days[e[2]][:4]) for e in ev]); sec = np.array([e[0] for e in ev]); dd = np.array([e[2] for e in ev]); sl = np.array([e[3] for e in ev]); nf = np.array([e[4] for e in ev])
    # Zulaessige Leader-Tage (Fenster-Anzahl) fuer eine Kalibrierung: je Leader-Tag ein Versuch je Slot
    nslots = 69 - max(start - 2, 0)
    print("\n[A] Ereignisse (Leader-Tage mit Sprung): %d von %d Leader-Tagen (%.2f%%); Fenster je Leader-Tag ~%d (bei Gauss 4 sigma zweiseitig ~0,006%% je Fenster => ~%.2f%% je Leader-Tag erwartet)" % (len(ev), nl * nd, 100.0 * len(ev) / (nl * nd), nslots, 100.0 * nslots * 6.3e-5))
    sd = set(zip(sec, dd)); dist = set(dd)
    print("[B] Unabhaengige Episoden: Sektor-Tage %d | verschiedene Handelstage %d (untere Schranke) | Mitlaeufer je Ereignis Median %d" % (len(sd), len(dist), int(np.median(nf))))
    print("[C] Je Jahr (Sektor-Tage): " + " | ".join("%d: %d" % (y, len(set(zip(sec[yrs == y], dd[yrs == y])))) for y in sorted(set(yrs))))
    print("[D] Je Sektor (Sektor-Tage): " + " | ".join("%s: %d" % (s, len(set(dd[sec == s]))) for s in SECTORS))
    bins = [(0, 12, "09:30-10:30"), (12, 24, "10:30-11:30"), (24, 42, "11:30-13:00"), (42, 60, "13:00-14:30"), (60, 78, "14:30-16:00")]
    print("[E] Zeitpunkt (Sprungbar, ET): " + " | ".join("%s: %d" % (lab, ((sl >= a_) & (sl < b_)).sum()) for a_, b_, lab in bins))
    se_all = np.concatenate([np.nanmean(slot_sigma(R[etf], w), 1) for etf in SECTORS if etf in R]); med = np.nanmedian(se_all)
    hi = np.array([e[5] >= med for e in ev])
    print("[F] Zustand (ETF-sigma der Vortage >= Median): hoch %d | niedrig %d Ereignisse; Sektor-Tage hoch %d | niedrig %d" % (hi.sum(), (~hi).sum(), len(set(zip(sec[hi], dd[hi]))), len(set(zip(sec[~hi], dd[~hi])))))
    for kk in (3.0, 5.0):
        e2 = events(days, R, kk, calm, w, start); print("    Sensitivitaet k=%.1f: Ereignisse %d, Sektor-Tage %d" % (kk, len(e2), len(set((x[0], x[2]) for x in e2))))
    for st in (2, 14):
        e2 = events(days, R, k, calm, w, st); print("    Sensitivitaet start-Slot %d: Ereignisse %d, Sektor-Tage %d" % (st, len(e2), len(set((x[0], x[2]) for x in e2))))
    E = len(sd); D = len(dist); ext = 1632.0 / nd
    print("\n[G] Power-Zeile (ANNAHMEN sigma des Mitlaeufer-Rueckkehr-Ertrags 60/80/100 bp je Ereignis; MDE70 = 3,34*sigma/sqrt(n_eff)):")
    for lab, nn in (("Entwicklung, Sektor-Tage", E), ("Entwicklung, nur verschiedene Tage", D), ("Test hochgerechnet (x%.2f), Sektor-Tage" % ext, E * ext), ("Test hochgerechnet, verschiedene Tage", D * ext)):
        print("  %-44s n_eff %6.0f | " % (lab, nn) + " | ".join("sigma %3d bp: MDE70 %5.1f bp" % (s, 3.34 * s / math.sqrt(nn)) for s in (60, 80, 100)))
    print("[H] Kosten (Ticket 1500 USD): Provision 4,7 bp Round-Trip; Slippage 2/3/5 bp je Seite => Hurdle brutto 8,7 / 10,7 / 14,7 bp. Autor-Erwartung netto +15 bp (ungeprueft).")
    print("\nHinweis: Nachrichten-/Ergebnistage nicht gefiltert; Universum feste Ueberlebenden-Auswahl (ANNAHME). Gleichzeitig verschiedene Handelstage = Anteil an allen %d Tagen: %.0f%%." % (nd, 100.0 * D / nd))

if __name__ == "__main__":
    main()
