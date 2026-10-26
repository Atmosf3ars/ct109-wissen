# orb_dev_sim_v1.py - ORB Entwicklungs-Simulation (NUR Entwicklungsfenster 2016-2019). Exploration ohne alpha; Regeln werden hier festgelegt, getestet wird spaeter einmal im Testfenster.
# Aufruf: python -u orb_dev_sim_v1.py <day5-Ordner> <auswahl-csv> [--ticket 1500] [--seed 20261026] [--draws 500]
# Paper-Regel (Zarattini/Barbon/Aziz, Working Paper): Signalkerze = erste 5-Min-Kerze (09:30). Long wenn Close > Open, Short wenn Close < Open (Doji kein Trade).
# Einstieg zum Open der naechsten vorhandenen Bar, Stop am Gegenende der Signalkerze, Ziel tm*R (tm = 3 / 10 / ohne), sonst Schluss der letzten Bar (15:55-Bar).
# Stop und Ziel in derselben Bar => Stop zuerst (konservativ). Luecke durch den Stop => Fuellung zum Open der Bar. Entry jenseits des Stops => kein Trade.
# R = |Entry - Stop| (Risiko je Trade). Kosten: Provision 0,70 USD je Round-Trip bei Ticket T (in R: 0,70/(T*Risiko%)), Slippage s bp je Seite (in R: 2*s/1e4/Risiko%).
# Placebos: (a) Zufallsrichtung (Long/Short je Trade per Muenzwurf, gleiche Stop-Geometrie), (b) Zeitversatz: Signalkerze um 12 bzw. 36 Bars (10:30 / 12:30) verschoben, Auswahl bleibt die der Eroeffnung.
# Das Testfenster (ab 2020-01-01) wird nie gelesen (Dateien/Zeilen ab 2020 werden verworfen).
import sys, os, csv, glob, math, itertools
from datetime import date
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from alpaca_intraday_v1 import et_offset

LAST = "2019-12-31"; TMS = (3.0, 10.0, float("inf")); OFFS = (0, 12, 36)

_OFF = {}
def day_off(day):
    if day not in _OFF:
        y, m, d = map(int, day.split("-")); _OFF[day] = 4 if et_offset(date(y, m, d)) == "-04:00" else 5
    return _OFF[day]

def scan(o, h, l, c, k, long_, tm):
    """eine Seite; k = Index der Signalkerze; liefert (R, exit, risiko_prozent) oder None"""
    e = k + 1
    if e >= len(o): return None
    entry = o[e]
    if long_:
        stop = l[k]; dist = entry - stop
    else:
        stop = h[k]; dist = stop - entry
    if not (dist > 0): return None
    hs = (l[e:] <= stop) if long_ else (h[e:] >= stop)
    ts = np.inf if math.isinf(tm) else None
    if ts is None:
        tgt = entry + tm * dist if long_ else entry - tm * dist
        ht = (h[e:] >= tgt) if long_ else (l[e:] <= tgt)
        it = ht.argmax() if ht.any() else -1
    else:
        it = -1
    is_ = hs.argmax() if hs.any() else -1
    if is_ >= 0 and (it < 0 or is_ <= it):
        px = min(stop, o[e + is_]) if long_ else max(stop, o[e + is_]); ex = 0
    elif it >= 0:
        px = max(tgt, o[e + it]) if long_ else min(tgt, o[e + it]); ex = 1
    else:
        px = c[-1]; ex = 2
    r = (px - entry) / dist if long_ else (entry - px) / dist
    return r, ex, dist / entry

def main():
    a = sys.argv[1:]
    if len(a) < 2: sys.exit(__doc__)
    def opt(k, d, f=str): return f(a[a.index(k) + 1]) if k in a else d
    ticket = opt("--ticket", 1500.0, float); seed = opt("--seed", 20261026, int); draws = opt("--draws", 500, int)
    sel = {}
    with open(a[1], newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["date"] <= LAST: sel[(r["date"], r["symbol"])] = int(r["rank"])
    days = sorted(set(k[0] for k in sel)); dix = {d: i for i, d in enumerate(days)}
    # Ergebnisse je (offset, richtung, tm): Arrays ueber alle Symbol-Tage der Auswahl
    cand = []  # Liste pro Symbol-Tag mit allen Ergebnissen
    ng = 0
    for fn in sorted(glob.glob(os.path.join(a[0], "day5_*.csv"))):
        if os.path.basename(fn)[5:12] > LAST[:7]: continue
        with open(fn, newline="") as f:
            rd = csv.reader(f); next(rd, None)
            for (day, sym), g in itertools.groupby(rd, key=lambda r: (r[0], r[1])):
                if day > LAST or (day, sym) not in sel: continue
                g = list(g)
                off_h = day_off(day); slot = np.array([(int(r[2][11:13]) * 60 + int(r[2][14:16]) - off_h * 60 - 570) // 5 for r in g])
                o = np.array([float(r[3]) for r in g]); h = np.array([float(r[4]) for r in g]); l = np.array([float(r[5]) for r in g]); c = np.array([float(r[6]) for r in g])
                if slot[0] != 0: continue            # keine Eroeffnungskerze
                item = {"day": dix[day], "rank": sel[(day, sym)], "year": int(day[:4]), "dir0": 0 if c[0] == o[0] else (1 if c[0] > o[0] else -1)}
                for off in OFFS:
                    k = np.searchsorted(slot, off)
                    if k >= len(slot) or slot[k] != off: continue
                    for side in (True, False):
                        for tm in TMS:
                            r = scan(o, h, l, c, k, side, tm)
                            if r is not None: item[(off, side, tm)] = r
                    item[("dir", off)] = 0 if c[k] == o[k] else (1 if c[k] > o[k] else -1)
                cand.append(item); ng += 1
    print("Skript: orb_dev_sim_v1.py | ausgewaehlte Symbol-Tage mit Ganztagsdaten: %d von %d | Tage %d | Ticket %.0f USD | Fenster bis %s" % (ng, len(sel), len(days), ticket, LAST))
    rng = np.random.default_rng(seed)
    rank = np.array([x["rank"] for x in cand]); dayi = np.array([x["day"] for x in cand]); year = np.array([x["year"] for x in cand])

    def arrays(off, tm, mode):
        """mode 'real' (Kerzenrichtung), 'L', 'S'. liefert (R, exit, risk, valid)"""
        n = len(cand); R = np.full(n, np.nan); EX = np.full(n, -1); RK = np.full(n, np.nan)
        for i, x in enumerate(cand):
            d = x.get(("dir", off), 0)
            if mode == "real":
                if d == 0: continue
                side = d > 0
            else:
                side = (mode == "L")
            r = x.get((off, side, tm))
            if r is not None: R[i], EX[i], RK[i] = r
        return R, EX, RK

    def cost_r(RK, s):
        return 0.70 / (ticket * RK) + 2.0 * s / 1e4 / RK

    def fmt(x, m=None):
        m = np.isfinite(x) if m is None else m & np.isfinite(x)
        v = x[m]
        if len(v) == 0: return "n=0"
        # Tagesclustered SE
        dd = dayi[m]; ud, inv = np.unique(dd, return_inverse=True)
        s = np.bincount(inv, weights=v - v.mean()); se = math.sqrt((s ** 2).sum()) / len(v)
        return "n=%d mean %+.4f R (SE %.4f)" % (len(v), v.mean(), se)

    print("\n[1] Primaer: Kerzenrichtung, Ziel 10 R, Zeitversatz 0, Top-K nach RV5 (brutto R, Tages-clustered SE):")
    R, EX, RK = arrays(0, 10.0, "real")
    for K in (5, 10, 20, 60):
        m = rank <= K
        ex = EX[m & np.isfinite(R)]
        print("  K=%2d: %s | Ausgang Stop %.1f%% / Ziel %.1f%% / Schluss %.1f%% | Kein-Trade-Anteil %.1f%%"
              % (K, fmt(R, m), 100 * (ex == 0).mean(), 100 * (ex == 1).mean(), 100 * (ex == 2).mean(), 100 * (1 - np.isfinite(R[m]).mean())))
    m20 = rank <= 20
    print("\n[2] K=20, nach Jahr (brutto R):")
    for y in (2016, 2017, 2018, 2019): print("  %d: %s" % (y, fmt(R, m20 & (year == y))))
    RL, _, _ = arrays(0, 10.0, "L"); RS, _, _ = arrays(0, 10.0, "S")
    dirs = np.array([x["dir0"] for x in cand])
    print("  Long (Kerze steigend): %s | Short (Kerze fallend): %s" % (fmt(R, m20 & (dirs > 0)), fmt(R, m20 & (dirs < 0))))
    print("\n[3] Ziel-Variante (K=20, brutto R): " + " | ".join("%s: %s" % ("ohne Ziel" if math.isinf(tm) else "%.0f R" % tm, fmt(arrays(0, tm, "real")[0], m20)) for tm in TMS))
    print("\n[4] Placebo Zufallsrichtung (K=20, Ziel 10 R, %d Ziehungen): gleiche Stop-Geometrie, Richtung per Muenzwurf" % draws)
    both = np.isfinite(RL) & np.isfinite(RS) & m20 & (dirs != 0)
    base = []
    for _ in range(draws):
        pick = rng.random(len(RL)) < 0.5
        x = np.where(pick, RL, RS)[both]; base.append(x.mean())
    base = np.array(base); real_m = R[both].mean()
    print("  Handelbar in beiden Richtungen: n=%d | echte Kerzenrichtung %+.4f R | Zufallsrichtung Mittel %+.4f R (q2.5 %+.4f / q97.5 %+.4f) | Differenz %+.4f R"
          % (both.sum(), real_m, base.mean(), np.percentile(base, 2.5), np.percentile(base, 97.5), real_m - base.mean()))
    print("  Immer Long: %+.4f R | immer Short: %+.4f R (gleiche Menge)" % (RL[both].mean(), RS[both].mean()))
    print("\n[5] Placebo Zeitversatz (K=20, Ziel 10 R, Signalkerze spaeter, gleiche Auswahl):")
    for off in OFFS:
        Ro = arrays(off, 10.0, "real")[0]
        print("  Signalkerze +%2d Bars (%s): %s" % (off, "09:30" if off == 0 else ("10:30" if off == 12 else "12:30"), fmt(Ro, m20)))
    print("\n[6] Kosten (K=20, Ziel 10 R, Ticket %.0f USD): mittlere Provision in R %.4f | Netto-R nach Provision und Slippage je Seite:" % (ticket, np.nanmean(cost_r(RK, 0)[m20 & np.isfinite(R)] - 0)))
    for s in (0, 5, 10, 20):
        net = R - cost_r(RK, s)
        print("  s=%2d bp/Seite: %s" % (s, fmt(net, m20)))
    print("\n[7] Mindest-Risikospanne (Risiko/Entry) und K (Ziel 10 R), Netto-R bei s=5 bp je Seite:")
    for K in (10, 20, 60):
        row = []
        for mr in (0.0, 0.005, 0.01, 0.02):
            m = (rank <= K) & (RK >= mr)
            row.append("Risiko>=%.1f%%: %s" % (100 * mr, fmt(R - cost_r(RK, 5), m)))
        print("  K=%2d | %s" % (K, " | ".join(row)))
    print("\nHinweis: Entwicklungsfenster, viele Varianten gesichtet (K, Ziel, Risiko-Filter, Slippage): jede Auswahl hier ist Exploration ohne alpha-Gewicht; der Test im Testfenster laeuft einmal mit vorab gehashten Parametern.")

if __name__ == "__main__":
    main()
