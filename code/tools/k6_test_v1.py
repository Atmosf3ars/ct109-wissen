# k6_test_v1.py - Testmechanik K6 FLOW (Order-Flow: Volumenschock + Aggressor-Ungleichgewicht), beide Richtungen
# Aufruf (im Ordner tools):
#   python -u k6_test_v1.py calib <agg-Ordner> <Paare|ALL> --sigma <bp je Ereignis> [--nnull 200] [--nplac 2000] [--boot 10000] [--alpha 0.00125] [--seed 20261025]
#   python -u k6_test_v1.py final <agg-Ordner> <Paare|ALL> --spec-hash <64 hex>      (NUR nach Freeze)
# K6-C: Position in Richtung der Imbalance (Fortsetzung); K6-R: entgegen (Umkehr). Je Seite einseitiger Test mit alpha = 0,00125 (D43).
# calib gibt NUR Raten/Streuung der Nullwelten aus, keine echten Kennzahlen.
import sys, os, math, re, time, hashlib
from array import array
import numpy as np
import count_events_v2 as v2
import count_cs_v1 as cs
import k4_test_v1 as k4

START, CUT, WEEK = v2.START, v2.CUT, k4.WEEK
M_RATIO, I_MIN, HOURS_BACK = 20.0, 0.7, 720
HOLD, STOP, GAP = 14400, 0.05, 4 * 3600
log = k4.log

class P6:
    def __init__(self, name, agg, st):
        self.name = name
        self.fee = 5.0
        self.slip = 3.0 if name in ("XBT", "ETH") else 8.0
        self._load(os.path.join(agg, name + "USD_1m.csv"), st)

    def _load(self, path, st):
        ts = array("q"); op = array("d"); hi = array("d"); lo = array("d"); cl = array("d")
        no = array("d"); vb = array("d"); vs = array("d")
        with open(path) as f:
            f.readline()
            for line in f:
                a = line.split(",")
                t = int(a[0])
                if t >= CUT: break
                ts.append(t); op.append(float(a[1])); hi.append(float(a[2])); lo.append(float(a[3])); cl.append(float(a[4]))
                vb.append(float(a[6])); vs.append(float(a[7])); no.append(float(a[10]))
        T = np.frombuffer(ts, dtype=np.int64); O = np.frombuffer(op); H = np.frombuffer(hi); L = np.frombuffer(lo); C = np.frombuffer(cl)
        prev = np.concatenate(([np.nan], C[:-1]))
        with np.errstate(invalid="ignore"):
            bad = (L <= 0) | (L < 0.7 * H) | (L < 0.7 * prev) | (H > 1.4 * prev)
        keep = ~bad
        self.nbad = int(bad.sum())
        self.ts = T[keep]; self.op = O[keep]; self.hi = H[keep]; self.lo = L[keep]; self.cl = C[keep]
        N = np.frombuffer(no)[keep]; B = np.frombuffer(vb)[keep]; S = np.frombuffer(vs)[keep]
        hk = self.ts // 3600
        h0 = int(hk[0]); n = int(hk[-1]) - h0 + 1
        idx = (hk - h0)
        notional = np.bincount(idx, weights=N, minlength=n); sb = np.bincount(idx, weights=B, minlength=n); ss = np.bincount(idx, weights=S, minlength=n)
        self.h0 = h0
        med = np.full(n, np.nan)
        for s in range(HOURS_BACK, n, 4000):
            e = min(n, s + 4000)
            ii = np.arange(s, e)[:, None] - np.arange(1, HOURS_BACK + 1)[None, :]
            med[s:e] = np.median(notional[ii], axis=1)
        tot = sb + ss
        imb = np.divide(sb - ss, tot, out=np.zeros(n), where=tot > 0)
        ev = []
        for i in np.nonzero((med > 0) & (tot > 0) & (notional >= M_RATIO * np.where(med > 0, med, np.inf)) & (np.abs(imb) >= I_MIN))[0]:
            t = (h0 + int(i)) * 3600
            if t < START: continue
            s_ = st.get(t // 86400)
            if s_ is None: continue
            ev.append((t, 1 if imb[i] > 0 else -1, s_))
        self.ev = ev
        self.rvdec = None
        self.cand = {}
        # Tageshuelle Sperre fuer vol-gematchte Pseudo-Ereignisse
        self.ev_days = np.array(sorted({t // 86400 for t, _, _ in ev}), dtype=np.int64)

def cost_rt(p, state, mult=1.0, hslip=1.0):
    sl = p.slip * (hslip if state == 2 else 1.0)
    return 2.0 * (p.fee * mult + sl * mult)

def run(p, events, flip=False, mult=1.0, delay=0, hslip=1.0):
    """events: sortierte (t_stunde, dir, state). Einstieg Open der Folgestunde (+ delay Minuten), Halten 4 h, Stop 5 %."""
    ts, op, hi, lo = p.ts, p.op, p.hi, p.lo
    n = len(ts); out = []; blocked = 0
    for t, d, s in events:
        te = t + 3600 + 60 * delay
        if te < blocked: continue
        k = int(np.searchsorted(ts, te))
        if k >= n or ts[k] - te > 600: continue
        tg = ts[k] + HOLD
        m = int(np.searchsorted(ts, tg))
        if m >= n or ts[m] - tg > 600 or ts[m] >= CUT or op[k] <= 0 or op[m] <= 0: continue
        dd = -d if flip else d
        e = op[k]
        if dd > 0:
            lvl = e * (1 - STOP); hit = np.nonzero(lo[k:m] <= lvl)[0]
        else:
            lvl = e * (1 + STOP); hit = np.nonzero(hi[k:m] >= lvl)[0]
        if hit.size:
            q = k + int(hit[0])
            xp = (min(lvl, op[q]) * (1 - 0.001)) if dd > 0 else (max(lvl, op[q]) * (1 + 0.001))
            texit = ts[q]
        else:
            xp = op[m]; texit = ts[m]
        g = dd * math.log(xp / e) * 1e4
        out.append((te, s, g - cost_rt(p, s, mult, hslip)))
        blocked = texit
    return out

class World6:
    def __init__(self, agg, names):
        xbt = v2.load(os.path.join(agg, "XBTUSD_1m.csv"))
        self.st = v2.state_table(v2.hourly(xbt[0], xbt[4]))
        del xbt
        if names == ["ALL"]: names = cs.POOL
        self.pairs = []
        for nm in names:
            p = P6(nm, agg, self.st); self.pairs.append(p)
        self.W = int((CUT - START) // WEEK) + 1
        log("Welt geladen: " + ", ".join("%s %d" % (p.name, len(p.ev)) for p in self.pairs))

    def real(self, flip, **kw):
        return {p.name: run(p, p.ev, flip, **kw) for p in self.pairs}

    def shifted(self, dw, flip, **kw):
        out = {}
        for p in self.pairs:
            ev = sorted((t + dw * WEEK, d, s) for t, d, s in p.ev if START <= t + dw * WEEK < CUT)
            out[p.name] = run(p, ev, flip, **kw)
        return out

    def _rv(self, p):
        if p.rvdec is not None: return p.rvdec
        h0 = p.h0; hh = p.ts // 3600; n = int(hh[-1]) - h0 + 1
        c = np.full(n, np.nan); c[hh - h0] = p.cl
        for i in range(1, n):
            if np.isnan(c[i]): c[i] = c[i - 1]
        r = np.diff(np.log(c), prepend=np.nan)
        cs2 = np.cumsum(np.nan_to_num(r) ** 2)
        rv = np.full(n, np.nan); rv[24:] = np.sqrt((cs2[24:] - cs2[:-24]) / 24.0)
        ok = np.nonzero(~np.isnan(rv) & ((h0 + np.arange(n)) * 3600 >= START))[0]
        edges = np.quantile(rv[ok], np.linspace(0.1, 0.9, 9))
        dec = np.full(n, -1); good = ~np.isnan(rv); dec[good] = np.searchsorted(edges, rv[good])
        p.rvdec = (dec,)
        return p.rvdec

    def volmatched(self, rng, flip, **kw):
        out = {}
        for p in self.pairs:
            (dec,) = self._rv(p)
            h0 = p.h0
            ev = []
            for t, d, s in p.ev:
                hod = (t // 3600) % 24
                i_t = t // 3600 - 1 - h0
                if i_t < 0 or i_t >= len(dec) or dec[i_t] < 0: continue
                key = (hod, int(dec[i_t]))
                cand = p.cand.get(key)
                if cand is None:
                    hours = np.arange(int(START // 3600), int(CUT // 3600) - 6)
                    hours = hours[(hours % 24) == hod]
                    ii = hours - 1 - h0
                    ok = (ii >= 0) & (ii < len(dec))
                    hours = hours[ok]; ii = ii[ok]
                    hours = hours[dec[ii] == key[1]]
                    dd = hours // 24
                    k = np.searchsorted(p.ev_days, dd)
                    near = np.zeros(len(hours), dtype=bool)
                    for sh in (-1, 0):
                        kk = np.clip(k + sh, 0, max(len(p.ev_days) - 1, 0))
                        if len(p.ev_days): near |= np.abs(p.ev_days[kk] - dd) <= 2
                    cand = hours[~near]
                    p.cand[key] = cand
                if cand.size == 0: continue
                tc = int(cand[rng.integers(cand.size)]) * 3600
                sc = self.st.get(tc // 86400)
                if sc is None: continue
                ev.append((tc, d, sc))
            ev.sort()
            out[p.name] = run(p, ev, flip, **kw)
        return out

def eps(ev): return k4.episodes_from(ev, gap=GAP)

def placebo_means(w, shifts, flip):
    ms = []
    for dw in shifts:
        T, S, X = eps(w.shifted(dw, flip))
        if len(X) >= 20: ms.append(X.mean())
    return np.array(ms)

def variants(w, flip, shift=None):
    res = {}
    for key, kw in (("a", dict(mult=1.5)), ("b", dict(delay=1)), ("c", dict(hslip=2.0))):
        ev = w.real(flip, **kw) if shift is None else w.shifted(shift, flip, **kw)
        res[key] = k4.mean_or_nan(eps(ev)[2])
    return res

def calib(agg, names, nnull, nplac, B, alpha, seed, sigma):
    print("Skript-SHA256 %s (K6)" % hashlib.sha256(open(__file__, "rb").read()).hexdigest()[:16], flush=True)
    rng = np.random.default_rng(seed)
    w = World6(agg, names)
    n_real = {}
    for side, flip in (("C", False), ("R", True)):
        n_real[side] = len(eps(w.real(flip))[2])
    print("echte Episoden (nur Anzahl): C %d, R %d" % (n_real["C"], n_real["R"]), flush=True)
    shifts_p = k4.make_shifts(rng, nplac)
    plac = {s: placebo_means(w, shifts_p, f) for s, f in (("C", False), ("R", True))}
    log("Zeitversatz-Placebos fertig")
    vm = {"C": [], "R": []}
    for _ in range(min(500, nplac)):
        for s, f in (("C", False), ("R", True)):
            T, S, X = eps(w.volmatched(rng, f))
            if len(X) >= 20: vm[s].append(X.mean())
    vm = {s: np.array(v) for s, v in vm.items()}
    log("vol-gematchte Placebos fertig")
    shifts = k4.make_shifts(rng, nnull * 2)
    nulls = {"C": [], "R": []}; sd_entry = []
    for dw in shifts:
        okw = True; tmp = {}
        for s, f in (("C", False), ("R", True)):
            ev = w.shifted(dw, f)
            T, S, X = eps(ev)
            if len(X) < 50: okw = False; break
            tmp[s] = (T, S, X, variants(w, f, dw), [x for lst in ev.values() for (_, _, x) in lst])
        if not okw: continue
        for s in ("C", "R"): nulls[s].append(tmp[s][:4])
        sd_entry.append(float(np.std(tmp["C"][4], ddof=1)))
        if len(nulls["C"]) >= nnull: break
    log("Nullwelten fertig")
    k = len(nulls["C"])
    fs = sigma / float(np.mean(sd_entry))
    print("Nullwelten %d; Streuung je Einstieg roh %.0f bp -> Skalierung auf %.0f bp (Faktor %.2f, Annahme [A])" % (k, np.mean(sd_entry), sigma, fs), flush=True)
    res = {}
    for side in ("C", "R"):
        M = float(np.mean([x[2].mean() for x in nulls[side]]))
        Mk = {key: float(np.mean([x[3][key] for x in nulls[side]])) for key in "abc"}
        sd_ep = fs * float(np.mean([x[2].std(ddof=1) for x in nulls[side]]))
        mde = (3.023 + 0.842) * sd_ep / math.sqrt(n_real[side])
        q_plac = fs * np.quantile(plac[side] - plac[side].mean(), 0.975)
        q_vm = fs * np.quantile(vm[side] - vm[side].mean(), 0.975)
        print("Seite K6-%s: Episoden %d, Episoden-Streuung skaliert %.0f bp, MDE80 (alpha %.5f) %.1f bp" % (side, n_real[side], sd_ep, alpha, mde), flush=True)
        passes = {}
        for lab, d in (("0", 0.0), ("0.5*MDE", 0.5 * mde), ("MDE", mde), ("2*MDE", 2 * mde)):
            flags = []
            for T, S, X, v in nulls[side]:
                Xa = fs * (X - M) + d
                ok2, p, lcb = k4.c2(T, Xa, w.W, B, rng, alpha)
                m = Xa.mean()
                ok3 = (m > q_plac) and (m > q_vm)
                ok4 = all((fs * (v[key] - Mk[key]) + d + (Mk[key] - M)) > 0 for key in "abc")
                flags.append((ok2, ok3, ok4, k4.c5(T, Xa), k4.c6(T, S, Xa)))
            passes[lab] = flags
            cnt = [sum(f[i] for f in flags) for i in range(5)]
            allp = sum(all(f) for f in flags)
            print("  delta=%-8s (%.1f bp): bestanden gesamt %d/%d = %.1f %%; einzeln C2 %d, C3 %d, C4 %d, C5 %d, C6 %d" % (lab, d, allp, k, 100.0 * allp / k, *cnt), flush=True)
        res[side] = passes
    both = sum(1 for i in range(k) if all(res["C"]["0"][i]) or all(res["R"]["0"][i]))
    print("Fehlpass beider Seiten zusammen (delta=0): %d/%d = %.1f %%. Soll <= 5 %%." % (both, k, 100.0 * both / k))

def final(agg, names, spec_hash, B, alpha, seed, nplac):
    print("Skript-SHA256 %s" % hashlib.sha256(open(__file__, "rb").read()).hexdigest()[:16])
    print("SPEC-HASH %s" % spec_hash)
    rng = np.random.default_rng(seed)
    w = World6(agg, names)
    shifts_p = k4.make_shifts(rng, nplac)
    for side, flip in (("C", False), ("R", True)):
        T, S, X = eps(w.real(flip))
        ok2, p, lcb = k4.c2(T, X, w.W, B, rng, alpha)
        plac = placebo_means(w, shifts_p, flip)
        vm = np.array([eps(w.volmatched(rng, flip))[2].mean() for _ in range(500)])
        v = variants(w, flip)
        m = float(X.mean()); q1 = float(np.quantile(plac, 0.975)); q2 = float(np.quantile(vm, 0.975))
        ok3 = (m > q1) and (m > q2); ok4 = all(x > 0 for x in v.values()); ok5 = k4.c5(T, X); ok6 = k4.c6(T, S, X)
        n = len(X); a_ = np.argsort(T)
        print("== K6-%s: Episoden %d; Zustaende %s" % (side, n, [int((S == s).sum()) for s in (0, 1, 2)]))
        print("   m = %.1f bp; p = %.5f; LCB = %.1f bp; C2 %s" % (m, p, lcb, ok2))
        print("   C3 Quantile %.1f / %.1f -> %s; C4 %s -> %s; C5 %s; C6 %s" % (q1, q2, ok3, {k: round(x, 1) for k, x in v.items()}, ok4, ok5, ok6))
        print("   Haelften %.1f / %.1f; je Zustand %s" % (X[a_][: n // 2].mean(), X[a_][n // 2:].mean(), [(int((S == s).sum()), round(float(X[S == s].mean()), 1) if (S == s).any() else None) for s in (0, 1, 2)]))
        allok = ok2 and ok3 and ok4 and ok5 and ok6
        if allok: cat = "BESTAETIGT"
        elif ok2: cat = "NICHT BESTAETIGT (C2 erfuellt, verfehlt: %s)" % ",".join(k for k, x in (("C3", ok3), ("C4", ok4), ("C5", ok5), ("C6", ok6)) if not x)
        elif m > 0: cat = "POSITIV-UNTERPOWERT (m > 0, C2 verfehlt)"
        else: cat = "NICHT NACHWEISBAR (m <= 0; kein Nullbefund bei Kante < MDE)"
        print("   KATEGORIE K6-%s: %s" % (side, cat), flush=True)

if __name__ == "__main__":
    mode, agg, names = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
    a = sys.argv[4:]
    def opt(k, d, f=float): return f(a[a.index(k) + 1]) if k in a else d
    if mode == "calib":
        if "--sigma" not in a: sys.exit("calib braucht --sigma")
        calib(agg, names, opt("--nnull", 200, int), opt("--nplac", 2000, int), opt("--boot", 10000, int), opt("--alpha", 0.00125), opt("--seed", 20261025, int), opt("--sigma", 0.0))
    elif mode == "final":
        h = opt("--spec-hash", "", str)
        if not re.fullmatch(r"[0-9a-f]{64}", h): sys.exit("final nur mit --spec-hash <sha256>")
        final(agg, names, h, opt("--boot", 10000, int), opt("--alpha", 0.00125), opt("--seed", 20261025, int), opt("--nplac", 2000, int))
