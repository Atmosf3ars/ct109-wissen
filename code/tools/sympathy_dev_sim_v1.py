# sympathy_dev_sim_v1.py - SYMPATHY-REVERSION Entwicklungs-Simulation (NUR Entwicklungsfenster 2016-2019). Exploration OHNE alpha; getestet wird spaeter einmal im Testfenster mit vorab gehashten Parametern.
# Aufruf: python -u sympathy_dev_sim_v1.py <day5-Ordner> [--seed 20261029] [--draws 300]
# Ereignis wie sympathy_count_v2.py (k=4, ETF ruhig 0,5, sigma je Slot aus 40 Vortagen, Sprungbar >= Slot 8, erstes Ereignis je Leader-Tag).
# Handel: jeder Mitlaeufer des Sektors, ENTGEGEN dem Sprung des Leaders, Einstieg zum Open der Bar nach dem Sprungfenster (s+1), Ausstieg zum Close nach H Bars (Standard 36 = 3 h) oder Tagesende (letzte Bar).
# Ertrag in bp je Mitlaeufer; je Ereignis Mittel ueber die Mitlaeufer (Ereignis = 1 Beobachtung); Cluster nach Handelstag. Kosten: 4,7 bp Round-Trip + 2*s bp (s = 2/3/5).
# Placebo: gleiche Mitlaeufer/Slot/Haltedauer an zufaelligen Nicht-Ereignistagen des Sektors, gleiche Richtung wie das Ereignis. Zusatz: sektorneutral (Mitlaeufer minus ETF).
# Das Testfenster (ab 2020-01-01) wird nie gelesen. Viele Auswertungen => jede Auswahl hier ist Exploration ohne alpha-Gewicht.
import sys, os, csv, glob, math
from datetime import date
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from alpaca_intraday_v1 import et_offset
from sympathy_sel_v1 import SECTORS
from sympathy_count_v2 import slot_sigma
from sympathy_count_v1 import NS, LAST

def load_oc(fol):
    raw = {}
    for fn in sorted(glob.glob(os.path.join(fol, "day5_*.csv"))):
        with open(fn, newline="") as f:
            r = csv.reader(f); next(r, None)
            for row in r:
                if row[0] > LAST: continue
                raw.setdefault(row[1], []).append((row[0], row[2], float(row[3]), float(row[6])))
    days = sorted(set(x[0] for v in raw.values() for x in v)); dix = {d: i for i, d in enumerate(days)}; offs = {}
    O, C = {}, {}
    for sym, v in raw.items():
        o = np.full((len(days), NS), np.nan); c = np.full((len(days), NS), np.nan)
        for d, t, op, cl in v:
            if d not in offs:
                y, m, dd = map(int, d.split("-")); offs[d] = 4 if et_offset(date(y, m, dd)) == "-04:00" else 5
            s = (int(t[11:13]) * 60 + int(t[14:16]) - offs[d] * 60 - 570) // 5
            if 0 <= s < NS and op > 0 and cl > 0: o[dix[d], s] = op; c[dix[d], s] = cl
        O[sym] = o; C[sym] = c
    return days, O, C

def find_events(O, C, k=4.0, calm=0.5, w=40, start=8):
    R = {s: np.log(C[s] / O[s]) for s in O}; out = []
    for etf, d in SECTORS.items():
        e = R[etf]; se = slot_sigma(e, w); je = e[:, 2:] + e[:, 1:-1] + e[:, :-2]
        se15 = np.sqrt(se[:, 2:] ** 2 + se[:, 1:-1] ** 2 + se[:, :-2] ** 2)
        for l in d["leaders"]:
            res = R[l] - e; sr = slot_sigma(res, w)
            j = res[:, 2:] + res[:, 1:-1] + res[:, :-2]
            s15 = np.sqrt(sr[:, 2:] ** 2 + sr[:, 1:-1] ** 2 + sr[:, :-2] ** 2)
            cond = np.isfinite(j) & np.isfinite(je) & np.isfinite(s15) & np.isfinite(se15) & (np.abs(j) >= k * s15) & (np.abs(je) < calm * se15)
            cond[:, 69:] = False; cond[:, :max(start - 2, 0)] = False
            for di in np.nonzero(cond.any(1))[0]:
                i = int(cond[di].argmax()); out.append((etf, l, int(di), i + 2, 1 if j[di, i] > 0 else -1, float(np.nanmean(se[di]))))
    return out

def trade_bp(O, C, sym, di, s, sign, H):
    """Ertrag in bp in Richtung sign: Einstieg Open Bar s+1, Ausstieg Close Bar min(s+H, 77); nan wenn Daten fehlen"""
    e = s + 1; x = min(s + H, NS - 1)
    if e > x: return np.nan
    o = O[sym][di, e]; c = C[sym][di, x]
    return sign * 1e4 * math.log(c / o) if (np.isfinite(o) and np.isfinite(c)) else np.nan

def cl_se(v, dayi):
    ud, inv = np.unique(dayi, return_inverse=True)
    s = np.bincount(inv, weights=v - v.mean()); return math.sqrt((s ** 2).sum()) / len(v)

def main():
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    def opt(k, d, f=str): return f(a[a.index(k) + 1]) if k in a else d
    seed = opt("--seed", 20261029, int); draws = opt("--draws", 300, int)
    days, O, C = load_oc(a[0]); nd = len(days); rng = np.random.default_rng(seed)
    ev = find_events(O, C)
    print("Skript: sympathy_dev_sim_v1.py | Tage %d | Ereignisse (Leader-Tage) %d | Fenster bis %s" % (nd, len(ev), LAST))
    ev_days = {}
    for etf, l, di, s, sg, sgm in ev: ev_days.setdefault(etf, set()).add(di)
    res = {}   # H -> (rev_bp je Ereignis, neutral, placebo-Mittel je Ziehung, day, year, state)
    def evaluate(H):
        r, rn, dayi, yr, hi, sec_ = [], [], [], [], [], []
        meds = np.nanmedian([x[5] for x in ev])
        pl = np.zeros((draws,)); pn = np.zeros((draws,)); cnt = 0; plv = [[] for _ in range(draws)]
        for etf, l, di, s, sg, sgm in ev:
            fo = SECTORS[etf]["followers"]; vals = []; neu = []
            etf_r = trade_bp(O, C, etf, di, s, -sg, H)
            for f in fo:
                v = trade_bp(O, C, f, di, s, -sg, H)
                if np.isfinite(v): vals.append(v); neu.append(v - etf_r if np.isfinite(etf_r) else np.nan)
            if len(vals) < 3: continue
            r.append(np.mean(vals)); rn.append(np.nanmean(neu)); dayi.append(di); yr.append(int(days[di][:4])); hi.append(sgm >= meds); sec_.append(etf)
            ok_days = [d for d in range(nd) if d not in ev_days[etf] and np.isfinite(O[etf][d, s + 1])]
            for q in range(draws):
                d2 = ok_days[rng.integers(len(ok_days))]
                pv = [trade_bp(O, C, f, d2, s, -sg, H) for f in fo]; pv = [x for x in pv if np.isfinite(x)]
                plv[q].append(np.mean(pv) if pv else np.nan)
        return np.array(r), np.array(rn), np.array(dayi), np.array(yr), np.array(hi), np.array(sec_), np.array([np.nanmean(p) for p in plv])
    print("\n[1] Mitlaeufer ENTGEGEN dem Leader-Sprung, Einstieg Open s+1, Ausstieg nach H Bars (bp; Mittel je Ereignis, Tages-Cluster-SE; Placebo = zufaellige Nicht-Ereignistage gleicher Richtung):")
    for H in (6, 12, 36, 80):
        r, rn, dayi, yr, hi, sec_, pl = evaluate(H)
        m = r.mean(); se = cl_se(r, dayi)
        print("  H=%2d Bars%s: n=%d | brutto %+6.2f bp (SE %.2f) | sektorneutral %+6.2f bp | Placebo %+6.2f bp (q2.5 %+6.2f / q97.5 %+6.2f) | Differenz %+6.2f bp"
              % (H, " (=Tagesende)" if H >= 70 else "", len(r), m, se, np.nanmean(rn), np.nanmean(pl), np.percentile(pl, 2.5), np.percentile(pl, 97.5), m - np.nanmean(pl)))
        if H == 36:
            print("      Kosten-Hurdle: Provision 4,7 bp + 2*s: s=2 -> 8,7 | s=3 -> 10,7 | s=5 -> 14,7 bp => Netto-Mittel (s=2/3/5): %+.2f / %+.2f / %+.2f bp" % (m - 8.7, m - 10.7, m - 14.7))
            for y in sorted(set(yr)): print("      Jahr %d: n=%d, %+6.2f bp" % (y, (yr == y).sum(), r[yr == y].mean()))
            print("      Zustand ETF-sigma hoch: n=%d %+6.2f bp | niedrig: n=%d %+6.2f bp" % (hi.sum(), r[hi].mean(), (~hi).sum(), r[~hi].mean()))
            for s_ in SECTORS: print("      Sektor %s: n=%d, %+6.2f bp" % (s_, (sec_ == s_).sum(), r[sec_ == s_].mean() if (sec_ == s_).any() else float("nan")))
            q = np.array([x[3] for x in ev]); print("      Verteilung Ereignis-Ertrag (je Ereignis, bp): p10 %.1f p50 %.1f p90 %.1f | Anteil positiv %.1f%%" % (np.percentile(r, 10), np.percentile(r, 50), np.percentile(r, 90), 100 * (r > 0).mean()))
    print("\nHinweis: Entwicklungsfenster, mehrere Haltedauern/Splits gesichtet: alles Exploration ohne alpha. Ein Freeze-Kandidat braucht vorab festes H (Draft: 36 Bars), Ereignisregel und Kosten; Test einmal im Testfenster.")

if __name__ == "__main__":
    main()
