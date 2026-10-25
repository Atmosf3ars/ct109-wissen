# k4_test_v1.py - Testmechanik C1-C7 der Runde-3-Spec (K4 AFTERSHOCK, K4P) + Nullwelt-Kalibrierung
# Aufruf (im Ordner tools):
#   python k4_test_v1.py calib <agg-Ordner> <Paar1,Paar2,...> --sigma <bp> [--nnull 200] [--nplac 2000] [--boot 10000] [--alpha 0.0025] [--seed 20261025]
#   python k4_test_v1.py final <agg-Ordner> <Paare> --spec-hash <64 hex>      (NUR nach Freeze; gibt Ergebnis des echten Tests aus)
# Paarangabe: XBT oder ETH (theta fest 3 %, Rundreise 16 bp) bzw. beliebige Alt-Namen (theta adaptiv, Rundreise 26 bp).
# calib gibt NUR Kennzahlen der Gesamtregel aus (Fehlpass-Raten, Operationscharakteristik, Streuung), keine Mittelwerte
# der Nullwelten und keine echte Kennzahl. Alle Kosten sind Annahmen [A] (Spec §4).
import sys, os, math, re, time
import numpy as np
from collections import deque
import count_events_v2 as v2
import count_events_v3 as v3

T0 = time.time()
def log(msg):
    print("[%5.0f s] %s" % (time.time() - T0, msg), flush=True)

START = v2.START
CUT = v2.CUT
WEEK = 7 * 86400
HOLD = 14400
STOP = 0.05

class Pair:
    def __init__(self, name, agg):
        self.name = name
        fixed = name in ("XBT", "ETH")
        self.adaptive = not fixed
        self.fee = 5.0
        self.slip = 3.0 if fixed else 8.0     # je Seite in bp; Rundreise 16 bzw. 26 bp
        d = v2.load(os.path.join(agg, name + "USD_1m.csv"))
        self.ts = np.array(d[0], dtype=np.int64); self.op = np.array(d[1]); self.hi = np.array(d[2])
        self.lo = np.array(d[3]); self.cl = np.array(d[4])
        self.sig = v3.sigma15_by_day(d[0], d[4]) if self.adaptive else None
        self._hi = d[2]; self._lo = d[3]; self._cl = d[4]; self._ts = d[0]
        self.trig = None
        self.rvdec = None

    def raw_triggers(self, st):
        """alle Minuten mit Schock-Bedingung (ohne Sperrzeiten), t >= START, Zustand vorhanden"""
        out = []
        dq = deque(); prev = None; WIN = 900
        ts, hi, lo, cl = self._ts, self._hi, self._lo, self._cl
        for i in range(len(ts)):
            t = ts[i]; h = hi[i]; l = lo[i]
            if l <= 0:
                continue
            while dq and dq[0][0] < t - WIN + 60: dq.popleft()
            while dq and dq[-1][1] <= h: dq.pop()
            dq.append((t, h))
            if t < START: continue
            day = t // 86400
            s = st.get(day)
            if s is None: continue
            if self.adaptive:
                s15 = self.sig.get(day)
                if s15 is None: continue
                theta = max(0.03, 6.0 * s15)
            else:
                theta = 0.03
            if l / dq[0][1] - 1.0 <= -theta:
                out.append((int(t), s))
        self.trig = out
        self._hi = self._lo = self._cl = self._ts = None
        return out

def cost_rt(p, state, mult=1.0, hslip=1.0):
    sl = p.slip * (hslip if state == 2 else 1.0)
    return 2.0 * (p.fee * mult + sl * mult)

def run_events(p, events, mult=1.0, delay=0, hslip=1.0):
    """events: sortierte (t, state). Liefert Liste (t, state, net_bp). Sperrzeiten wie Spec §7."""
    ts, op, lo = p.ts, p.op, p.lo
    n = len(ts); out = []; blocked = 0
    for t, s in events:
        if t < blocked: continue
        i = int(np.searchsorted(ts, t))
        if i >= n or ts[i] != t: continue
        low = lo[i]; lastnew = t; j = i + 1; done = False
        while j < n and ts[j] <= t + 7200:
            if lo[j] < low:
                low = lo[j]; lastnew = ts[j]
            if ts[j] >= t + 1200 and ts[j] - lastnew >= 600:
                tgt = ts[j] + 60 + 60 * delay
                k = int(np.searchsorted(ts, tgt))
                if k < n and ts[k] - tgt <= 600:
                    tg2 = ts[k] + HOLD
                    m = int(np.searchsorted(ts, tg2))
                    if m < n and ts[m] - tg2 <= 600 and op[k] > 0 and op[m] > 0 and ts[m] < CUT:
                        e = op[k]; lvl = e * (1 - STOP)
                        seg = lo[k:m]
                        hit = np.nonzero(seg <= lvl)[0]
                        if hit.size:
                            q = k + int(hit[0])
                            xp = min(lvl, op[q]) * (1 - 0.001)
                            texit = ts[q]
                        else:
                            xp = op[m]; texit = ts[m]
                        g = math.log(xp / e) * 1e4
                        out.append((t, s, g - cost_rt(p, s, mult, hslip)))
                        blocked = texit + 6 * 3600
                        done = True
                break
            j += 1
        if not done and blocked < t + 3600:
            blocked = t + 3600
    return out

def episodes_from(events_by_pair, gap=86400):
    """events_by_pair: {pair: [(t,s,net)]} -> Arrays (t, s, net) je Episode (Mittel je Paar, dann ueber Paare)"""
    allv = []
    for pn, ev in events_by_pair.items():
        for t, s, x in ev: allv.append((t, s, x, pn))
    allv.sort()
    eps = []; cur = []; last = None
    for e in allv:
        if last is not None and e[0] - last >= gap:
            eps.append(cur); cur = []
        cur.append(e); last = e[0]
    if cur: eps.append(cur)
    T = []; S = []; X = []
    for c in eps:
        by = {}
        for t, s, x, pn in c: by.setdefault(pn, []).append(x)
        X.append(sum(sum(v) / len(v) for v in by.values()) / len(by)); T.append(c[0][0]); S.append(c[0][1])
    return np.array(T, dtype=np.int64), np.array(S, dtype=np.int64), np.array(X)

class World:
    def __init__(self, agg, names):
        self.agg = agg
        self.pairs = [Pair(n, agg) for n in names]
        xbt = self.pairs[0] if self.pairs[0].name == "XBT" else Pair("XBT", agg)
        self.st = v2.state_table(v2.hourly(xbt._ts, xbt._cl))
        for p in self.pairs: p.raw_triggers(self.st)
        self.W = int((CUT - START) // WEEK) + 1

    def real_events(self, **kw):
        return {p.name: run_events(p, p.trig, **kw) for p in self.pairs}

    def shifted_events(self, dw, **kw):
        out = {}
        for p in self.pairs:
            ev = sorted((t + dw * WEEK, s) for t, s in p.trig if START <= t + dw * WEEK < CUT)
            out[p.name] = run_events(p, ev, **kw)
        return out

    def rv_deciles(self, p):
        if p.rvdec is not None: return p.rvdec
        h = p.ts // 3600
        h0 = int(h[0]); H = int(h[-1]) - h0 + 1
        c = np.full(H, np.nan)
        c[h - h0] = p.cl                       # letzter Schluss je Stunde (spaetere ueberschreiben frueher)
        s = None
        for i in range(H):
            if np.isnan(c[i]): c[i] = c[i - 1] if i > 0 else np.nan
        r = np.diff(np.log(c), prepend=np.nan)
        r2 = np.nan_to_num(r) ** 2; cs = np.cumsum(r2)
        rv = np.full(H, np.nan)
        rv[24:] = np.sqrt((cs[24:] - cs[:-24]) / 24.0)
        valid = np.nonzero(~np.isnan(rv) & ((h0 + np.arange(H)) * 3600 >= START))[0]
        edges = np.quantile(rv[valid], np.linspace(0.1, 0.9, 9))
        p.rvdec = (h0, rv, edges)
        return p.rvdec

    def vol_matched_events(self, rng, **kw):
        out = {}
        for p in self.pairs:
            h0, rv, edges = self.rv_deciles(p)
            real = np.array(sorted(t for t, _ in p.trig), dtype=np.int64)
            ev = []
            for t, s in p.trig:
                if not hasattr(p, "_cand"): p._cand = {}
                cand = p._cand.get(t)
                if cand is None:
                    d0 = START // 86400; d1 = CUT // 86400
                    c = (np.arange(d0, d1) * 86400 + (t % 86400)).astype(np.int64)
                    i = c // 3600 - 1 - h0
                    ok = (i >= 0) & (i < len(rv))
                    c = c[ok]; i = i[ok]
                    rr = rv[i]; ok = ~np.isnan(rr); c = c[ok]; rr = rr[ok]
                    d_t = int(np.searchsorted(edges, rv[min(max(t // 3600 - 1 - h0, 0), len(rv) - 1)]))
                    dec = np.searchsorted(edges, rr)
                    k = np.searchsorted(real, c)
                    near = np.zeros(len(c), dtype=bool)
                    for sh in (-1, 0):
                        kk = np.clip(k + sh, 0, len(real) - 1)
                        near |= np.abs(real[kk] - c) < 2 * 86400
                    cand = c[(dec == d_t) & ~near]
                    p._cand[t] = cand
                if cand.size == 0: continue
                tc = int(cand[rng.integers(cand.size)])
                sc = self.st.get(tc // 86400)
                if sc is None: continue
                ev.append((tc, sc))
            ev.sort()
            out[p.name] = run_events(p, ev, **kw)
        return out

def week_arrays(T, X, W):
    wk = ((T - START) // WEEK).astype(np.int64)
    wk = np.clip(wk, 0, W - 1)
    S = np.bincount(wk, weights=X, minlength=W); N = np.bincount(wk, minlength=W).astype(float)
    return S, N

def boot_means(T, X, W, B, rng, block=4):
    S, N = week_arrays(T, X, W)
    nb = int(math.ceil(W / block))
    starts = rng.integers(0, W - block + 1, size=(B, nb))
    idx = starts[:, :, None] + np.arange(block)[None, None, :]
    sm = S[idx].sum(axis=(1, 2)); nm = N[idx].sum(axis=(1, 2))
    return sm / np.maximum(nm, 1.0)

def c2(T, X, W, B, rng, alpha):
    if len(X) < 5: return False, 1.0, float("nan")
    bm = boot_means(T, X, W, B, rng)
    p = float(np.mean(bm <= 0))
    lcb = float(np.quantile(bm, alpha))
    return (p <= alpha and lcb > 0), p, lcb

def c5(T, X):
    if len(X) == 0 or X.mean() <= 0: return False
    pos = np.sort(X[X > 0])[::-1]
    gp = pos.sum()
    if gp <= 0 or pos[:3].sum() > 0.40 * gp: return False
    yrs = ((T // 86400 + 719468) // 365.2425).astype(int)    # grobe Jahreszuordnung genuegt fuer Konzentrationstest
    tot = X.sum()
    for y in np.unique(yrs):
        if X[yrs == y].sum() > 0.5 * tot: return False
    return True

def c6(T, S, X):
    n = len(X)
    if n < 10: return False
    a = np.argsort(T); X2 = X[a]; S2 = S[a]
    if not (X2[: n // 2].mean() > 0 and X2[n // 2:].mean() > 0): return False
    good = 0
    for s in (0, 1, 2):
        m = S2 == s
        if m.sum() >= 20 and X2[m].mean() > 0: good += 1
    return good >= 2

def mean_or_nan(X): return float(X.mean()) if len(X) else float("nan")

def make_shifts(rng, k):
    out = []
    for _ in range(k):
        dw = int(rng.integers(4, 53)) * (1 if rng.random() < 0.5 else -1)
        out.append(dw)
    return out

def placebo_means(world, shifts):
    ms = []
    for dw in shifts:
        T, S, X = episodes_from(world.shifted_events(dw))
        if len(X) >= 5: ms.append(X.mean())
    return np.array(ms)

def variants(world, shift=None):
    """C4-Stressvarianten: (a) Kosten x1,5, (b) 1 Minute Verzoegerung, (c) Slippage x2 im Zustand HOCH"""
    res = {}
    for key, kw in (("a", dict(mult=1.5)), ("b", dict(delay=1)), ("c", dict(hslip=2.0))):
        ev = world.real_events(**kw) if shift is None else world.shifted_events(shift, **kw)
        T, S, X = episodes_from(ev)
        res[key] = mean_or_nan(X)
    return res

def calib(agg, names, nnull, nplac, B, alpha, seed, sigma):
    rng = np.random.default_rng(seed)
    world = World(agg, names)
    log("Welt geladen")
    print("Welt: Paare %s; Ausloeser je Paar %s" % (",".join(names), [len(p.trig) for p in world.pairs]))
    Tr, Sr, Xr = episodes_from(world.real_events())
    print("echte Episoden (nur Anzahl): %d; Zustaende %s" % (len(Xr), [int((Sr == s).sum()) for s in (0, 1, 2)]))
    # Placebo-Verteilung (zeitversetzt) und vol-gematchte Verteilung
    plac = placebo_means(world, make_shifts(rng, nplac))
    log("Zeitversatz-Placebos fertig")
    vm = []
    for _ in range(min(500, nplac)):
        T, S, X = episodes_from(world.vol_matched_events(rng))
        if len(X) >= 5: vm.append(X.mean())
    vm = np.array(vm)
    log("vol-gematchte Placebos fertig")
    # Nullwelten (andere Verschiebungen als die Placebo-Menge)
    shifts = make_shifts(rng, nnull * 2)
    nulls = []
    sd_entry = []
    for dw in shifts:
        ev = world.shifted_events(dw)
        T, S, X = episodes_from(ev)
        if len(X) < 20: continue
        allx = [x for lst in ev.values() for (_, _, x) in lst]
        sd_entry.append(float(np.std(allx, ddof=1)))
        v = variants(world, dw)
        nulls.append((T, S, X, v))
        if len(nulls) >= nnull: break
    k = len(nulls)
    log("Nullwelten fertig")
    M = float(np.mean([x[2].mean() for x in nulls]))
    Mk = {key: float(np.mean([x[3][key] for x in nulls])) for key in "abc"}
    sd_ep_null = float(np.mean([x[2].std(ddof=1) for x in nulls]))
    sd_ent_null = float(np.mean(sd_entry))
    f = sigma / sd_ent_null          # Skalierung: Nullwelt-Streuung auf die gezaehlte Streuung der Nachereignis-Renditen (nur Betragsgroesse)
    sd_ep = f * sd_ep_null
    n_ep = float(len(Tr))            # echte Episodenzahl (Zaehlung)
    mde = (2.807 + 0.842) * sd_ep / math.sqrt(n_ep)
    print("Nullwelten %d (von %d versucht); Streuung je Einstieg in Nullwelt %.0f bp -> Skalierung auf %.0f bp (Faktor %.2f, Annahme [A]); Episoden-Streuung skaliert %.0f bp; echte Episoden %d; MDE(80 %%) %.0f bp (analytisch)" % (
        k, len(shifts), sd_ent_null, sigma, f, sd_ep, int(n_ep), mde), flush=True)
    q_plac = f * np.quantile(plac - plac.mean(), 0.975); q_vm = f * np.quantile(vm - vm.mean(), 0.975)
    print("Placebo-Mengen: zeitversetzt %d, vol-gematcht %d" % (len(plac), len(vm)))
    print("Operationscharakteristik der Gesamtregel (alle C2..C6; wahre Netto-Kante delta, Nullwelten rezentriert und auf die gezaehlte Streuung skaliert):")
    for lab, d in (("0", 0.0), ("0.5*MDE", 0.5 * mde), ("MDE", mde), ("2*MDE", 2 * mde)):
        cnt = dict(c2=0, c3=0, c4=0, c5=0, c6=0, all=0)
        for T, S, X, v in nulls:
            Xa = f * (X - M) + d
            ok2, p, lcb = c2(T, Xa, world.W, B, rng, alpha)
            m = Xa.mean()
            ok3 = (m > q_plac) and (m > q_vm)
            ok4 = all((f * (v[key] - Mk[key]) + d + (Mk[key] - M)) > 0 for key in "abc")
            ok5 = c5(T, Xa); ok6 = c6(T, S, Xa)
            for key, val in (("c2", ok2), ("c3", ok3), ("c4", ok4), ("c5", ok5), ("c6", ok6)):
                cnt[key] += int(val)
            cnt["all"] += int(ok2 and ok3 and ok4 and ok5 and ok6)
        print("  delta=%-8s (%.0f bp): bestanden gesamt %d/%d = %.1f %%; einzeln C2 %d, C3 %d, C4 %d, C5 %d, C6 %d" % (
            lab, d, cnt["all"], k, 100.0 * cnt["all"] / k, cnt["c2"], cnt["c3"], cnt["c4"], cnt["c5"], cnt["c6"]), flush=True)
    print("Hinweis: bei delta=0 ist die erwartete Fehlpass-Rate durch C2 (alpha_i) und C3 begrenzt; Soll <= 5 %.")

def final(agg, names, spec_hash, B, alpha, seed, nplac):
    rng = np.random.default_rng(seed)
    world = World(agg, names)
    T, S, X = episodes_from(world.real_events())
    ok2, p, lcb = c2(T, X, world.W, B, rng, alpha)
    plac = placebo_means(world, make_shifts(rng, nplac))
    vm = np.array([episodes_from(world.vol_matched_events(rng))[2].mean() for _ in range(500)])
    v = variants(world)
    print("SPEC-HASH %s" % spec_hash)
    print("Episoden %d; m = %.1f bp; p = %.5f; LCB = %.1f bp; C2 %s" % (len(X), X.mean(), p, lcb, ok2))
    print("C3a Quantil97.5 %.1f, C3b %.1f -> %s" % (np.quantile(plac, 0.975), np.quantile(vm, 0.975), (X.mean() > np.quantile(plac, 0.975)) and (X.mean() > np.quantile(vm, 0.975))))
    print("C4 a/b/c: %s -> %s" % (v, all(x > 0 for x in v.values())))
    print("C5 %s; C6 %s" % (c5(T, X), c6(T, S, X)))

if __name__ == "__main__":
    mode, agg, names = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
    a = sys.argv[4:]
    def opt(k, d, f=float):
        return f(a[a.index(k) + 1]) if k in a else d
    if mode == "calib":
        if "--sigma" not in a: sys.exit("calib braucht --sigma <gezaehlte Streuung der 4-h-Rendite je Einstieg in bp> (K4: 310, K4P: 411)")
        calib(agg, names, opt("--nnull", 200, int), opt("--nplac", 2000, int), opt("--boot", 10000, int), opt("--alpha", 0.0025), opt("--seed", 20261025, int), opt("--sigma", 0.0))
    elif mode == "final":
        h = opt("--spec-hash", "", str)
        if not re.fullmatch(r"[0-9a-f]{64}", h):
            sys.exit("final nur mit --spec-hash <sha256 der eingefrorenen Spec>")
        final(agg, names, h, opt("--boot", 10000, int), opt("--alpha", 0.0025), opt("--seed", 20261025, int), opt("--nplac", 2000, int))
