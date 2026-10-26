# orb_test_v1.py - ORB (Opening Range Breakout, Stocks in Play) Test, HINWEIS-Klasse (kein alpha). Modi:
#   dry   : Entwicklungsfenster 2016-01-01..2019-12-31 (Pruefung, dass Code = Entwicklungs-Simulation; keine Entscheidung)
#   final : Testfenster 2020-01-01..2026-06-30, EINMAL, nur mit --spec-hash <64 hex Freeze-Hash>
# Aufruf: python -u orb_test_v1.py dry|final <day5-Ordner> <auswahl-csv> [--spec-hash H]
# Regel (vorab festgelegt, Spec RUNDE3F): Top-20 je Tag nach RV5; Signalkerze 09:30; Long bei Close>Open, Short bei Close<Open; Einstieg Open der naechsten vorhandenen Bar;
# Stop am Gegenende der Signalkerze; Ziel 10 R; sonst Schluss (letzte Bar); Stop vor Ziel in derselben Bar; Luecke => Fuellung zum Open; Entry jenseits des Stops => kein Trade.
# Kosten: Provision 0,70 USD je Round-Trip bei Ticket 1500 USD, Slippage s bp je Seite (primaer s = 5). Primaer: Netto-R je Trade (s = 5).
# Tagesblock-Bootstrap: zirkulaere Bloecke von 5 Handelstagen, 10000 Ziehungen, Seed 20261026; z_adj = m / (1,3 * SE_boot).
# Kategorie: HINWEIS-POSITIV nur wenn (i) n >= 20000, (ii) Netto-R(s=5) > 0 mit z_adj >= 1,645, (iii) Richtungswert (Kerzenrichtung minus Mittel beider Richtungen, brutto, beide Seiten handelbar)
# > 0 mit z_adj >= 1,645, (iv) beide Haelften (2020-2022, 2023-2026H1) Netto-R(s=5) > 0. n < 20000 => INSUFFICIENT; sonst NICHT NACHWEISBAR. Alle anderen Zahlen nur berichtet.
import sys, os, csv, glob, math, itertools, hashlib
from datetime import date
import numpy as np

WIN = {"dry": ("2016-01-01", "2019-12-31"), "final": ("2020-01-01", "2026-06-30")}
K_TOP = 20; TICKET = 1500.0; COMM = 0.70; S_PRIMARY = 5.0; L_BLK = 5; B_DRAWS = 10000; SEED = 20261026; INFL = 1.3; ZCRIT = 1.645; N_MIN = 20000; TM = 10.0

def nth_sunday(y, m, n):
    d = date(y, m, 1); d = d.fromordinal(d.toordinal() + (6 - d.weekday()) % 7)
    return d.fromordinal(d.toordinal() + 7 * (n - 1))
_OFF = {}
def day_off(day):
    if day not in _OFF:
        y, m, d = map(int, day.split("-")); dt = date(y, m, d)
        _OFF[day] = 4 if nth_sunday(y, 3, 2) <= dt < nth_sunday(y, 11, 1) else 5
    return _OFF[day]

def scan(o, h, l, c, k, long_, tm):
    e = k + 1
    if e >= len(o): return None
    entry = o[e]
    if long_: stop = l[k]; dist = entry - stop
    else: stop = h[k]; dist = stop - entry
    if not (dist > 0): return None
    hs = (l[e:] <= stop) if long_ else (h[e:] >= stop)
    tgt = entry + tm * dist if long_ else entry - tm * dist
    ht = (h[e:] >= tgt) if long_ else (l[e:] <= tgt)
    it = ht.argmax() if ht.any() else -1
    is_ = hs.argmax() if hs.any() else -1
    if is_ >= 0 and (it < 0 or is_ <= it): px = min(stop, o[e + is_]) if long_ else max(stop, o[e + is_])
    elif it >= 0: px = max(tgt, o[e + it]) if long_ else min(tgt, o[e + it])
    else: px = c[-1]
    return ((px - entry) / dist if long_ else (entry - px) / dist), dist / entry

def boot(sums, cnts, rng):
    """Tagesblock-Bootstrap des Mittels (Verhaeltnis-Schaetzer); liefert SE."""
    nd = len(sums); nb = int(math.ceil(nd / L_BLK)); res = []
    cs = np.concatenate([[0.0], np.cumsum(sums)]); cc = np.concatenate([[0.0], np.cumsum(cnts)])
    for _ in range(B_DRAWS // 1000):
        st = rng.integers(0, nd, size=(1000, nb))
        idx = (st[:, :, None] + np.arange(L_BLK)[None, None, :]) % nd
        s = sums[idx].sum(axis=(1, 2)); n = cnts[idx].sum(axis=(1, 2))
        res.append(s / np.maximum(n, 1))
    return float(np.std(np.concatenate(res), ddof=1))

def main():
    a = sys.argv[1:]
    if len(a) < 3 or a[0] not in WIN: sys.exit(__doc__)
    mode = a[0]; lo_d, hi_d = WIN[mode]
    if mode == "final":
        if "--spec-hash" not in a or len(a[a.index("--spec-hash") + 1]) != 64: sys.exit("final braucht --spec-hash <64 hex> (Freeze-Hash).")
        print("Freeze-Hash: " + a[a.index("--spec-hash") + 1])
    sel = {}
    with open(a[2], newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if lo_d <= r["date"] <= hi_d and int(r["rank"]) <= K_TOP: sel[(r["date"], r["symbol"])] = int(r["rank"])
    days = sorted(set(k[0] for k in sel)); dix = {d: i for i, d in enumerate(days)}
    cand = []
    for fn in sorted(glob.glob(os.path.join(a[1], "day5_*.csv"))):
        ym = os.path.basename(fn)[5:12]
        if ym < lo_d[:7] or ym > hi_d[:7]: continue
        with open(fn, newline="") as f:
            rd = csv.reader(f); next(rd, None)
            for (day, sym), g in itertools.groupby(rd, key=lambda r: (r[0], r[1])):
                if (day, sym) not in sel: continue
                g = list(g); oh = day_off(day)
                slot = np.array([(int(r[2][11:13]) * 60 + int(r[2][14:16]) - oh * 60 - 570) // 5 for r in g])
                if slot[0] != 0: continue
                o = np.array([float(r[3]) for r in g]); h = np.array([float(r[4]) for r in g]); l = np.array([float(r[5]) for r in g]); c = np.array([float(r[6]) for r in g])
                it = {"day": dix[day], "rank": sel[(day, sym)], "year": int(day[:4]), "dir": 0 if c[0] == o[0] else (1 if c[0] > o[0] else -1)}
                it["L"] = scan(o, h, l, c, 0, True, TM); it["S"] = scan(o, h, l, c, 0, False, TM)
                if len(o) > 1: it["ret"] = c[-1] / o[1] - 1.0
                k12 = np.searchsorted(slot, 12)
                if k12 < len(slot) and slot[k12] == 12:
                    d12 = 0 if c[k12] == o[k12] else (1 if c[k12] > o[k12] else -1)
                    if d12 != 0:
                        r12 = scan(o, h, l, c, k12, d12 > 0, TM)
                        if r12 is not None: it["p12"] = r12[0]
                cand.append(it)
    N = len(cand)
    print("Skript: orb_test_v1.py | Modus %s | Fenster %s..%s | Auswahl-Symbol-Tage %d | mit Ganztagsdaten %d | Handelstage %d" % (mode, lo_d, hi_d, len(sel), N, len(days)))
    nd = len(days)
    dayi = np.array([x["day"] for x in cand]); rank = np.array([x["rank"] for x in cand]); year = np.array([x["year"] for x in cand])
    R = np.full(N, np.nan); RK = np.full(N, np.nan); RL = np.full(N, np.nan); RS = np.full(N, np.nan); RKL = np.full(N, np.nan); RKS = np.full(N, np.nan)
    for i, x in enumerate(cand):
        if x["L"] is not None: RL[i], RKL[i] = x["L"]
        if x["S"] is not None: RS[i], RKS[i] = x["S"]
        if x["dir"] > 0 and x["L"] is not None: R[i], RK[i] = x["L"]
        if x["dir"] < 0 and x["S"] is not None: R[i], RK[i] = x["S"]
    rng = np.random.default_rng(SEED)

    def cost(s): return COMM / (TICKET * RK) + 2.0 * s / 1e4 / RK
    def stat(x, m=None, label=""):
        m = np.isfinite(x) if m is None else (m & np.isfinite(x))
        v = x[m]; d = dayi[m]
        sums = np.bincount(d, weights=v, minlength=nd); cnts = np.bincount(d, minlength=nd).astype(float)
        mu = v.mean() if len(v) else float("nan")
        se = boot(sums, cnts, np.random.default_rng(SEED)) if len(v) > 50 else float("nan")
        z = mu / (INFL * se) if se and se > 0 else float("nan")
        return len(v), mu, se, z
    def line(lab, x, m=None):
        n, mu, se, z = stat(x, m)
        return "%s: n=%d mean %+.4f R (SE %.4f, z_adj %+.2f)" % (lab, n, mu, se, z)

    ex = np.isfinite(R)
    print("\n[Primaer] Kerzenrichtung, K=20, Ziel 10 R, Ticket %.0f USD" % TICKET)
    n0, g_mu, g_se, g_z = stat(R); print("  " + line("Brutto", R))
    NET = {s: R - cost(s) for s in (0.0, 5.0, 10.0)}
    for s in (0.0, 5.0, 10.0): print("  " + line("Netto s=%.0f bp/Seite" % s, NET[s]))
    n_net, m_net, se_net, z_net = stat(NET[S_PRIMARY])
    print("  mittlere Provision in R: %.4f | Kein-Trade-Anteil: %.2f%%" % (np.nanmean(COMM / (TICKET * RK[ex])), 100 * (1 - ex.mean())))
    both = np.isfinite(RL) & np.isfinite(RS) & ex
    dv = np.full(N, np.nan); dv[both] = R[both] - 0.5 * (RL[both] + RS[both])
    n_d, m_d, se_d, z_d = stat(dv)
    print("\n[Richtungswert] Kerzenrichtung minus Mittel beider Richtungen (brutto, gleiche Stop-Geometrie):")
    print("  " + line("Differenz", dv)); print("  Immer Long %+.4f R | immer Short %+.4f R | echte Richtung %+.4f R (gleiche %d Trades)" % (np.nanmean(RL[both]), np.nanmean(RS[both]), np.nanmean(R[both]), both.sum()))
    hA = year <= 2022 if mode == "final" else year <= 2017
    nA, mA, _, zA = stat(NET[S_PRIMARY], hA); nB, mB, _, zB = stat(NET[S_PRIMARY], ~hA)
    print("\n[Haelften] Netto-R (s=5): %s %+.4f R (n=%d, z %+.2f) | %s %+.4f R (n=%d, z %+.2f)" % ("A" if mode == "final" else "A(2016-17)", mA, nA, zA, "B" if mode == "final" else "B(2018-19)", mB, nB, zB))
    print("\n[Nur berichtet]")
    for y in sorted(set(year)): print("  Jahr %d: %s" % (y, line("brutto", R, year == y)))
    dirs = np.array([x["dir"] for x in cand])
    print("  " + line("Long (Kerze steigend) brutto", R, dirs > 0)); print("  " + line("Short (Kerze fallend) brutto", R, dirs < 0))
    for K in (5, 10): print("  " + line("K=%d Netto s=5" % K, NET[S_PRIMARY], rank <= K))
    p12 = np.array([x.get("p12", np.nan) for x in cand]); print("  " + line("Zeitversatz-Placebo 10:30 brutto", p12))
    ret = np.array([x.get("ret", np.nan) for x in cand]) * 1e4; dd = dirs
    mm = np.isfinite(ret) & (dd != 0)
    v = ret[mm] * dd[mm]; sums = np.bincount(dayi[mm], weights=v, minlength=nd); cn = np.bincount(dayi[mm], minlength=nd).astype(float)
    print("  Diagnose ohne Stops (Open 2. Bar bis Schluss), Kerzenrichtung: n=%d %+.1f bp (SE %.1f)" % (mm.sum(), v.mean(), boot(sums, cn, np.random.default_rng(SEED))))
    crit = [("n >= %d" % N_MIN, n_net >= N_MIN), ("Netto-R(s=5) > 0 und z_adj >= %.3f" % ZCRIT, m_net > 0 and z_net >= ZCRIT),
            ("Richtungswert > 0 und z_adj >= %.3f" % ZCRIT, m_d > 0 and z_d >= ZCRIT), ("beide Haelften Netto-R > 0", mA > 0 and mB > 0)]
    print("\n[Kriterien]")
    for t, ok in crit: print("  %-52s %s" % (t, "JA" if ok else "NEIN"))
    if n_net < N_MIN: cat = "INSUFFICIENT"
    elif all(ok for _, ok in crit): cat = "HINWEIS-POSITIV"
    else: cat = "NICHT NACHWEISBAR"
    print("\nKATEGORIE: %s (HINWEIS-Klasse, kein alpha; Modus %s)" % (cat, mode))
    if mode == "dry": print("Hinweis: dry = Entwicklungsfenster, nur Code-Pruefung gegen orb_dev_sim (erwartet bei K=20 brutto n=19207, +0,0562 R); keine Entscheidung.")

if __name__ == "__main__":
    main()
