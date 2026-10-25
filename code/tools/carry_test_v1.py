# carry_test_v1.py - CARRY-HOLD (Spot long / Perp short, Binance-Proxy BTCUSDT+ETHUSDT 50/50), HINWEIS-Klasse (D58): Modi
#   dry   <klines> <funding>                      -> gleiche Auswertung im TRAININGSFENSTER (2019-09-09..2023-12-31), zur Codepruefung (offen)
#   final <klines> <funding> --spec-hash <64 hex>  -> TESTFENSTER 2024-01-01..2026-06-28 (130 volle Wochen), NUR nach Freeze, genau einmal
# Regel (vorab): taegliche Entscheidung auf nachlaufendes 7-Tage-Funding F7 (annualisiert, Info bis d-1): Einstieg wenn F7 > E=10 %, Ausstieg wenn F7 < X=3 %; Wirkung am Tag d.
# P&L je Tag in Position (bp des Notionals): Funding(d) - Aenderung der Basis (ln perp - ln spot); Kosten je Phase 2*40 bp Spot (Maker) + 2*5 bp Perp = 90 bp (Haelfte bei Einstieg, Haelfte bei Ausstieg;
# erzwungener Ausstieg am Fensterende); Kollateralreibung 0.5 bp je Woche in Position [A]. Stress: Spot 80 bp/Seite (Taker) = 170 bp je Phase.
import sys, os, io, csv, zipfile, math, re, hashlib
import numpy as np
from datetime import date, datetime, timedelta, timezone
E_IN, X_OUT = 0.10, 0.03; COST_BASE = 90.0; COST_STRESS = 170.0; FRIC_WEEK = 0.5; BLK = 8; INFL = 1.5; ZCRIT = 1.645
CUT = date(2026, 7, 1)
WIN = {"dry": (date(2019, 9, 9), date(2023, 12, 31)), "final": (date(2024, 1, 1), date(2026, 6, 28))}
def months():
    y, m = 2019, 9
    while (y, m) <= (2026, 6):
        yield "%04d-%02d" % (y, m); m += 1
        if m == 13: y += 1; m = 1
def load(p):
    out = {}; z = zipfile.ZipFile(p)
    for n in z.namelist():
        for row in csv.reader(io.TextIOWrapper(z.open(n), "utf-8")):
            try: t = int(row[0]); c = float(row[4])
            except ValueError: continue
            if t > 10**14: t //= 1000
            d = datetime.fromtimestamp(t / 1000, timezone.utc).date()
            if d < CUT: out[d] = c
    return out
def coin(kd, fd, s, last_month):
    spot = {}; perp = {}
    for mo in months():
        if mo > last_month: break
        for kind, store in (("spot", spot), ("um", perp)):
            fp = os.path.join(kd, "%s_%s_%s.zip" % (kind, s, mo))
            if os.path.exists(fp) and os.path.getsize(fp) > 0: store.update(load(fp))
    fund = {}
    with open(os.path.join(fd, s + ".csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            d = datetime.fromtimestamp(int(r["fundingTimeMs"]) / 1000, timezone.utc).date()
            if d < CUT: fund[d] = fund.get(d, 0.0) + float(r["fundingRate"])
    return spot, perp, fund
def series(spot, perp, fund, a, b):
    days = [a + timedelta(days=i) for i in range((b - a).days + 1)]
    g = np.zeros(len(days)); f7 = np.zeros(len(days)); ok = np.zeros(len(days), bool)
    for i, d in enumerate(days):
        f7[i] = sum(fund.get(d - timedelta(days=k), 0.0) for k in range(1, 8)) / 7 * 365
        p = d - timedelta(days=1)
        if all(x in spot and x in perp for x in (d, p)):
            bch = (math.log(perp[d]) - math.log(spot[d])) - (math.log(perp[p]) - math.log(spot[p]))
            g[i] = fund.get(d, 0.0) * 1e4 - bch * 1e4; ok[i] = True
    return days, g, f7, ok
def schedule(f7, ok):
    pos = np.zeros(len(f7), bool); cur = False
    for i in range(len(f7)):
        want = (f7[i] > E_IN) if not cur else (f7[i] >= X_OUT)
        cur = bool(want); pos[i] = cur
    return pos
def weekly_pl(g, pos, cost):
    prev = np.concatenate([[False], pos[:-1]]); ent = pos & ~prev; ex = (~pos) & prev
    pl = pos * g - cost / 2 * ent - cost / 2 * ex - FRIC_WEEK / 7.0 * pos
    pl[-1] -= cost / 2 * pos[-1]           # erzwungener Ausstieg am Fensterende
    return pl.reshape(-1, 7).sum(axis=1), int(ent.sum()) + int(pos[0])
def boot_se(x, B, rng, L=BLK):
    n = len(x); nb = int(math.ceil(n / L)); st = rng.integers(0, n - L + 1, size=(B, nb))
    idx = (st[:, :, None] + np.arange(L)[None, None, :]).reshape(B, -1)[:, :n]
    return x[idx].mean(axis=1).std(ddof=1)
def rand_sched(pos, rng):
    n = len(pos); runs = []; i = 0
    while i < n:
        if pos[i]:
            j = i
            while j < n and pos[j]: j += 1
            runs.append(j - i); i = j
        else: i += 1
    k = len(runs); free = n - sum(runs)
    if k == 0: return np.zeros(n, bool)
    cuts = np.sort(rng.integers(0, free + 1, size=k)); gaps = np.diff(np.concatenate([[0], cuts])); out = np.zeros(n, bool); t = 0
    order = rng.permutation(k)
    for idx, gap in zip(order, gaps):
        t += int(gap); out[t:t + runs[idx]] = True; t += runs[idx]
    return out
def run(mode, kd, fd, spec_hash, B=10000, seed=20261025, nplac=2000):
    a, b = WIN[mode]; last_month = "2023-12" if mode == "dry" else "2026-06"
    print("Skript-SHA256 %s; Modus %s; Fenster %s .. %s; SPEC-HASH %s" % (hashlib.sha256(open(__file__, "rb").read()).hexdigest()[:16], mode, a, b, spec_hash))
    rng = np.random.default_rng(seed); W = ((b - a).days + 1) // 7
    wk_base = []; wk_str = []; wk_on = []; info = {}; coins = ["BTCUSDT", "ETHUSDT"]; plac = np.zeros((nplac, W))
    spotB = None
    for s in coins:
        spot, perp, fund = coin(kd, fd, s, last_month)
        if s == "BTCUSDT": spotB = spot
        days, g, f7, ok = series(spot, perp, fund, a, b); pos = schedule(f7, ok)
        base, ph = weekly_pl(g, pos, COST_BASE); st, _ = weekly_pl(g, pos, COST_STRESS); on, _ = weekly_pl(g, np.ones(len(pos), bool), COST_BASE)
        wk_base.append(base); wk_str.append(st); wk_on.append(on); info[s] = (ph, int(pos.sum()), float(base.mean()))
        for i in range(nplac): plac[i] += weekly_pl(g, rand_sched(pos, rng), COST_BASE)[0] / 2
    x = np.mean(wk_base, axis=0); xs = np.mean(wk_str, axis=0); xo = np.mean(wk_on, axis=0)
    # RV30-Zustand (BTC, Info bis Wochenbeginn-1): Perzentil gegen die bisherige Historie ab 2019-09
    allp = sorted(d for d in spotB if d <= b); lr = {allp[i]: math.log(spotB[allp[i]] / spotB[allp[i - 1]]) for i in range(1, len(allp)) if (allp[i] - allp[i - 1]).days == 1}
    def rv(d): 
        v = [lr[d - timedelta(days=k)] for k in range(1, 31) if (d - timedelta(days=k)) in lr]
        return float(np.std(v, ddof=1)) if len(v) >= 25 else None
    hist = []; wst = []
    d0 = allp[0] + timedelta(days=31); d = d0
    rvd = {}
    while d <= b: rvd[d] = rv(d); d += timedelta(days=1)
    for w in range(W):
        ws = a + timedelta(days=7 * w); past = [v for dd, v in rvd.items() if dd < ws and v is not None]; cur = rvd.get(ws)
        wst.append(None if (cur is None or len(past) < 60) else (cur >= float(np.median(past))))
    wst = np.array([(-1 if v is None else int(v)) for v in wst])
    m = float(x.mean()); se = boot_se(x, B, rng); zadj = m / (INFL * se) if se > 0 else float("nan")
    h = W // 2; hv = (float(x[:h].mean()), float(x[h:].mean()))
    hi = x[wst == 1]; lo = x[wst == 0]
    q975 = float(np.quantile(plac.mean(axis=1), 0.975)); rank = float((plac.mean(axis=1) < m).mean())
    print("Wochen %d | BTC: Phasen %d, Tage in Pos %d, netto %.2f bp/Woche | ETH: Phasen %d, Tage in Pos %d, netto %.2f bp/Woche" % (W, info["BTCUSDT"][0], info["BTCUSDT"][1], info["BTCUSDT"][2], info["ETHUSDT"][0], info["ETHUSDT"][1], info["ETHUSDT"][2]))
    print("Portfolio netto m = %.2f bp/Woche (%.1f %% p. a. auf Notional); sigma_Woche %.1f; Bootstrap-SE (Bloecke %d) %.2f; z_adj = m/(%.1f*SE) = %.2f (Kriterium >= %.3f)" % (m, m * 52 / 100, float(x.std(ddof=1)), BLK, se, INFL, zadj, ZCRIT))
    print("Haelften %.2f / %.2f | Zustand RV30 hoch %.2f (n=%d) / niedrig %.2f (n=%d) | Stresskosten m = %.2f | immer-an m = %.2f | Placebo (zufaellige Phasenlage gleicher Laengen): q97.5 %.2f, Rang des Ergebnisses %.2f" % (hv[0], hv[1], float(hi.mean()) if len(hi) else float("nan"), len(hi), float(lo.mean()) if len(lo) else float("nan"), len(lo), float(xs.mean()), float(xo.mean()), q975, rank))
    okk = (m > 0) and (zadj >= ZCRIT) and len(hi) >= 10 and len(lo) >= 10 and hi.mean() > 0 and lo.mean() > 0 and xs.mean() > 0
    print("KATEGORIE: %s" % ("HINWEIS-POSITIV (nur Vorwaertsbeobachtung/Paper, kein BESTAETIGT)" if okk else "NICHT NACHWEISBAR (m <= 0 oder Kriterien verfehlt; bei Erwartung nahe der Aufloesung kein Nullbefund)"))
if __name__ == "__main__":
    mode, kd, fd = sys.argv[1], sys.argv[2], sys.argv[3]; a = sys.argv[4:]
    if mode == "dry": run("dry", kd, fd, "DRY-TRAINING-KEIN-FREEZE")
    elif mode == "final":
        h = a[a.index("--spec-hash") + 1] if "--spec-hash" in a else ""
        if not re.fullmatch(r"[0-9a-f]{64}", h): sys.exit("final nur mit --spec-hash <sha256>")
        run("final", kd, fd, h)
