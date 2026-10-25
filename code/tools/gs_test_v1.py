# gs_test_v1.py - GOLD-SILBER (GLD/SLV) woechentlicher Spread-Test, HINWEIS-Klasse (kein alpha-Konto). Modi:
#   calib <bars-ordner> [--nnull 200] [--boot 10000] [--seed 20261025]
#   final <bars-ordner> --spec-hash <64 hex>      (NUR nach Freeze; genau einmal)
import sys, os, csv, math, re, hashlib
import numpy as np
from datetime import date
COST = 6.0        # bp je Woche: 4 ETF-Seiten x 1,5 bp [A]
BLOCK = 4; CUT = date(2026, 7, 1)
def load(folder, sym):
    rows = []
    with open(os.path.join(folder, sym + ".csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            x = date.fromisoformat(r["date"])
            if x >= CUT: continue
            rows.append((x, float(r["open"]), float(r["close"])))
    return rows
def weekly(folder):
    g = {x: (o, c) for x, o, c in load(folder, "GLD")}; s = {x: (o, c) for x, o, c in load(folder, "SLV")}
    days = sorted(set(g) & set(s)); wk = {}
    for d in days:
        key = d.isocalendar()[:2]; wk.setdefault(key, []).append(d)
    keys = sorted(wk); RG = []; RS = []; WD = []
    for k in keys:
        a, b = wk[k][0], wk[k][-1]
        RG.append(math.log(g[b][1] / g[a][0])); RS.append(math.log(s[b][1] / s[a][0])); WD.append(a.toordinal())
    return np.array(RG), np.array(RS), np.array(WD)
def build(RG, RS):
    n = len(RG); beta = np.full(n, np.nan)
    for k in range(52, n):
        x = RG[k - 52:k]; y = RS[k - 52:k]; beta[k] = np.cov(y, x)[0, 1] / np.var(x, ddof=1)
    sp = RS - beta * RG                      # Spread-Rendite der Woche k mit dem zu Wochenbeginn bekannten Beta
    sig = np.full(n, np.nan)      # Signal: Vorzeichen des Spreads der Vorwoche mit dem zu Beginn der Handelswoche bekannten Beta
    for k in range(53, n): sig[k] = np.sign(RS[k - 1] - beta[k] * RG[k - 1])
    return sp * 1e4, sig
def side(sp, sig, which):
    ok = ~np.isnan(sp) & ~np.isnan(sig) & (sig != 0)
    d = sig if which == "C" else -sig
    return np.where(ok, d * sp, np.nan), ok
def boot(x, B, rng, block=BLOCK):
    n = len(x); nb = int(math.ceil(n / block)); st = rng.integers(0, n - block + 1, size=(B, nb))
    idx = (st[:, :, None] + np.arange(block)[None, None, :]).reshape(B, -1)[:, :n]
    return x[idx].mean(axis=1)
def evaluate(x, B, rng, plac_q, cost_mult_x):
    m = float(x.mean()); bm = boot(x, B, rng); p = float(np.mean(bm <= 0)); lcb = float(np.quantile(bm, 0.05))
    h = len(x) // 2; halves = (float(x[:h].mean()), float(x[h:].mean()))
    ok = (m > 0) and (p <= 0.05) and (m > plac_q) and halves[0] > 0 and halves[1] > 0 and cost_mult_x > 0
    return m, p, lcb, halves, ok
def placebo_means(sp, sig, which, rng, k):
    out = []
    n = len(sp)
    for _ in range(k):
        sh = int(rng.integers(8, 53)) * (1 if rng.random() < 0.5 else -1)
        s2 = np.full(n, np.nan)
        if sh > 0: s2[sh:] = sig[:-sh]
        else: s2[:sh] = sig[-sh:]
        x, ok = side(sp, s2, which); x = x[ok] - COST
        if len(x) > 100: out.append(x.mean())
    return np.array(out)
def prep(folder):
    RG, RS, WD = weekly(folder); sp, sig = build(RG, RS); return sp, sig, WD
def final(folder, spec_hash, B, seed, nplac):
    print("Skript-SHA256 %s" % hashlib.sha256(open(__file__, "rb").read()).hexdigest()[:16]); print("SPEC-HASH %s" % spec_hash)
    rng = np.random.default_rng(seed); sp, sig, WD = prep(folder)
    for which, name in (("C", "GS-C Fortsetzung (Spread-Richtung der Vorwoche)"), ("R", "GS-R Umkehr")):
        x, ok = side(sp, sig, which); x = x[ok]
        net = x - COST; pl = placebo_means(sp, sig, which, rng, nplac); q = float(np.quantile(pl, 0.975))
        net15 = x - 1.5 * COST
        m, p, lcb, hv, okk = evaluate(net, B, rng, q, float(net15.mean()))
        print("%s: Wochen %d (%s .. %s); brutto %.1f bp/Woche; netto m = %.1f bp/Woche (%.1f %% p. a.); p(einseitig) = %.4f; LCB95 = %.1f; Placebo-q97.5 = %.1f; Haelften %.1f / %.1f; Kosten x1,5: %.1f" % (
            name, len(net), date.fromordinal(int(WD[ok][0])), date.fromordinal(int(WD[ok][-1])), float(x.mean()), m, m * 52 / 100, p, lcb, q, hv[0], hv[1], float(net15.mean())))
        print("  KATEGORIE: %s" % ("HINWEIS-POSITIV (nur Vorwaertsbeobachtung, kein BESTAETIGT)" if okk else ("NICHT NACHWEISBAR (m <= 0 oder Kriterien verfehlt; kein Nullbefund bei Kante < MDE)")))
def calib(folder, nnull, B, seed):
    print("Skript-SHA256 %s (calib)" % hashlib.sha256(open(__file__, "rb").read()).hexdigest()[:16])
    rng = np.random.default_rng(seed); sp, sig, WD = prep(folder)
    for which in ("C", "R"):
        x0, ok0 = side(sp, sig, which); n = int(ok0.sum()); sd = float(np.std(x0[ok0], ddof=1))
        mde = 2.487 * sd / math.sqrt(n)
        print("Seite %s: n = %d, Streuung je Woche %.0f bp, MDE80 (einseitig 0,05) = %.1f bp/Woche (%.1f %% p. a.)" % (which, n, sd, mde, mde * 52 / 100))
        for lab, dlt in (("0", 0.0), ("0.5*MDE", 0.5 * mde), ("MDE", mde), ("2*MDE", 2 * mde)):
            hit = 0; tot = 0
            for _ in range(nnull):
                sh = int(rng.integers(8, 53)) * (1 if rng.random() < 0.5 else -1); s2 = np.full(len(sp), np.nan)
                if sh > 0: s2[sh:] = sig[:-sh]
                else: s2[:sh] = sig[-sh:]
                x, ok = side(sp, s2, which); x = x[ok]
                if len(x) < 100: continue
                tot += 1; xa = x - x.mean() + dlt          # dlt = wahre NETTO-Kante
                pl = placebo_means(sp, sig, which, rng, 100); q = float(np.quantile(pl - pl.mean(), 0.975))   # zentriert: Nullwelt-Mittel schwankt um 0
                m, p, lcb, hv, okk = evaluate(xa, B, rng, q, float(dlt - 0.5 * COST))
                hit += int(okk)
            print("  delta = %-8s (%.1f bp netto): Regel bestanden %d/%d = %.1f %%" % (lab, dlt, hit, tot, 100.0 * hit / max(1, tot)), flush=True)
if __name__ == "__main__":
    mode, folder = sys.argv[1], sys.argv[2]; a = sys.argv[3:]
    def opt(k, d, f=float): return f(a[a.index(k) + 1]) if k in a else d
    if mode == "calib": calib(folder, opt("--nnull", 200, int), opt("--boot", 2000, int), opt("--seed", 20261025, int))
    elif mode == "final":
        h = opt("--spec-hash", "", str)
        if not re.fullmatch(r"[0-9a-f]{64}", h): sys.exit("final nur mit --spec-hash <sha256>")
        final(folder, h, opt("--boot", 10000, int), opt("--seed", 20261025, int), opt("--nplac", 2000, int))
