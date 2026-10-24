import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from lf2 import core, stats, protocol as P  # noqa: E402


def synth(T=420, N=130, seed=1, gaps=True):
    """Zufallspanel mit Luecken, Teilhistorien und Ausreissern."""
    rng = np.random.default_rng(seed)
    r = rng.normal(0, 0.02, (T, N))
    adj = 50.0 * np.exp(np.cumsum(r, axis=0))
    opn = adj * np.exp(rng.normal(0, 0.003, (T, N)))
    raw = adj * 1.3
    vol = rng.uniform(2e5, 4e6, (T, N))
    if gaps:
        for _ in range(60):
            t, j = rng.integers(0, T), rng.integers(0, N)
            adj[t, j] = opn[t, j] = raw[t, j] = vol[t, j] = np.nan
        for _ in range(8):
            j = rng.integers(0, N)
            s = rng.integers(10, 150)
            adj[:s, j] = opn[:s, j] = raw[:s, j] = vol[:s, j] = np.nan
        for _ in range(5):
            j = rng.integers(0, N)
            s = rng.integers(250, T)
            adj[s:, j] = opn[s:, j] = raw[s:, j] = vol[s:, j] = np.nan
        for _ in range(12):
            j = rng.integers(0, N)
            opn[rng.integers(0, T), j] = np.nan
    return {"O": opn, "C": adj, "CL": raw, "V": vol}


# ---------- langsame Referenz (Schleifen) ----------

def ref_tradable(CL, V):
    T, N = CL.shape
    ok = np.zeros((T, N), bool)
    med = np.full((T, N), np.nan)
    for j in range(N):
        hist = 0
        for t in range(T):
            if np.isfinite(CL[t, j]):
                hist += 1
            if t >= core.DV_WIN - 1:
                w = [CL[s, j] * V[s, j] for s in range(t - core.DV_WIN + 1, t + 1)]
                w = [x for x in w if np.isfinite(x)]
                if len(w) >= core.DV_MIN_VALID:
                    med[t, j] = float(np.median(w))
            ok[t, j] = bool(np.isfinite(med[t, j]) and med[t, j] >= core.MIN_DV and np.isfinite(CL[t, j]) and CL[t, j] >= core.MIN_PX and hist >= core.MIN_HIST)
    return ok, med


def ref_cost(trad, med):
    T, N = trad.shape
    c = np.full((T, N), np.nan)
    for t in range(T):
        idx = [j for j in range(N) if trad[t, j]]
        idx.sort(key=lambda j: (-med[t, j], j))
        for rk, j in enumerate(idx):
            bp = 4.0 if rk < 100 else (7.0 if rk < 300 else 12.0)
            c[t, j] = bp * core.COST_PAD
    return c


def ref_ret(O, H, delay):
    T, N = O.shape
    r = np.full((T, N), np.nan)
    for t in range(T):
        e, x = t + 1 + delay, t + 1 + delay + H
        if x < T:
            for j in range(N):
                a, b = O[e, j], O[x, j]
                if np.isfinite(a) and np.isfinite(b):
                    r[t, j] = b / a - 1.0
    return r


def ref_cohort(score, elig, ret, cost, H):
    T, N = score.shape
    g = np.full(T, np.nan); c = np.full(T, np.nan); n_el = np.zeros(T, int)
    for t in range(T):
        idx = [j for j in range(N) if elig[t, j] and np.isfinite(score[t, j])]
        n = len(idx)
        n_el[t] = n
        k = n // 5
        if n < core.MIN_ELIG or k == 0:
            continue
        idx.sort(key=lambda j: (score[t, j], j))
        S = [j for j in idx[:k] if np.isfinite(ret[t, j])]
        L = [j for j in idx[n - k:] if np.isfinite(ret[t, j])]
        if not S or not L:
            continue
        g[t] = 0.5 * (np.mean([ret[t, j] for j in L]) - np.mean([ret[t, j] for j in S])) * 1e4
        c[t] = 0.5 * (np.mean([cost[t, j] for j in L]) + np.mean([cost[t, j] for j in S]))
    return g, c, n_el


class CoreVsReference(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = synth(T=420, N=130, seed=3)
        core.MIN_HIST_BAK = core.MIN_HIST
        cls.trad, cls.med = core.tradable(cls.p["CL"], cls.p["V"])

    def test_tradable_equals_reference(self):
        rt, rm = ref_tradable(self.p["CL"], self.p["V"])
        np.testing.assert_array_equal(self.trad, rt)
        both = np.isfinite(rm) | np.isfinite(self.med)
        np.testing.assert_allclose(self.med[both], rm[both], rtol=1e-12)
        self.assertGreater(self.trad.sum(), 1000)           # Test ist nicht leer

    def test_tradable_no_lookahead(self):
        """Aenderung der Zukunft (ab t0+1) darf die Handelbarkeit bis t0 nicht aendern."""
        t0 = 300
        CL2, V2 = self.p["CL"].copy(), self.p["V"].copy()
        CL2[t0 + 1:] *= 0.01; V2[t0 + 1:] *= 0.01
        tr2, _ = core.tradable(CL2, V2)
        np.testing.assert_array_equal(self.trad[:t0 + 1], tr2[:t0 + 1])

    def test_cost_equals_reference(self):
        np.testing.assert_allclose(np.nan_to_num(core.cost_matrix(self.trad, self.med), nan=-1), np.nan_to_num(ref_cost(self.trad, self.med), nan=-1))

    def test_cost_classes_with_many_names(self):
        T, N = 3, 450
        rng = np.random.default_rng(0)
        med = rng.uniform(3e7, 9e8, (T, N))
        tr = np.ones((T, N), bool)
        c = core.cost_matrix(tr, med)
        for t in range(T):
            order = np.argsort(-med[t])
            self.assertTrue(np.all(c[t, order[:100]] == 4.0 * 1.25))
            self.assertTrue(np.all(c[t, order[100:300]] == 7.0 * 1.25))
            self.assertTrue(np.all(c[t, order[300:]] == 12.0 * 1.25))

    def test_forward_returns_equals_reference(self):
        for H, d in ((5, 0), (21, 0), (5, 1)):
            np.testing.assert_allclose(np.nan_to_num(core.forward_returns(self.p["O"], H, d), nan=-9), np.nan_to_num(ref_ret(self.p["O"], H, d), nan=-9), rtol=1e-12)

    def test_scores_formula_and_no_lookahead(self):
        C = self.p["C"]
        s = core.score_str(C, 5)
        t, j = 200, 7
        self.assertAlmostEqual(s[t, j], -np.log(C[t, j] / C[t - 5, j]))
        m = core.score_mom(C, 252, 21)
        t = 330
        self.assertAlmostEqual(m[t, j], np.log(C[t - 21, j] / C[t - 252, j]))
        self.assertTrue(np.all(np.isnan(m[:252])))
        C2 = C.copy(); C2[301:] *= 3.0
        np.testing.assert_array_equal(np.nan_to_num(core.score_str(C2, 5)[:301], nan=-1), np.nan_to_num(s[:301], nan=-1))
        np.testing.assert_array_equal(np.nan_to_num(core.score_mom(C2)[:301], nan=-1), np.nan_to_num(m[:301], nan=-1))

    def test_cohorts_equal_reference(self):
        cost = core.cost_matrix(self.trad, self.med)
        for hyp in P.HYPOTHESES:
            H = hyp["H"]
            sc = P.hyp_score(hyp, self.p["C"])
            ret = core.forward_returns(self.p["O"], H, 0)
            coh = core.cohorts(sc, self.trad, ret, cost, H)
            g, c, n = ref_cohort(sc, self.trad, ret, cost, H)
            np.testing.assert_array_equal(coh["n_elig"], n)
            np.testing.assert_allclose(np.nan_to_num(coh["gross_bp"], nan=-1e9), np.nan_to_num(g, nan=-1e9), rtol=1e-9, atol=1e-9)
            np.testing.assert_allclose(np.nan_to_num(coh["cost_bp"], nan=-1e9), np.nan_to_num(c, nan=-1e9), rtol=1e-9)
            self.assertTrue(np.isfinite(g).sum() > 20 or hyp["rule"] == "MOM")

    def test_cohort_series_window_and_dating(self):
        cost = core.cost_matrix(self.trad, self.med)
        H = 5
        sc = core.score_str(self.p["C"], 5)
        coh = core.cohorts(sc, self.trad, core.forward_returns(self.p["O"], H, 0), cost, H)
        ws, we = 100, 380
        x, v, t = core.cohort_series(coh, H, ws, we)
        self.assertTrue(np.all(x == t + 1 + H))
        self.assertTrue(np.all(t + 1 >= ws) and np.all(x <= we))
        self.assertTrue(np.allclose(v, (coh["gross_bp"][t] - coh["cost_bp"][t] - coh["borrow_bp"]) / H))
        x2, v2, _ = core.cohort_series(coh, H, ws, we, cost_mult=1.5)
        np.testing.assert_allclose(v2, (coh["gross_bp"][t] - 1.5 * (coh["cost_bp"][t] + coh["borrow_bp"])) / H)
        x3, _, t3 = core.cohort_series(coh, H, ws, we, delay=1)
        self.assertTrue(np.all(x3 == t3 + 2 + H))

    def test_exact_cost_arithmetic(self):
        """Kuenstliches Panel: Gewinner/Verlierer bekannt -> Brutto und Netto von Hand."""
        T, N, H = 40, 100, 5
        O = np.ones((T, N)); C = np.ones((T, N))
        for j in range(N):
            C[:, j] = 1.0 + 0.001 * j * np.arange(T) / T      # Score STR = -log(C[t]/C[t-5]) ist fuer kleine j gross (kleine Steigung = "Verlierer" groesser?)
        score = np.tile(np.arange(N, dtype=float), (T, 1))     # Score = Spaltenindex: Long = j 80..99, Short = 0..19
        ret = np.zeros((T, N)); ret[:, 80:] = 0.02; ret[:, :20] = -0.01
        elig = np.ones((T, N), bool); cost = np.full((T, N), 10.0)
        coh = core.cohorts(score, elig, ret, cost, H)
        self.assertAlmostEqual(coh["gross_bp"][3], 0.5 * (0.02 + 0.01) * 1e4)     # 150
        self.assertAlmostEqual(coh["cost_bp"][3], 10.0)
        self.assertAlmostEqual(coh["borrow_bp"], 0.5 * H * 1.0)
        self.assertAlmostEqual(coh["net_bp"][3], 150 - 10 - 2.5)
        self.assertEqual((coh["n_long"][3], coh["n_short"][3], coh["k"][3]), (20, 20, 20))

    def test_min_elig_blocks_signal(self):
        T, N, H = 10, 99, 5
        score = np.random.default_rng(0).normal(size=(T, N)); ret = np.random.default_rng(1).normal(size=(T, N)) * 0.01
        coh = core.cohorts(score, np.ones((T, N), bool), ret, np.full((T, N), 5.0), H)
        self.assertFalse(coh["ok"].any())
        self.assertTrue(np.all(np.isnan(coh["net_bp"])))


class Stats(unittest.TestCase):
    def test_block_means_count(self):
        bm, _ = stats.block_means([np.arange(10.0), np.arange(100.0, 105.0)], block=4)
        self.assertEqual(len(bm), 7 + 2)
        self.assertAlmostEqual(bm[0], 1.5)
        self.assertAlmostEqual(bm[7], 100 + 1.5)

    def test_null_data_not_rejected_and_signal_rejected(self):
        rng = np.random.default_rng(5)
        z = rng.normal(0, 10, 2500)
        s0 = stats.summarize([z], ndraw=2000)
        self.assertGreater(s0["p"], 0.01)
        s1 = stats.summarize([z + 2.0], ndraw=2000)
        self.assertLess(s1["p"], 0.01)
        self.assertGreater(s1["lcb95_bp_day"], 0)
        self.assertAlmostEqual(s1["mean_bp_day"], z.mean() + 2.0)
        self.assertLess(s1["lcb95_bp_day"], s1["mean_bp_day"])
        self.assertAlmostEqual(s1["lcb95_bp_day"], s1["mean_bp_day"] - 1.645 * s1["se_bp_day"], delta=0.25 * s1["se_bp_day"])

    def test_mde_formula(self):
        s = stats.summarize([np.random.default_rng(0).normal(0, 5, 3000)], ndraw=1000)
        self.assertAlmostEqual(s["mde_bp_day"], 3.3393 * s["se_bp_day"])

    def test_deterministic(self):
        z = np.random.default_rng(2).normal(0, 3, 500)
        self.assertEqual(stats.summarize([z], ndraw=500), stats.summarize([z], ndraw=500))

    def test_autocorrelation_inflates_se(self):
        rng = np.random.default_rng(9)
        e = rng.normal(size=4000); x = np.zeros(4000)
        for i in range(1, 4000):
            x[i] = 0.8 * x[i - 1] + e[i]
        se_blk = stats.summarize([x], ndraw=1000)["se_bp_day"]
        self.assertGreater(se_blk, x.std() / np.sqrt(4000) * 1.5)

    def test_bh(self):
        self.assertEqual(stats.bh_reject([0.01, 0.04], 0.05), [True, True])
        self.assertEqual(stats.bh_reject([0.03, 0.04], 0.05), [True, True])      # 0.04 <= 2/2*0.05 -> beide
        self.assertEqual(stats.bh_reject([0.026, 0.9], 0.05), [False, False])
        self.assertEqual(stats.bh_reject([0.02, 0.9], 0.05), [True, False])
        self.assertEqual(stats.bh_reject([0.9, 0.02], 0.05), [False, True])


class ProtocolBits(unittest.TestCase):
    def test_decide_requires_all_conditions(self):
        base = {"id": "R-H1", "p": 0.001, "mean_bp_day": 3.0, "lcb95_bp_day": 1.0, "c1_power": True, "c3_placebo": True, "c3b_placebo_cols": True, "c4_stress": True,
                "c5_names": True, "c5_year": True, "per_window": {"E": {"mean_bp_day": 2.0}, "F": {"mean_bp_day": 4.0}}}
        a1 = {"id": "R-H1", "mean_bp_day": 1.0}
        a2 = {"id": "R-H2", "mean_bp_day": 1.0}
        other = dict(base, id="R-H2", p=0.9, mean_bp_day=-1.0, lcb95_bp_day=-3.0)
        d = P.decide_stage_b([base, other], [a1, a2])
        self.assertEqual(d[0]["category"], "HINWEIS-POSITIV (survivorship-behaftet)")
        self.assertEqual(d[1]["category"], "NULLBEFUND")
        for key, val in (("c3_placebo", False), ("c3b_placebo_cols", False), ("c4_stress", False), ("c5_names", False), ("c5_year", False)):
            d = P.decide_stage_b([dict(base, **{key: val}), other], [a1, a2])
            self.assertEqual(d[0]["category"], "NULLBEFUND", key)
        d = P.decide_stage_b([dict(base, per_window={"E": {"mean_bp_day": -1.0}, "F": {"mean_bp_day": 4.0}}), other], [a1, a2])
        self.assertEqual(d[0]["category"], "NULLBEFUND")
        d = P.decide_stage_b([dict(base, per_window={"E": {"mean_bp_day": 2.0}, "F": {"mean_bp_day": -4.0}}), other], [a1, a2])
        self.assertEqual(d[0]["category"], "NULLBEFUND")
        d = P.decide_stage_b([base, other], [dict(a1, mean_bp_day=-0.1), a2])
        self.assertEqual(d[0]["category"], "NULLBEFUND")
        d = P.decide_stage_b([dict(base, lcb95_bp_day=-0.1), other], [a1, a2])
        self.assertEqual(d[0]["category"], "NULLBEFUND")
        d = P.decide_stage_b([dict(base, p=0.04), dict(other, p=0.9)], [a1, a2])
        self.assertFalse(d[0]["bh_reject"])             # 0.04 > 1/2*0.05 -> BH lehnt nicht ab
        self.assertEqual(d[0]["category"], "NULLBEFUND")

    def test_never_bestaetigt(self):
        base = {"id": "R-H1", "p": 0.0001, "mean_bp_day": 9.0, "lcb95_bp_day": 5.0, "c1_power": True, "c3_placebo": True, "c3b_placebo_cols": True, "c4_stress": True,
                "c5_names": True, "c5_year": True, "per_window": {"E": {"mean_bp_day": 2.0}, "F": {"mean_bp_day": 4.0}}}
        d = P.decide_stage_b([base, dict(base, id="R-H2")], [{"id": "R-H1", "mean_bp_day": 1.0}, {"id": "R-H2", "mean_bp_day": 1.0}])
        for x in d:
            self.assertNotEqual(x["category"], "BESTAETIGT")


if __name__ == "__main__":
    unittest.main()


class IdCheck(unittest.TestCase):
    def test_id_mismatch_rejected(self):
        r = {"id": "R-H1", "p": 0.5, "mean_bp_day": 0, "lcb95_bp_day": 0, "c1_power": True, "c3_placebo": False, "c3b_placebo_cols": False, "c4_stress": False,
             "c5_names": False, "c5_year": False, "per_window": {"E": {"mean_bp_day": 0}, "F": {"mean_bp_day": 0}}}
        with self.assertRaises(ValueError):
            P.decide_stage_b([r, dict(r, id="R-H2")], [{"id": "R-H2", "mean_bp_day": 1}, {"id": "R-H1", "mean_bp_day": 1}])
