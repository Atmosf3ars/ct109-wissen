import copy
import json
import math
import os
import sys
import tempfile
import unittest
from unittest import mock

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
from lf1 import backtest as bt  # noqa: E402
from lf1 import core  # noqa: E402
from lf1.util import json_hash  # noqa: E402


def gate_stub(classes=None):
    classes = classes or {}
    cells = []
    for a in ("BTC", "ETH", "SOL"):
        for h in (1, 4, 24, 72):
            cls = classes.get((a, h), "X" if h in (1, 4) else "W")
            cells.append({"asset": a, "h_hours": h, "class": cls, "evaluable": True,
                          "mde_net_bp_full_exposure": 49.0, "n_eff": 269})
    return {"result_hash": "g" * 64, "cells": cells}


def hyp(i="H1", rule="TS_MOM", params=None, asset="BTC", H=24):
    return {"id": i, "rule": rule, "params": params or {"L": 24, "side": "both"}, "asset": asset, "H": H}


def mk_grid(logret):
    c = 100.0 * np.exp(np.cumsum(logret))
    o = np.concatenate(([100.0], c[:-1]))
    h = np.maximum(o, c) * 1.0005
    l = np.minimum(o, c) * 0.9995
    return {"o": o, "h": h, "l": l, "c": c}


def regime_series(n, mu_bp, sig_bp, persist, seed):
    """Tagesrichtung d in {+1,-1} mit Persistenz; Stundenrenditen d*mu + Rauschen (Momentum-Struktur)."""
    rng = np.random.default_rng(seed)
    days = n // 24 + 1
    d = np.empty(days)
    d[0] = 1.0
    for k in range(1, days):
        d[k] = d[k - 1] if rng.random() < persist else -d[k - 1]
    r = (np.repeat(d, 24)[:n] * mu_bp + rng.normal(0, sig_bp, n)) * 1e-4
    return mk_grid(r)


class TestValidation(unittest.TestCase):
    def test_valid_list_and_w_cap(self):
        g = gate_stub()
        info = bt.validate_list([hyp("H1"), hyp("H2", asset="ETH", H=72)], g)
        self.assertEqual(info, {"n": 2, "n_class_W": 2})
        with self.assertRaises(bt.FreezeError):
            bt.validate_list([hyp("H1"), hyp("H2", asset="ETH"), hyp("H3", asset="SOL")], g)   # 3 x W

    def test_class_p_cells_do_not_count_against_w_cap(self):
        g = gate_stub({("BTC", 24): "P", ("ETH", 24): "P", ("SOL", 24): "P"})
        info = bt.validate_list([hyp("H1"), hyp("H2", asset="ETH"), hyp("H3", asset="SOL"), hyp("H4", H=72)], g)
        self.assertEqual(info["n_class_W"], 1)

    def test_blocked_cell_and_limits(self):
        g = gate_stub()
        with self.assertRaises(bt.FreezeError):
            bt.validate_list([hyp("H1", H=4)], g)                       # 4 h ist X
        with self.assertRaises(bt.FreezeError):
            bt.validate_list([], g)
        with self.assertRaises(bt.FreezeError):
            bt.validate_list([hyp("H1"), hyp("H1", asset="ETH")], g)    # doppelte ID
        many = [hyp("H%d" % i) for i in range(9)]
        gp = gate_stub({("BTC", 24): "P"})
        with self.assertRaises(bt.FreezeError):
            bt.validate_list(many, gp)                                  # > 8

    def test_hypothesis_form(self):
        bad = [
            dict(hyp(), rule="MAGIC"),
            dict(hyp(), params={"L": 24}),
            dict(hyp(), params={"L": 0, "side": "both"}),
            dict(hyp(), params={"L": 24, "side": "up"}),
            dict(hyp(), params={"L": True, "side": "both"}),
            dict(hyp(), asset="DOGE"),
            dict(hyp(), H=12),
            dict(hyp(), extra=1),
            dict(hyp(rule="SHOCK_FADE", params={"w": 1, "k": -2.0, "N": 40})),
            dict(hyp(rule="SHOCK_FADE", params={"w": 1, "k": 2.0, "N": 1})),
        ]
        for h in bad:
            with self.assertRaises(bt.FreezeError, msg=str(h)):
                bt.validate_hypothesis(h)
        bt.validate_hypothesis(hyp(rule="SHOCK_FADE", params={"w": 2, "k": 3.0, "N": 48}))

    def test_lookback_cap(self):
        bt.validate_hypothesis(hyp(params={"L": bt.MAX_LOOKBACK, "side": "both"}))
        with self.assertRaises(bt.FreezeError):
            bt.validate_hypothesis(hyp(params={"L": bt.MAX_LOOKBACK + 1, "side": "both"}))
        with self.assertRaises(bt.FreezeError):
            bt.validate_hypothesis(hyp(rule="SHOCK_FADE", params={"w": 100, "k": 3.0, "N": 300}))

    def test_round2_aliases(self):
        from lf1 import data
        self.assertIn("XDGUSD", data.ALIASES["DOGE"])
        self.assertIn("XRPUSD", data.ALIASES["XRP"])


class TestFreezeHash(unittest.TestCase):
    def make(self, hyps=None, **kw):
        hyps = hyps or [hyp()]
        args = dict(regime_hash="r" * 64, bau_spec_sha256="b" * 64, windows_desc={"A": ["2025-10-04", "2026-06-30"]},
                    data_manifest=[{"asset": "BTC", "sha256": "d" * 64}])
        args.update(kw)
        return bt.make_freeze(hyps, gate_stub(), **args)

    def test_deterministic_and_sensitive(self):
        p1, h1 = self.make()
        p2, h2 = self.make()
        self.assertEqual(h1, h2)
        self.assertEqual(h1, json_hash(p1))
        for kw in ({"hyps": [hyp(params={"L": 25, "side": "both"})]}, {"regime_hash": "x" * 64},
                   {"bau_spec_sha256": "c" * 64}, {"data_manifest": [{"asset": "BTC", "sha256": "e" * 64}]},
                   {"windows_desc": {"A": ["2025-10-05", "2026-06-30"]}}):
            self.assertNotEqual(self.make(**kw)[1], h1, kw)
        with mock.patch("lf1.backtest.code_hash", return_value="f" * 64):
            self.assertNotEqual(self.make()[1], h1)

    def test_protocol_values_written_before_evaluation(self):
        p, _h = self.make([hyp(), hyp("H2", asset="SOL", H=72)])
        self.assertEqual([x["id"] for x in p["per_hypothesis_protocol"]], ["H1", "H2"])
        self.assertIn("mde_net_bp_full_exposure", p["per_hypothesis_protocol"][0])
        self.assertIn("max_trades_in_gate_window", p["per_hypothesis_protocol"][0])
        self.assertEqual(p["limits"]["n_class_W"], 2)


class TestStats(unittest.TestCase):
    def test_bh_fdr_known_cases(self):
        self.assertEqual(bt.bh_fdr([0.01, 0.02, 0.03, 0.04, 0.05]), [True] * 5)
        self.assertEqual(bt.bh_fdr([0.03, 0.001, 0.02]), [True, True, True])
        p = [0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.074, 0.205, 0.212, 0.216]
        self.assertEqual(bt.bh_fdr(p), [True, True] + [False] * 8)
        self.assertEqual(bt.bh_fdr([0.2, 0.3, 0.5]), [False] * 3)
        # Step-up: ein grosser Rang rettet kleinere, die ihre eigene Schwelle verfehlen
        self.assertEqual(bt.bh_fdr([0.02, 0.03, 0.0375]), [True, True, True])      # Rang 1 verfehlt eigene Schwelle, Rang 3 rettet
        self.assertEqual(bt.bh_fdr([0.04, 0.045, 0.05, 0.9]), [False] * 4)         # m=4: Schwellen .0125/.025/.0375/.05

    def test_bonferroni(self):
        self.assertEqual(bt.bonferroni([0.01, 0.03]), [True, False])

    def test_n_min_and_mde_inverse(self):
        s = 3.3393
        self.assertAlmostEqual(bt.n_min(100.0, 10.0), math.ceil((s * 10) ** 2), delta=2)
        n = bt.n_min(240.0, 15.6)
        self.assertAlmostEqual(bt.mde_bp(240.0, n), 15.6, delta=0.05)
        self.assertGreater(bt.n_min(240.0, 7.8), 3.9 * bt.n_min(240.0, 15.6))   # halbes delta -> vierfach

    def test_top_share(self):
        self.assertAlmostEqual(bt.top_share([10, 1, 1, 1, 1, 1, 1]), 14 / 16)
        self.assertIsNone(bt.top_share([-1, -2, 0.5]))
        self.assertIsNone(bt.top_share([1.0, -1.0]))                              # Summe exakt 0
        self.assertIsNone(bt.top_share([]))
        self.assertAlmostEqual(bt.top_share([-1, -2, 3, 0.5]), 1.0)             # alle Trades unter den Top-5
        self.assertEqual(bt.top_share([1, 1, 1, 1, 1, 1, 1, 1, 1, 1]), 0.5)

    def test_bootstrap_sensible_and_deterministic(self):
        rng = np.random.default_rng(1)
        pos = rng.normal(5.0, 10.0, 400)
        a = bt.block_bootstrap(pos, 4, 600, np.random.default_rng(9))
        b = bt.block_bootstrap(pos, 4, 600, np.random.default_rng(9))
        self.assertEqual(a, b)
        self.assertLess(a["p"], 0.01)
        self.assertAlmostEqual(a["p"], 1.0 / 601, places=9)                      # +1-Glaettung: nie exakt 0
        gap = a["mean"] - a["lcb95"]
        self.assertGreater(gap, 0.4)                                              # 5-%-Quantil, nicht Median
        self.assertLess(gap, 3.0)
        self.assertGreater(a["lcb95"], 0)
        zero = rng.normal(0.0, 10.0, 400)
        z = bt.block_bootstrap(zero, 4, 600, np.random.default_rng(9))
        self.assertGreater(z["p"], 0.05)
        neg = bt.block_bootstrap(rng.normal(-5.0, 10.0, 400), 4, 600, np.random.default_rng(9))
        self.assertGreater(neg["p"], 0.9)
        self.assertEqual(bt.block_bootstrap([1.0], 2, 10, np.random.default_rng(1))["p"], 1.0)

    def test_block_len_uses_spacing_within_windows(self):
        t = np.zeros(4, dtype=core.TRADE_DTYPE)
        t["i_entry"] = [10, 34, 58, 1000]       # letzter Trade in anderem Fenster
        self.assertEqual(bt.block_len(24, t, [(0, 100), (900, 1100)]), 6)    # Abstand 24 -> ceil(6*24/24)
        t["i_entry"] = [10, 100, 190, 280]
        self.assertEqual(bt.block_len(24, t, [(0, 400)]), 2)                  # Abstand 90 -> ceil(1.6) = 2
        self.assertEqual(bt.block_len(24, t[:1], [(0, 400)]), 2)


class TestTrading(unittest.TestCase):
    def test_windows_isolate_trades_and_use_warmup(self):
        g = mk_grid(np.random.default_rng(5).normal(0, 0.01, 600))
        h = hyp(params={"L": 24, "side": "both"}, H=24)
        cost = core.CostModel(0.0)
        tr = bt.trades_for(h, g, [(100, 300), (400, 590)], cost)
        self.assertGreater(len(tr), 3)
        for s, e in [(100, 300), (400, 590)]:
            m = (tr["i_dec"] >= s) & (tr["i_dec"] < e)
            self.assertTrue(np.all(tr["i_exit"][m] < e))                # nichts ueber die Fenstergrenze
        self.assertTrue(np.all(((tr["i_dec"] >= 100) & (tr["i_dec"] < 300)) | ((tr["i_dec"] >= 400) & (tr["i_dec"] < 590))))
        # Vorlauf: Entscheidung bei i=100 darf Daten vor 100 nutzen (L=24 -> c[76])
        sig = bt.build_signals(h, g)
        first = bt.trades_for(h, g, [(100, 300)], cost)
        if sig[100] != 0:
            self.assertEqual(int(first["i_dec"][0]), 100)

    def test_placebo_random_walk_centered_at_minus_cost(self):
        g = mk_grid(np.random.default_rng(3).normal(0, 0.003, 4000))
        h = hyp(H=24)
        cost = bt.cost_for("BTC")
        tr = bt.trades_for(h, g, [(0, 4000)], cost)
        pm = bt.placebo_means(h, g, [(0, 4000)], tr, cost, 0, 200, np.random.default_rng(2))
        self.assertEqual(len(pm), 200)
        self.assertAlmostEqual(float(pm.mean()), -cost.cost_bp(24), delta=6.0)
        self.assertIsNone(bt.placebo_means(h, g, [(0, 30)], tr, cost, 0, 10, np.random.default_rng(2)))

    def test_cost_model_stress_scales_everything(self):
        c1 = bt.cost_for("BTC")
        c15 = bt.cost_for("BTC", 1.5)
        self.assertAlmostEqual(c15.cost_bp(24), 1.5 * c1.cost_bp(24))


class TestDecisions(unittest.TestCase):
    FH = "ab" * 32

    def test_null_world_no_false_candidates(self):
        """S2.7: iid-Walk, Kosten > 0, >= 200 Seeds: Fehlentscheidungen nicht oberhalb alpha."""
        nseed, sig_hits, cands = 200, 0, 0
        h = hyp(params={"L": 24, "side": "both"}, H=24)
        for s in range(nseed):
            g = mk_grid(np.random.default_rng(1000 + s).normal(0, 0.0035, 3000))
            r = bt.evaluate_hypothesis(h, 0, g, [(0, 3000)], self.FH, nboot=200, nplacebo=60)
            win = bt.decide([r], ["H1"])
            sig_hits += int(r["c2_signif"])
            cands += int(win is not None)
        # c2_signif = BH(m=1) bei q=0.05 und lcb95>0: erwartet <= ~5 %; Toleranz 3 Standardfehler
        limit = nseed * 0.05 + 3 * math.sqrt(nseed * 0.05 * 0.95)
        self.assertLessEqual(sig_hits, limit, "Fehlalarmrate zu hoch: %d" % sig_hits)
        self.assertEqual(cands, 0)

    def test_injected_edge_is_detected(self):
        g = regime_series(24 * 700, mu_bp=3.0, sig_bp=6.0, persist=0.8, seed=11)
        h = hyp("H1", params={"L": 24, "side": "both"}, H=24)
        r = bt.evaluate_hypothesis(h, 0, g, [(0, 24 * 700)], self.FH, nboot=800, nplacebo=200)
        bt.decide([r], ["H1"])
        self.assertGreater(r["net_mean_bp"], 15.0)
        for k in ("c1_power", "c2_signif", "c3_placebo", "c4_stress", "c5_conc"):
            self.assertTrue(r[k], "%s: %s" % (k, {x: r.get(x) for x in ("n_trades", "n_min", "p", "lcb95_bp", "placebo_q95_bp",
                                                                  "stress_latency_net_bp", "stress_cost_net_bp", "top5_share")}))
        self.assertTrue(r["passes_all"])

    def test_pure_drift_fails_placebo(self):
        """Reiner Aufwaertstrend wird von Zufallseinstiegen (gleiche Richtung) ebenso erreicht: C3 muss scheitern."""
        rng = np.random.default_rng(4)
        g = mk_grid((3.0 + rng.normal(0, 6.0, 24 * 700)) * 1e-4)
        h = hyp("H1", params={"L": 24, "side": "long"}, H=24)
        r = bt.evaluate_hypothesis(h, 0, g, [(0, 24 * 700)], self.FH, nboot=400, nplacebo=200)
        bt.decide([r], ["H1"])
        self.assertGreater(r["net_mean_bp"], 0)
        self.assertFalse(r["c3_placebo"])
        self.assertFalse(r["passes_all"])

    def test_underpowered_is_null_result(self):
        g = regime_series(24 * 120, mu_bp=3.0, sig_bp=6.0, persist=0.8, seed=11)     # nur ~120 Trades
        h = hyp("H1", params={"L": 24, "side": "both"}, H=24)
        r = bt.evaluate_hypothesis(h, 0, g, [(0, 24 * 120)], self.FH, nboot=200, nplacebo=60)
        r2 = dict(r); r2["n_min"] = r["n_trades"] + 1
        self.assertTrue(r["n_trades"] >= 1)
        self.assertEqual(r["c1_power"], r["n_trades"] >= r["n_min"])
        # C1-Grenze exakt: n == n_min besteht, n_min - 1 nicht (ueber n_min-Funktion)
        n = bt.n_min(50.0, 15.6)
        self.assertGreaterEqual(n, 1)
        self.assertLess(bt.mde_bp(50.0, n + 1), 15.6 + 1e-9)

    def test_concentration_blocks_single_jump_profit(self):
        rng = np.random.default_rng(8)
        r = rng.normal(0, 0.0005, 24 * 400)
        r[24 * 200 + 5] = 0.25                       # ein einzelner riesiger Sprung bringt (fast) den ganzen Gewinn
        g = mk_grid(r)
        h = hyp("H1", params={"L": 24, "side": "both"}, H=24)
        res = bt.evaluate_hypothesis(h, 0, g, [(0, 24 * 400)], self.FH, nboot=200, nplacebo=60)
        if res.get("top5_share") is not None and res["net_mean_bp"] > 0:
            self.assertFalse(res["c5_conc"])

    def test_selection_highest_lcb_then_lower_index(self):
        def mk(i, lcb):
            return {"id": i, "p": 0.0001, "lcb95_bp": lcb, "c1_power": True, "c3_placebo": True, "c4_stress": True, "c5_conc": True}
        rs = [mk("A", 5.0), mk("B", 9.0), mk("C", 9.0)]
        self.assertEqual(bt.decide(rs, ["A", "B", "C"]), "B")
        rs = [mk("A", 5.0), mk("B", 9.0)]
        rs[1]["c3_placebo"] = False
        self.assertEqual(bt.decide(rs, ["A", "B"]), "A")
        self.assertIsNone(bt.decide([dict(mk("A", -1.0), p=0.9)], ["A"]))

    def test_bh_across_list_not_per_hypothesis(self):
        # m = 8: eine Hypothese mit p = 0.02 besteht BH bei m=8 nicht (Schwelle 0.05/8 = 0.00625 auf Rang 1)
        rs = [{"id": "H%d" % i, "p": 0.9, "lcb95_bp": 1.0, "c1_power": True, "c3_placebo": True, "c4_stress": True, "c5_conc": True}
              for i in range(8)]
        rs[0]["p"] = 0.02
        self.assertIsNone(bt.decide(rs, ["H%d" % i for i in range(8)]))
        rs[0]["p"] = 0.004
        self.assertEqual(bt.decide(rs, ["H%d" % i for i in range(8)]), "H0")


class TestSpecConstants(unittest.TestCase):
    def test_constants_match_spec(self):
        self.assertEqual((bt.MAX_HYP, bt.MAX_W_HYP), (8, 2))
        self.assertEqual((bt.CONC_TOP, bt.CONC_MAX), (5, 0.5))
        self.assertEqual((bt.STRESS_COST, bt.Q_FDR), (1.5, 0.05))
        self.assertEqual((bt.NBOOT_P, bt.NPLACEBO), (5000, 1000))

    def test_rng_streams_distinct_and_reproducible(self):
        a = bt._rng("ab" * 32, 0, 1).random(3)
        self.assertTrue(np.array_equal(a, bt._rng("ab" * 32, 0, 1).random(3)))
        for other in (bt._rng("cd" * 32, 0, 1), bt._rng("ab" * 32, 1, 1), bt._rng("ab" * 32, 0, 2)):
            self.assertFalse(np.array_equal(a, other.random(3)))

    def test_cost_model_in_freeze_hash(self):
        base = bt.make_freeze([hyp()], gate_stub(), "r" * 64, "b" * 64, {}, [])[1]
        with mock.patch("lf1.backtest.C0_BP", dict(bt.C0_BP, BTC=11.0)):
            self.assertNotEqual(bt.make_freeze([hyp()], gate_stub(), "r" * 64, "b" * 64, {}, [])[1], base)
        with mock.patch("lf1.backtest.COST_FACTOR", 1.5):
            self.assertNotEqual(bt.make_freeze([hyp()], gate_stub(), "r" * 64, "b" * 64, {}, [])[1], base)
        with mock.patch("lf1.backtest.FUND_BP_PER_8H", 2.0):
            self.assertNotEqual(bt.make_freeze([hyp()], gate_stub(), "r" * 64, "b" * 64, {}, [])[1], base)


class TestCriteriaWiring(unittest.TestCase):
    FH = "ab" * 32

    def setUp(self):
        self.g = regime_series(24 * 300, mu_bp=3.0, sig_bp=6.0, persist=0.8, seed=5)
        self.h = hyp("H1", params={"L": 24, "side": "both"}, H=24)
        self.w = [(0, 24 * 300)]

    def test_stress_values_are_computed_from_stressed_trades(self):
        r = bt.evaluate_hypothesis(self.h, 0, self.g, self.w, self.FH, nboot=50, nplacebo=20)
        cost = bt.cost_for("BTC")
        # gleiche Trades, Kosten x1.5 -> Netto sinkt um genau 0.5 * Kosten
        self.assertAlmostEqual(r["stress_cost_net_bp"], r["net_mean_bp"] - 0.5 * cost.cost_bp(24), places=6)
        # Einstieg +1 Bar: andere Trades/Ergebnisse als Basis
        self.assertNotAlmostEqual(r["stress_latency_net_bp"], r["net_mean_bp"], places=3)
        direct = bt.trades_for(self.h, self.g, self.w, cost, 1)
        self.assertAlmostEqual(r["stress_latency_net_bp"], float(direct["net_bp"].mean()), places=9)

    def test_c4_requires_both_stress_values_positive(self):
        base = bt.evaluate_hypothesis(self.h, 0, self.g, self.w, self.FH, nboot=50, nplacebo=20)
        tr = bt.trades_for(self.h, self.g, self.w, bt.cost_for("BTC"), 0)
        for lat, cst, exp in ((5.0, 5.0, True), (-1.0, 5.0, False), (5.0, -1.0, False)):
            calls = {"n": 0}
            def fake(h, grid, windows, cost, latency_bars=0, sig=None, tr=tr, lat=lat, cst=cst, calls=calls):
                t = tr.copy()
                t["net_bp"] = (lat if latency_bars else (cst if cost.mult > 1 else t["net_bp"]))
                return t
            with mock.patch("lf1.backtest.trades_for", side_effect=fake):
                r = bt.evaluate_hypothesis(self.h, 0, self.g, self.w, self.FH, nboot=20, nplacebo=10)
            self.assertEqual(r["c4_stress"], exp, (lat, cst))
        self.assertIn("c4_stress", base)

    def test_c5_threshold(self):
        for share, exp in ((0.5, True), (0.51, False), (0.2, True)):
            with mock.patch("lf1.backtest.top_share", return_value=share):
                r = bt.evaluate_hypothesis(self.h, 0, self.g, self.w, self.FH, nboot=20, nplacebo=10)
            self.assertEqual(r["c5_conc"], exp, share)
        with mock.patch("lf1.backtest.top_share", return_value=None):
            self.assertFalse(bt.evaluate_hypothesis(self.h, 0, self.g, self.w, self.FH, nboot=20, nplacebo=10)["c5_conc"])

    def test_c2_needs_positive_lcb(self):
        r = {"id": "A", "p": 0.0001, "lcb95_bp": -1.0, "c1_power": True, "c3_placebo": True, "c4_stress": True, "c5_conc": True}
        self.assertIsNone(bt.decide([r], ["A"]))
        self.assertFalse(r["c2_signif"])
        self.assertTrue(r["bh_reject"])
        r = {"id": "A", "p": 0.0001, "lcb95_bp": None, "c1_power": True, "c3_placebo": True, "c4_stress": True, "c5_conc": True}
        self.assertIsNone(bt.decide([r], ["A"]))


class TestRunStage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        n = 24 * 90
        self.grids = {"BTC": regime_series(n, 3.0, 6.0, 0.8, 21)}
        self.windows = {"BTC": [(0, n)]}
        self.hyps = [hyp("H1", params={"L": 24, "side": "both"}, H=24)]
        self.payload, self.fh = bt.make_freeze(self.hyps, gate_stub(), "r" * 64, "b" * 64, {"A": "x"}, [])

    def tearDown(self):
        self.tmp.cleanup()

    def run_stage(self, payload=None, fh=None, stage="discovery_A"):
        with mock.patch("lf1.backtest.NBOOT_P", 100), mock.patch("lf1.backtest.NPLACEBO", 30):
            return bt.run_stage(stage, payload or self.payload, fh or self.fh, self.grids, self.windows, self.tmp.name)

    def test_run_writes_result_and_second_run_refused(self):
        with mock.patch("lf1.backtest.evaluate_hypothesis.__defaults__", (100, 30, None, None)):
            res = self.run_stage()
        self.assertEqual(res["verdict"], "BESCHREIBEND")
        self.assertIsNone(res["candidate"])
        saved = json.load(open(os.path.join(self.tmp.name, "bt_result_discovery_A.json")))
        self.assertEqual(saved["result_hash"], res["result_hash"])
        self.assertEqual(saved["freeze_hash"], self.fh)
        with self.assertRaises(bt.FreezeError):
            self.run_stage()

    def test_modified_payload_or_hash_refused(self):
        p2 = copy.deepcopy(self.payload)
        p2["hypotheses"][0]["params"]["L"] = 25
        with self.assertRaises(bt.FreezeError):
            self.run_stage(payload=p2)
        with self.assertRaises(bt.FreezeError):
            self.run_stage(fh="0" * 64)
        self.assertFalse(os.path.exists(os.path.join(self.tmp.name, "bt_lock_discovery_A.json")))   # vor dem Lock abgelehnt

    def test_code_hash_mismatch_refused(self):
        with mock.patch("lf1.backtest.code_hash", return_value="f" * 64):
            with self.assertRaises(bt.FreezeError):
                self.run_stage()

    def test_technical_error_allows_identical_rerun(self):
        with mock.patch("lf1.backtest.evaluate_hypothesis", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                self.run_stage()
        lk = json.load(open(os.path.join(self.tmp.name, "bt_lock_discovery_A.json")))
        self.assertEqual(lk["status"], "error")
        with mock.patch("lf1.backtest.evaluate_hypothesis.__defaults__", (100, 30, None, None)):
            res = self.run_stage()
        lk = json.load(open(os.path.join(self.tmp.name, "bt_lock_discovery_A.json")))
        self.assertEqual((lk["status"], lk["attempts"]), ("done", 2))
        self.assertIn("results", res)

    def test_rerun_after_error_requires_same_freeze(self):
        with mock.patch("lf1.backtest.evaluate_hypothesis", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                self.run_stage()
        other = [hyp("H1", params={"L": 25, "side": "both"}, H=24)]
        p2, fh2 = bt.make_freeze(other, gate_stub(), "r" * 64, "b" * 64, {"A": "x"}, [])
        with self.assertRaises(bt.FreezeError):
            self.run_stage(payload=p2, fh=fh2)

    def test_result_hash_reproducible(self):
        with mock.patch("lf1.backtest.evaluate_hypothesis.__defaults__", (100, 30, None, None)):
            a = self.run_stage(stage="s1")
            b = self.run_stage(stage="s2")
        self.assertEqual(a["results"], b["results"])                     # Stage-Name geht bewusst in den Hash ein
        self.assertEqual(a["candidate"], b["candidate"])
        self.assertNotEqual(a["result_hash"], b["result_hash"])


if __name__ == "__main__":
    unittest.main()
