# insider_test_v1.py - Testmechanik INSIDER-ALL (Insider-Cluster k>=3, US-Aktien, Long 28 Kalendertage, Netto-Excess gegen SPY)
# Aufruf (im Ordner tools):
#   python insider_test_v1.py count <cluster-csv> <bars-ordner>                                  (NUR Zaehlungen und zentrierte Streuung, keine Vorzeichen-Statistik)
#   python insider_test_v1.py calib <cluster-csv> <bars-ordner> --sigma <bp> [--nnull 200] [--nplac 2000] [--nsame 500] [--boot 10000] [--alpha 0.0025] [--seed 20261025]
#   python insider_test_v1.py final <cluster-csv> <bars-ordner> --spec-hash <64 hex>              (NUR nach Freeze)
# Alle Kosten sind Annahmen [A] (Spec). Hartes Ende: Bars ab 2026-07-01 werden beim Laden verworfen.
import sys, os, csv, math, time, re, hashlib
import numpy as np
from datetime import date

T0 = time.time()
def log(s): print("[%5d s] %s" % (time.time() - T0, s), flush=True)
EPOCH = date(1970, 1, 1).toordinal()
def di(s): return date.fromisoformat(s).toordinal() - EPOCH
def iso(n): return date.fromordinal(int(n) + EPOCH).isoformat()
START = di("2016-09-01"); END = di("2026-05-31"); CUT_BAR = di("2026-07-01")
HOLD = 28; HEDGE = 4.0; DV_MIN = 3e5; MINPRICE = 2.0
TIER_COST = {1: 100.0, 2: 50.0, 3: 25.0}          # Rundreise bp je Dollarvolumen-Klasse (Median 20 Tage: 300k-2M, 2M-10M, >=10M) [A]
WEEK = 7; BLOCK = 6; TOP_N = 10; TOP_SHARE = 0.25; MIN_STATE = 100

class Bars:
    def __init__(self, folder): self.folder = folder; self.cache = {}
    def get(self, sym):
        if sym in self.cache: return self.cache[sym]
        r = None
        for nm in (sym.replace("/", "_"), sym.replace("-", ".")):
            p = os.path.join(self.folder, nm + ".csv")
            if os.path.exists(p):
                d = []; o = []; c = []; v = []
                with open(p, newline="", encoding="utf-8") as f:
                    for row in csv.DictReader(f):
                        x = di(row["date"])
                        if x >= CUT_BAR: continue
                        d.append(x); o.append(float(row["open"])); c.append(float(row["close"])); v.append(float(row["volume"]))
                if len(d) >= 30: r = (np.array(d, dtype=np.int64), np.array(o), np.array(c), np.array(v))
                break
        self.cache[sym] = r
        return r

def spy_state(spy):
    d, o, c, v = spy
    r = np.diff(np.log(c), prepend=np.nan)
    rv = np.full(len(d), np.nan)
    for k in range(30, len(d)):
        rv[k] = np.std(r[k - 29:k + 1], ddof=1) * math.sqrt(252)
    st = np.full(len(d), -1, dtype=np.int64)
    for k in range(1, len(d)):
        val = rv[k - 1]
        if np.isnan(val): continue
        hist = rv[max(0, k - 1 - 756):k - 1]; hist = hist[~np.isnan(hist)]
        if len(hist) < 120: continue
        p = float(np.mean(hist < val))
        st[k] = 0 if p < 1 / 3 else (2 if p > 2 / 3 else 1)
    return st

class World:
    def __init__(self, csvp, folder, hedge="SPY"):
        self.B = Bars(folder)
        self.spy = self.B.get("SPY")
        if self.spy is None: sys.exit("SPY.csv fehlt im Bars-Ordner (alpaca_daily_v1.py ... --extra SPY,IWM)")
        self.hedge = hedge
        if hedge == "SPY": self.hd = (self.spy[0], self.spy[1])
        else:
            iwm = self.B.get("IWM")
            if iwm is None: sys.exit("IWM.csv fehlt im Bars-Ordner")
            if hedge == "IWM": self.hd = (iwm[0], iwm[1])
            elif hedge == "IWMB":     # IWM mit Beta (120 Bars vor Clusterdatum, Mischung 0,5*Beta + 0,5*1, Grenzen 0..3)
                self.hd = (iwm[0], iwm[1]); self.hc = iwm[2]
            elif hedge == "MIX":      # 50/50 geometrisch, nur gemeinsame Handelstage
                common, ia, ib = np.intersect1d(self.spy[0], iwm[0], return_indices=True)
                self.hd = (common, np.sqrt(self.spy[1][ia] * iwm[1][ib]))
            else: sys.exit("--hedge SPY|IWM|IWMB|MIX")
        self.sst = spy_state(self.spy)
        rows = []
        with open(csvp, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if int(r["kmin"]) != 3 or float(r["avg_price"]) < MINPRICE: continue
                cd = di(r["cluster_date"])
                if not (START <= cd <= END): continue
                s = r["symbol"].strip().upper()
                if not s or " " in s or s in ("NONE", "N/A", "NA"): continue
                rows.append((s, cd))
        self.events = []          # (sym, cd, tier)
        self.miss_dates = []
        self.n_gap = 0
        for s, cd in rows:
            b = self.B.get(s)
            if b is None: self.miss_dates.append(cd); continue
            tier = self.tier(b, cd)
            if tier is None: self.n_gap += 1; continue
            if self.trade(s, cd, 0) is None: self.n_gap += 1; continue
            if self.state(cd) < 0: self.n_gap += 1; continue
            self.events.append((s, cd, tier))
        self.W = int((END + 400 - START) // WEEK) + 1
        self.by_sym = {}
        for s, cd, t in self.events: self.by_sym.setdefault(s, []).append(cd)

    def tier(self, b, cd):
        d, o, c, v = b
        i0 = int(np.searchsorted(d, cd, side="right"))
        if i0 < 16: return None
        lo = max(0, i0 - 20)
        if cd - d[lo] > 40: return None
        dv = float(np.median(c[lo:i0] * v[lo:i0]))
        if dv < DV_MIN: return None
        return 1 if dv < 2e6 else (2 if dv < 1e7 else 3)

    def state(self, cd):
        k = int(np.searchsorted(self.spy[0], cd, side="right")) - 1
        return int(self.sst[k]) if k >= 0 else -1

    def beta(self, d, c, cd):
        i0 = int(np.searchsorted(d, cd, side="right"))
        lo = max(1, i0 - 120)
        if i0 - lo < 60: return 1.0
        hd, hc = self.hd[0], self.hc
        a = np.searchsorted(hd, d[lo - 1:i0]); 
        if a.max() >= len(hd) or not np.all(hd[a] == d[lo - 1:i0]): return 1.0
        rs = np.diff(np.log(c[lo - 1:i0])); rh = np.diff(np.log(hc[a]))
        v = float(np.var(rh))
        if v <= 0: return 1.0
        b = float(np.cov(rs, rh)[0, 1]) / v
        return min(3.0, max(0.0, 0.5 * b + 0.5))

    def trade(self, sym, cd, delay):
        """liefert (Excess gegen SPY vor Kosten in bp, early) oder None"""
        b = self.B.get(sym)
        if b is None: return None
        d, o, c, v = b
        i = int(np.searchsorted(d, cd, side="right")) + delay
        if i >= len(d): return None
        e = int(d[i])
        if e - cd > 6 + 3 * delay or o[i] <= 0: return None
        tgt = e + HOLD
        j = int(np.searchsorted(d, tgt, side="left"))
        early = False
        if j < len(d):
            if d[j] - tgt > 6 or o[j] <= 0: return None
            px = o[j]; ed = int(d[j])
        else:
            if d[-1] <= e + 3 or c[-1] <= 0: return None
            px = c[-1]; ed = int(d[-1]); early = True
        sd, so = self.hd
        k = int(np.searchsorted(sd, e, side="left")); kk = int(np.searchsorted(sd, ed, side="left"))
        if k >= len(sd) or kk >= len(sd) or sd[k] - e > 5 or sd[kk] - ed > 5: return None
        bt = self.beta(d, c, cd) if self.hedge == "IWMB" else 1.0
        return (math.log(px / o[i]) - bt * math.log(so[kk] / so[k])) * 1e4, early

    def net(self, rex, tier, mult=1.0, t1x=1.0):
        c = TIER_COST[tier] * (t1x if tier == 1 else 1.0)
        return rex - mult * (c + HEDGE)

    def arrays(self, cds=None, delay=0, mult=1.0, t1x=1.0):
        """Ereignisse (optional mit verschobenen Clusterdaten cds) -> T (Clusterdatum), S (Zustand), X (Netto-bp), n_early"""
        T = []; S = []; X = []; ne = 0
        for idx, (s, cd0, tier) in enumerate(self.events):
            cd = cd0 if cds is None else cds[idx]
            if not (START <= cd <= END): continue
            st = self.state(cd)
            if st < 0: continue
            r = self.trade(s, cd, delay)
            if r is None: continue
            T.append(cd); S.append(st); X.append(self.net(r[0], tier, mult, t1x)); ne += int(r[1])
        return np.array(T, dtype=np.int64), np.array(S, dtype=np.int64), np.array(X), ne

    def shifted(self, dw, **kw):
        return self.arrays([cd + 7 * dw for _, cd, _ in self.events], **kw)

    def same_symbol(self, rng, **kw):
        cds = []
        for s, cd, tier in self.events:
            d = self.B.get(s)[0]
            cand = d[(d >= START) & (d <= END)]
            real = np.array(self.by_sym[s])
            ok = np.ones(len(cand), dtype=bool)
            for x in real: ok &= np.abs(cand - x) > 60
            cand = cand[ok]
            cds.append(int(cand[rng.integers(len(cand))]) if len(cand) else -10 ** 9)
        return self.arrays(cds, **kw)

def week_arrays(T, X, W):
    wk = np.clip(((T - START) // WEEK).astype(np.int64), 0, W - 1)
    return np.bincount(wk, weights=X, minlength=W), np.bincount(wk, minlength=W).astype(float)

def boot_means(T, X, W, B, rng, block=BLOCK):
    S, N = week_arrays(T, X, W)
    nb = int(math.ceil(W / block))
    starts = rng.integers(0, W - block + 1, size=(B, nb))
    idx = starts[:, :, None] + np.arange(block)[None, None, :]
    return S[idx].sum(axis=(1, 2)) / np.maximum(N[idx].sum(axis=(1, 2)), 1.0)

def c2(T, X, W, B, rng, alpha):
    if len(X) < 30: return False, 1.0, float("nan")
    bm = boot_means(T, X, W, B, rng)
    p = float(np.mean(bm <= 0)); lcb = float(np.quantile(bm, alpha))
    return (p <= alpha and lcb > 0), p, lcb

def c5(T, X):
    if len(X) == 0 or X.mean() <= 0: return False
    pos = np.sort(X[X > 0])[::-1]; gp = pos.sum()
    if gp <= 0 or pos[:TOP_N].sum() > TOP_SHARE * gp: return False
    yrs = np.array([int(iso(t)[:4]) for t in T]); tot = X.sum()
    return all(X[yrs == y].sum() <= 0.5 * tot for y in np.unique(yrs))

def c6(T, S, X):
    n = len(X)
    if n < 50: return False
    a = np.argsort(T); X2 = X[a]; S2 = S[a]
    if not (X2[: n // 2].mean() > 0 and X2[n // 2:].mean() > 0): return False
    return sum(1 for s in (0, 1, 2) if (S2 == s).sum() >= MIN_STATE and X2[S2 == s].mean() > 0) >= 2

def make_shifts(rng, k):
    return [int(rng.integers(8, 105)) * (1 if rng.random() < 0.5 else -1) for _ in range(k)]

def variants(w, cds=None, n_miss=0):
    """C4: (a) Kosten x1,5; (b) Einstieg einen Handelstag spaeter; (c) Kosten Klasse 1 x2; (d) Survivorship: fehlende Ereignisse mit 10-%-Quantil"""
    res = {}
    res["a"] = float(w.arrays(cds, mult=1.5)[2].mean())
    res["b"] = float(w.arrays(cds, delay=1)[2].mean())
    res["c"] = float(w.arrays(cds, t1x=2.0)[2].mean())
    X = w.arrays(cds)[2]
    q10 = float(np.quantile(X, 0.10))
    res["d"] = float((X.sum() + n_miss * q10) / (len(X) + n_miss))
    return res

def counts(w):
    T, S, X, ne = w.arrays()
    print("Ereignisse (k>=3, Preis>=2, 2016-09..2026-05) mit Bars-Datei und gueltiger Handelbarkeit: %d; ohne Bars-Datei: %d; Luecke/Liquiditaet/Zustand fehlt: %d" % (len(w.events), len(w.miss_dates), w.n_gap))
    print("davon Bars enden vor Haltedauerende (early): %d" % ne)
    print("Klassen (Dollarvolumen 300k-2M / 2M-10M / >=10M): %s" % [sum(1 for e in w.events if e[2] == t) for t in (1, 2, 3)])
    print("Zustaende SPY-RV30 (NIEDRIG/MITTEL/HOCH): %s" % [int((S == s).sum()) for s in (0, 1, 2)])
    print("je Jahr: %s" % ", ".join("%d:%d" % (y, sum(1 for t in T if iso(t)[:4] == str(y))) for y in range(2016, 2027)))
    print("Wochen mit Ereignis: %d von %d; Emittenten (Symbole): %d" % (len(set(((T - START) // WEEK).tolist())), w.W, len(w.by_sym)))
    print("Streuung der Netto-Excess-Rendite je Ereignis (zentriert): %.0f bp; mittlere Abweichung vom Mittel (|x-m|): %.0f bp" % (float(np.std(X, ddof=1)), float(np.mean(np.abs(X - X.mean())))))

def hedgecmp(csvp, folder, nnull, seed):
    """Waehlt den Hedge ex ante NUR nach Nullwelt-Streuung (Zeitversatz-Nullwelten). Gibt keine Mittelwerte aus, nur Streuungen und Anzahlen."""
    print("Skript-SHA256 %s (hedgecmp)" % hashlib.sha256(open(__file__, "rb").read()).hexdigest()[:16], flush=True)
    for hedge in ("SPY", "IWM", "IWMB", "MIX"):
        rng = np.random.default_rng(seed)
        w = World(csvp, folder, hedge); mm = []; sd = []; n0 = None
        for dw in make_shifts(rng, nnull * 2):
            T, S, X, _ = w.shifted(dw)
            if len(X) < 500: continue
            mm.append(float(X.mean())); sd.append(float(np.std(X, ddof=1)))
            if len(mm) >= nnull: break
        T, S, X, _ = w.arrays()
        print("Hedge %-3s: Ereignisse %d; Streuung je Ereignis (zentriert) %.0f bp; SE analytisch %.1f bp; SE der Nullwelt-Mittel (Streuung ueber %d Welten) %.1f bp; Verhaeltnis %.2f" % (
            hedge, len(X), float(np.std(X, ddof=1)), float(np.std(X, ddof=1)) / math.sqrt(len(X)), len(mm), float(np.std(mm, ddof=1)), float(np.std(mm, ddof=1)) / (float(np.std(X, ddof=1)) / math.sqrt(len(X)))), flush=True)

def calib(csvp, folder, hedge, nnull, nplac, nsame, B, alpha, seed, sigma):
    print("Skript-SHA256 %s (INSIDER-ALL)" % hashlib.sha256(open(__file__, "rb").read()).hexdigest()[:16], flush=True)
    rng = np.random.default_rng(seed)
    w = World(csvp, folder, hedge); log("Welt geladen")
    print("Hedge: %s" % hedge)
    Tr, Sr, Xr, ner = w.arrays()
    print("echte Ereignisse (nur Anzahl): %d; Zustaende %s; fehlend (ohne Bars) %d" % (len(Xr), [int((Sr == s).sum()) for s in (0, 1, 2)], len(w.miss_dates)))
    plac = []
    for dw in make_shifts(rng, nplac):
        T, S, X, _ = w.shifted(dw)
        if len(X) >= 500: plac.append(X.mean())
    plac = np.array(plac); log("Zeitversatz-Placebos fertig")
    same = []
    for _ in range(nsame):
        T, S, X, _ = w.same_symbol(rng)
        if len(X) >= 500: same.append(X.mean())
    same = np.array(same); log("Same-Symbol-Placebos fertig")
    shifts = make_shifts(rng, nnull * 2); nulls = []; sd_ent = []
    for dw in shifts:
        cds = [cd + 7 * dw for _, cd, _ in w.events]
        T, S, X, _ = w.arrays(cds)
        if len(X) < 500: continue
        sd_ent.append(float(np.std(X, ddof=1)))
        nulls.append((T, S, X, variants(w, cds, int(round(len(w.miss_dates) * len(X) / max(1, len(Xr)))))))
        if len(nulls) >= nnull: break
    k = len(nulls); log("Nullwelten fertig")
    M = float(np.mean([x[2].mean() for x in nulls])); Mk = {key: float(np.mean([x[3][key] for x in nulls])) for key in "abcd"}
    sd_ent_null = float(np.mean(sd_ent)); f = sigma / sd_ent_null
    se_emp = f * float(np.std([x[2].mean() for x in nulls], ddof=1))     # empirischer SE des Mittels (inkl. Marktabhaengigkeit)
    se_ana = sigma / math.sqrt(len(Xr))
    z = 2.807 + 0.842
    mde = z * max(se_emp, se_ana)
    print("Nullwelten %d (von %d versucht); Streuung je Ereignis in Nullwelt %.0f bp -> Skalierung auf %.0f bp (Faktor %.2f, Annahme [A]); echte Ereignisse %d; SE des Mittels analytisch %.1f bp, empirisch (Nullwelten) %.1f bp; MDE(80 %%) = %.0f bp (groesserer SE)" % (
        k, len(shifts), sd_ent_null, sigma, f, len(Xr), se_ana, se_emp, mde), flush=True)
    q_plac = f * np.quantile(plac - plac.mean(), 0.975); q_same = f * np.quantile(same - same.mean(), 0.975)
    print("Placebo-Mengen: zeitversetzt %d, same-symbol %d" % (len(plac), len(same)))
    print("Operationscharakteristik der Gesamtregel (alle C2..C6; wahre Netto-Kante delta, Nullwelten rezentriert und skaliert):")
    for lab, dlt in (("0", 0.0), ("0.5*MDE", 0.5 * mde), ("MDE", mde), ("2*MDE", 2 * mde)):
        cnt = dict(c2=0, c3=0, c4=0, c5=0, c6=0, all=0)
        for T, S, X, v in nulls:
            Xa = f * (X - M) + dlt
            ok2, p, lcb = c2(T, Xa, w.W, B, rng, alpha); m = Xa.mean()
            ok3 = (m > q_plac) and (m > q_same)
            ok4 = all((f * (v[key] - Mk[key]) + dlt + (Mk[key] - M)) > 0 for key in "abcd")
            ok5 = c5(T, Xa); ok6 = c6(T, S, Xa)
            for key, val in (("c2", ok2), ("c3", ok3), ("c4", ok4), ("c5", ok5), ("c6", ok6)): cnt[key] += int(val)
            cnt["all"] += int(ok2 and ok3 and ok4 and ok5 and ok6)
        print("  delta=%-8s (%.0f bp): bestanden gesamt %d/%d = %.1f %%; einzeln C2 %d, C3 %d, C4 %d, C5 %d, C6 %d" % (
            lab, dlt, cnt["all"], k, 100.0 * cnt["all"] / k, cnt["c2"], cnt["c3"], cnt["c4"], cnt["c5"], cnt["c6"]), flush=True)
    print("Hinweis: bei delta=0 ist die erwartete Fehlpass-Rate durch C2 (alpha_i) und C3 begrenzt; Soll <= 5 %.")

def final(csvp, folder, hedge, spec_hash, B, alpha, seed, nplac, nsame):
    print("Skript-SHA256 %s" % hashlib.sha256(open(__file__, "rb").read()).hexdigest()[:16])
    print("SPEC-HASH %s" % spec_hash, flush=True)
    rng = np.random.default_rng(seed)
    w = World(csvp, folder, hedge)
    print("Hedge: %s" % hedge)
    T, S, X, ne = w.arrays()
    ok2, p, lcb = c2(T, X, w.W, B, rng, alpha)
    plac = np.array([m for m in (w.shifted(dw)[2].mean() if len(w.shifted(dw)[2]) >= 500 else np.nan for dw in make_shifts(rng, nplac)) if not np.isnan(m)])
    same = np.array([w.same_symbol(rng)[2].mean() for _ in range(nsame)])
    v = variants(w, None, len(w.miss_dates))
    m = float(X.mean()); q1 = float(np.quantile(plac, 0.975)); q2 = float(np.quantile(same, 0.975))
    ok3 = (m > q1) and (m > q2); ok4 = all(x > 0 for x in v.values()); ok5 = c5(T, X); ok6 = c6(T, S, X)
    print("Ereignisse %d (early %d, fehlend ohne Bars %d); Zustaende %s" % (len(X), ne, len(w.miss_dates), [int((S == s).sum()) for s in (0, 1, 2)]))
    print("m = %.1f bp; p = %.5f; LCB(alpha) = %.1f bp; C2 %s" % (m, p, lcb, ok2))
    print("C3 Quantile97.5: zeitversetzt %.1f bp, same-symbol %.1f bp -> %s" % (q1, q2, ok3))
    print("C4 a/b/c/d: %s -> %s" % ({k: round(x, 1) for k, x in v.items()}, ok4))
    print("C5 %s; C6 %s" % (ok5, ok6))
    n = len(X); a = np.argsort(T)
    print("Haelften: %.1f / %.1f bp" % (X[a][: n // 2].mean(), X[a][n // 2:].mean()))
    print("je Zustand (n, Mittel bp): %s" % [(int((S == s).sum()), round(float(X[S == s].mean()), 1) if (S == s).any() else None) for s in (0, 1, 2)])
    allok = ok2 and ok3 and ok4 and ok5 and ok6
    if allok: cat = "BESTAETIGT"
    elif ok2: cat = "NICHT BESTAETIGT (C2 erfuellt, verfehlt: %s)" % ",".join(k for k, x in (("C3", ok3), ("C4", ok4), ("C5", ok5), ("C6", ok6)) if not x)
    elif m > 0: cat = "POSITIV-UNTERPOWERT (m > 0, C2 verfehlt; kein Nullbefund)"
    else: cat = "NICHT NACHWEISBAR (m <= 0; kein Nullbefund bei Kante < MDE)"
    print("KATEGORIE: %s" % cat)

if __name__ == "__main__":
    mode, csvp, folder = sys.argv[1], sys.argv[2], sys.argv[3]
    a = sys.argv[4:]
    def opt(k, d, f=float): return f(a[a.index(k) + 1]) if k in a else d
    hedge = opt("--hedge", "SPY", str)
    if mode == "count": counts(World(csvp, folder, hedge))
    elif mode == "hedgecmp": hedgecmp(csvp, folder, opt("--nnull", 80, int), opt("--seed", 20261025, int))
    elif mode == "calib":
        if "--sigma" not in a: sys.exit("calib braucht --sigma <gezaehlte Streuung der Netto-Excess-Rendite je Ereignis in bp> (Ausgabe von count)")
        calib(csvp, folder, hedge, opt("--nnull", 200, int), opt("--nplac", 2000, int), opt("--nsame", 500, int), opt("--boot", 10000, int), opt("--alpha", 0.0025), opt("--seed", 20261025, int), opt("--sigma", 0.0))
    elif mode == "final":
        h = opt("--spec-hash", "", str)
        if not re.fullmatch(r"[0-9a-f]{64}", h): sys.exit("final nur mit --spec-hash <sha256>")
        final(csvp, folder, hedge, h, opt("--boot", 10000, int), opt("--alpha", 0.0025), opt("--seed", 20261025, int), opt("--nplac", 2000, int), opt("--nsame", 500, int))
