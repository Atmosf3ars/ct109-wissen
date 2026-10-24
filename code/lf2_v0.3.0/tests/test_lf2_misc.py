import os
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from lf2 import core, stats, protocol as P  # noqa: E402
from lf2.data import load_panel, window_bounds, read_csv  # noqa: E402

HEAD = "date,close,high,low,open,volume,adjClose,adjHigh,adjLow,adjOpen,adjVolume,divCash,splitFactor\n"


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        f.write(HEAD)
        for d, c, v, ac, ao in rows:
            f.write("%s,%s,1,1,1,%s,%s,1,1,%s,1,0,1\n" % (d, c, v, ac, ao))


class Pinned(unittest.TestCase):
    """Spec-Konstanten (RUNDE2_SPEC_v1) -- jede Aenderung ist eine neue Spec-Version."""

    def test_constants(self):
        self.assertEqual((core.MIN_DV, core.MIN_PX, core.MIN_HIST, core.DV_WIN, core.MIN_ELIG), (20e6, 5.0, 260, 60, 100))
        self.assertEqual(core.COST_CLASSES[0], (100, 4.0)); self.assertEqual(core.COST_CLASSES[1], (300, 7.0)); self.assertEqual(core.COST_CLASSES[2][1], 12.0)
        self.assertEqual((core.COST_PAD, core.BORROW_BP_PER_DAY), (1.25, 1.0))
        self.assertEqual((stats.BLOCK, stats.NBOOT, stats.NBOOT_GATE, stats.SEED, stats.DELTA_MIN, stats.Z_SUM, stats.Q_FDR), (20, 5000, 2000, 20261024, 2.0, 3.3393, 0.05))
        self.assertEqual((P.STRESS_COST, P.NPLACEBO, P.C_GATE_BP, P.GATE_P, P.GATE_W), (1.5, 1000, 8.75, 0.05, 0.10))
        self.assertEqual((P.CONC_TOP, P.CONC_TOP_MAX, P.CONC_YEAR_MAX), (10, 0.25, 0.40))
        self.assertEqual(P.WINDOWS, {"A": (20120103, 20191231), "E": (20050103, 20111230), "F": (20200102, 20260630)})
        self.assertEqual([(h["id"], h["rule"], h["H"]) for h in P.HYPOTHESES], [("R-H1", "STR", 5), ("R-H2", "MOM", 21)])
        self.assertEqual(P.HYPOTHESES[0]["params"], {"L": 5}); self.assertEqual(P.HYPOTHESES[1]["params"], {"far": 252, "skip": 21})

    def test_block_rule(self):
        self.assertEqual((stats.block_for(5), stats.block_for(10), stats.block_for(21), stats.block_for(30)), (20, 40, 84, 120))

    def test_gate_cell(self):
        rng = np.random.default_rng(3)
        daily = 300 + 40 * rng.standard_normal(1500)
        for H in (5, 21):
            c = P.gate_cell(daily, H)
            want = float(np.quantile(stats.boot_mean([daily], stats.block_for(H), stats.NBOOT_GATE, stats.SEED)[0], 0.05))
            self.assertEqual(c["lcb95_bp"], want)
            self.assertAlmostEqual(c["rho_min_plus"], 8.75 / want)
            self.assertEqual(c["class"], "P")
        self.assertEqual(P.gate_cell(daily * 0 + 1.0, 5)["class"], "X")          # winziges |r| -> rho riesig
        self.assertEqual(P.gate_cell(daily * 0, 5)["rho_min_plus"], float("inf"))

    def test_classify(self):
        self.assertEqual([P.classify_rho(x) for x in (0.0, 0.05, 0.0500001, 0.10, 0.1000001, 5.0, float("inf"))], ["P", "P", "W", "W", "X", "X", "X"])


class Loader(unittest.TestCase):
    def test_panel_alignment(self):
        d = tempfile.mkdtemp()
        cal = ["2020-01-02", "2020-01-03", "2020-01-06", "2020-01-07"]
        write_csv(os.path.join(d, "SPY.csv"), [(x, 10, 100, 10, 10) for x in cal] + [("2020-02-01", 10, 100, 10, 10)])
        write_csv(os.path.join(d, "AAA.csv"), [("2020-01-03", 20, 200, 19, 18), ("2020-01-06", 21, 300, 20, 19), ("2020-01-04", 5, 5, 5, 5), ("2020-01-07", 22, "", 21, 20)])
        p = load_panel(d, ["AAA", "MISSING", "SPY"], end_date=20200131)
        self.assertEqual(list(p["dates"]), [20200102, 20200103, 20200106, 20200107])
        self.assertEqual(p["symbols"], ["AAA"])
        self.assertEqual(p["dropped_rows"], 1)                             # 04.01. liegt nicht im SPY-Kalender
        self.assertTrue(np.isnan(p["O"][0, 0]))                            # nichts aufgefuellt
        self.assertEqual(p["O"][1, 0], 18); self.assertEqual(p["C"][2, 0], 20); self.assertEqual(p["CL"][2, 0], 21)
        self.assertTrue(np.isnan(p["V"][3, 0]))                            # leeres Feld -> NaN
        self.assertEqual(len(p["spy_close"]), 4)                           # Daten nach end_date abgeschnitten

    def test_window_bounds(self):
        dates = np.array([20111229, 20111230, 20120103, 20120104, 20191231, 20200102])
        self.assertEqual(window_bounds(dates, 20120103, 20191231), (2, 4))
        with self.assertRaises(ValueError):
            window_bounds(dates, 20300101, 20300201)


class FakeCtx:
    def __init__(self, ret, dates, bounds, trad=None, cost=None, score=None, opn=None):
        self._r, self.dates, self.bounds = ret, dates, bounds
        self.trad, self.cost, self._score, self._opn = trad, cost, score, opn

    def ret(self, H, delay=0):
        if self._opn is not None:
            return core.forward_returns(self._opn, H, delay)
        return self._r

    def score(self, hyp):
        return self._score


def make_dates(T, start_year=2012):
    out, y, m, d = [], start_year, 1, 1
    for i in range(T):
        out.append(y * 10000 + m * 100 + d)
        d += 1
        if d > 28:
            d = 1; m += 1
            if m > 12:
                m = 1; y += 1
    return np.array(out)


class Concentration(unittest.TestCase):
    def _coh(self, T, N, longs_fn, shorts_fn):
        mL = np.zeros((T, N), bool); mS = np.zeros((T, N), bool)
        for t in range(T):
            mL[t, longs_fn(t)] = True; mS[t, shorts_fn(t)] = True
        return {"ok": np.ones(T, bool), "_mL": mL, "_mS": mS}

    def test_diffuse_vs_concentrated(self):
        T, N, H = 400, 100, 5
        dates = make_dates(T)
        rng = np.random.default_rng(0)
        ret = rng.normal(0, 0.01, (T, N))
        rot = lambda t: [(t * 7 + k) % N for k in range(20)]
        rotS = lambda t: [(t * 7 + 50 + k) % N for k in range(20)]
        coh = self._coh(T, N, rot, rotS)
        ret = ret + 0.004 * coh["_mL"] - 0.004 * coh["_mS"]                 # echter, breit gestreuter Bruttogewinn
        ctx = FakeCtx(ret, dates, {"A": (0, T - 1)})
        series = [(np.arange(10, 300), np.ones(290), None)]
        r = P.concentration(ctx, {"H": H}, ["A"], coh, series)
        self.assertTrue(r["c5_names"], r)
        ctx_neg = FakeCtx(-ret, dates, {"A": (0, T - 1)})                   # Bruttogewinn <= 0 -> (i) nicht erfuellbar
        self.assertFalse(P.concentration(ctx_neg, {"H": H}, ["A"], coh, series)["c5_names"])
        # konzentriert: Aktie 0 immer Long mit riesiger Rendite
        ret2 = ret.copy(); ret2[:, 0] = 0.5
        ctx2 = FakeCtx(ret2, dates, {"A": (0, T - 1)})
        coh2 = self._coh(T, N, lambda t: [0] + [1 + (t + k) % 99 for k in range(19)], rotS)
        r2 = P.concentration(ctx2, {"H": H}, ["A"], coh2, series)
        self.assertFalse(r2["c5_names"], r2)
        self.assertGreater(r2["top10_share"], 0.25)

    def test_year_share(self):
        T, N, H = 1200, 100, 5
        dates = make_dates(T)
        ctx = FakeCtx(np.zeros((T, N)), dates, {"A": (0, T - 1)})
        coh = self._coh(T, N, lambda t: [0], lambda t: [1])
        y1 = np.where(dates // 10000 == 2012)[0][:100]; y2 = np.where(dates // 10000 == 2013)[0][:100]; y3 = np.where(dates // 10000 == 2014)[0][:100]
        ser_ok = [(np.concatenate([y1, y2, y3]), np.ones(300), None)]            # je 33 %
        self.assertTrue(P.concentration(ctx, {"H": H}, ["A"], coh, ser_ok)["c5_year"])
        ser_bad = [(np.concatenate([y1, y2]), np.concatenate([np.ones(100) * 3, np.ones(100)]), None)]       # 75 % in einem Jahr
        ser_neg = [(np.concatenate([y1, y2]), np.concatenate([-np.ones(100) * 3, np.ones(100)]), None)]       # Gesamtnetto <= 0 -> (ii) nicht geprueft
        self.assertTrue(P.concentration(ctx, {"H": H}, ["A"], coh, ser_neg)["c5_year"])
        r = P.concentration(ctx, {"H": H}, ["A"], coh, ser_bad)
        self.assertFalse(r["c5_year"]); self.assertAlmostEqual(r["max_year_share"], 0.75)


class Tradability(unittest.TestCase):
    def _panel(self, close, vol, T=300):
        CL = np.full((T, 1), close, dtype=float); V = np.full((T, 1), vol, dtype=float)
        return core.tradable(CL, V)

    def test_basic_pass_and_price_floor(self):
        ok, _ = self._panel(50.0, 1e6)                       # 50 Mio USD Dollarvolumen
        self.assertTrue(ok[-1, 0]); self.assertFalse(ok[100, 0])        # Historie < 260 Tage
        ok2, med2 = self._panel(4.0, 1e8)                    # Preis unter 5 USD, Dollarvolumen riesig
        self.assertGreater(med2[-1, 0], core.MIN_DV); self.assertFalse(ok2[-1, 0])
        ok3, _ = self._panel(50.0, 1e5)                      # 5 Mio USD < 20 Mio
        self.assertFalse(ok3[-1, 0])

    def test_min_valid_days_in_window(self):
        T = 300
        CL = np.full((T, 1), 50.0); V = np.full((T, 1), 1e6)
        V[250:290:1, 0] = np.nan                             # 40 fehlende Tage im 60-Tage-Fenster ab t=299 -> nur 20 gueltige
        CL[250:290:1, 0] = np.nan
        ok, med = core.tradable(CL, V)
        self.assertTrue(np.isnan(med[299, 0])); self.assertFalse(ok[299, 0])
        V2 = np.full((T, 1), 1e6); CL2 = np.full((T, 1), 50.0)
        V2[280:290, 0] = np.nan; CL2[280:290, 0] = np.nan    # 10 fehlend -> 50 gueltig -> gerade noch ok
        ok2, med2 = core.tradable(CL2, V2)
        self.assertTrue(np.isfinite(med2[299, 0]))
        V3 = np.full((T, 1), 1e6); CL3 = np.full((T, 1), 50.0)
        V3[270:290, 0] = np.nan; CL3[270:290, 0] = np.nan    # 20 fehlend -> 40 gueltig -> NaN
        self.assertTrue(np.isnan(core.tradable(CL3, V3)[1][299, 0]))


class Placebo(unittest.TestCase):
    def test_random_and_reproducible(self):
        T, N = 300, 150
        rng = np.random.default_rng(0)
        ctx = FakeCtx(rng.normal(0, 0.02, (T, N)), make_dates(T), {"A": (20, 280)}, trad=np.ones((T, N), bool), cost=np.full((T, N), 5.0))
        hyp = {"id": "X", "H": 5}
        m1 = P.placebo_means(ctx, hyp, ["A"], 40, 123)
        m2 = P.placebo_means(ctx, hyp, ["A"], 40, 123)
        m3 = P.placebo_means(ctx, hyp, ["A"], 40, 124)
        np.testing.assert_array_equal(m1, m2)
        self.assertFalse(np.array_equal(m1, m3))
        self.assertGreater(np.std(m1), 0.1)                                   # Ziehungen unterscheiden sich
        self.assertLess(abs(np.mean(m1) - (-(5.0 + 2.5) / 5)), 1.0)           # Mittel ~ -(Kosten+Leihe)/H


class StressAndPlacebo(unittest.TestCase):
    def _world(self, T=400, N=140, seed=5):
        rng = np.random.default_rng(seed)
        opn = 50 * np.exp(np.cumsum(rng.normal(0, 0.02, (T, N)), axis=0))
        score = rng.normal(size=(T, N))
        trad = np.ones((T, N), bool)
        cost = np.full((T, N), 6.0)
        return FakeCtx(None, make_dates(T), {"A": (30, 370)}, trad=trad, cost=cost, score=score, opn=opn)

    def test_stress_means_match_independent_calc(self):
        ctx = self._world()
        hyp = {"id": "X", "H": 5}
        m_cost, m_lat = P.stress_means(ctx, hyp, ["A"])
        coh = core.cohorts(ctx._score, ctx.trad, ctx.ret(5, 0), ctx.cost, 5)
        x, v, _ = core.cohort_series(coh, 5, 30, 370, 0, 1.5)
        base = core.cohort_series(coh, 5, 30, 370, 0, 1.0)[1]
        self.assertAlmostEqual(m_cost, float(np.mean(v)))
        self.assertLess(m_cost, float(np.mean(base)) - 0.1)                       # Kosten und Leihe wirken wirklich
        coh1 = core.cohorts(ctx._score, ctx.trad, ctx.ret(5, 1), ctx.cost, 5)
        v1 = core.cohort_series(coh1, 5, 30, 370, 1, 1.0)[1]
        self.assertAlmostEqual(m_lat, float(np.mean(v1)))
        self.assertNotAlmostEqual(m_lat, float(np.mean(base)), places=3)

    def test_placebo_threshold(self):
        self.assertEqual(P.placebo_threshold(np.arange(101.0)), 95.0)
        self.assertIsNone(P.placebo_threshold(np.array([])))

    def test_placebo_window_alignment(self):
        T, N = 300, 150
        ctx = FakeCtx(np.zeros((T, N)), make_dates(T), {"A": (100, 200)}, trad=np.ones((T, N), bool), cost=np.zeros((T, N)))
        ctx.cost[:99] = 1000.0; ctx.cost[195:] = 1000.0                       # nur ausserhalb des Fensters teuer
        m = P.placebo_means(ctx, {"id": "X", "H": 5}, ["A"], 5, 1)
        np.testing.assert_allclose(m, -(0 + 2.5) / 5, atol=1e-9)               # nur Leihe, keine Kosten im Fenster
        m2 = P.placebo_means_cols(FakeCtx(np.zeros((T, N)), make_dates(T), {"A": (100, 200)}, trad=np.ones((T, N), bool), cost=ctx.cost,
                                          score=np.random.default_rng(0).normal(size=(T, N))), {"id": "X", "H": 5}, ["A"], 5, 1)
        np.testing.assert_allclose(m2, -(0 + 2.5) / 5, atol=1e-9)

    def test_cols_placebo_keeps_persistence_and_kills_link(self):
        T, N = 500, 150
        rng = np.random.default_rng(1)
        score = np.cumsum(rng.normal(size=(T, N)), axis=0) * 0.1                # sehr persistent
        opn = 50 * np.exp(np.cumsum(0.0005 * np.sign(score) + rng.normal(0, 0.01, (T, N)), axis=0))   # Rendite haengt (verzoegert) am Score
        ctx = FakeCtx(None, make_dates(T), {"A": (30, 460)}, trad=np.ones((T, N), bool), cost=np.zeros((T, N)), score=score, opn=opn)
        hyp = {"id": "X", "H": 5}
        real = float(np.mean(P.series_for(ctx, hyp, ["A"])[0][0][1]))
        pl = P.placebo_means_cols(ctx, hyp, ["A"], 40, 3)
        self.assertGreater(real, np.quantile(pl, 0.95))                         # echter Zusammenhang wird erkannt
        pl_days = P.placebo_means(ctx, hyp, ["A"], 40, 3)
        self.assertGreater(np.std(pl), np.std(pl_days))                         # persistentes Placebo streut breiter (kalibriert)
        np.testing.assert_array_equal(pl, P.placebo_means_cols(ctx, hyp, ["A"], 40, 3))


class ConcentrationExact(unittest.TestCase):
    def test_top_share_brute_force_and_window_end(self):
        T, N, H = 80, 15, 5
        rng = np.random.default_rng(4)
        ret = rng.normal(0.002, 0.02, (T, N))
        ret[60:, 0] = 5.0                                                        # nach dem Fensterende: darf nicht zaehlen
        mL = np.zeros((T, N), bool); mS = np.zeros((T, N), bool)
        for t in range(T):
            mL[t, [(t + k) % N for k in range(4)]] = True
            mS[t, [(t + 7 + k) % N for k in range(4)]] = True
        mL[:, 0] = True
        coh = {"ok": np.ones(T, bool), "_mL": mL, "_mS": mS}
        ctx = FakeCtx(ret, make_dates(T), {"A": (5, 60)})
        r = P.concentration(ctx, {"H": H}, ["A"], coh, [])
        contrib = np.zeros(N)
        for t in range(T):
            if t + 1 >= 5 and t + 1 + H <= 60:
                L = np.where(mL[t])[0]; S = np.where(mS[t])[0]
                for j in L: contrib[j] += 0.5 / len(L) * ret[t, j] * 1e4 / H
                for j in S: contrib[j] -= 0.5 / len(S) * ret[t, j] * 1e4 / H
        want = np.sort(contrib)[::-1][:10].sum() / contrib.sum()
        self.assertAlmostEqual(r["top10_share"], want, places=9)
        self.assertAlmostEqual(r["gross_total_bp_day_sum"], contrib.sum(), places=6)


class CodeHashAndIO(unittest.TestCase):
    def test_code_hash_ignores_line_endings(self):
        import shutil
        from lf2.util import code_hash
        src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lf2")
        d = tempfile.mkdtemp()
        dst = os.path.join(d, "lf2"); os.makedirs(dst)
        for n in os.listdir(src):
            if n.endswith(".py"):
                body = open(os.path.join(src, n), "rb").read().replace(b"\r\n", b"\n")
                open(os.path.join(dst, n), "wb").write(body.replace(b"\n", b"\r\n"))
        self.assertEqual(code_hash(dst), code_hash(src))
        open(os.path.join(dst, "core.py"), "ab").write(b"# x\r\n")
        self.assertNotEqual(code_hash(dst), code_hash(src))
        shutil.rmtree(d)

    def test_write_once(self):
        from lf2.util import write_once
        d = tempfile.mkdtemp()
        p = os.path.join(d, "a.json")
        self.assertTrue(write_once(p, "eins\n"))
        self.assertFalse(write_once(p, "zwei\n"))
        self.assertEqual(open(p).read(), "eins\n")
        self.assertEqual(os.listdir(d), ["a.json"])                             # keine Reste

    def test_dropped_legs_counted(self):
        T, N, H = 10, 100, 5
        score = np.tile(np.arange(N, dtype=float), (T, 1))
        ret = np.full((T, N), 0.01)
        ret[3, 95:99] = np.nan                                                   # 4 Long-Namen ohne Exit
        coh = core.cohorts(score, np.ones((T, N), bool), ret, np.full((T, N), 5.0), H)
        self.assertEqual(int(coh["dropped_legs"][3]), 4); self.assertEqual(int(coh["legs_total"][3]), 40)
        self.assertEqual(int(coh["dropped_legs"][2]), 0)


if __name__ == "__main__":
    unittest.main()
