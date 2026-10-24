import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
import synth  # noqa: E402
from lf1 import backtest as bt  # noqa: E402
from lf1 import cli, core, regime  # noqa: E402
from test_backtest import gate_stub, hyp, mk_grid, regime_series  # noqa: E402

FH = "ab" * 32


class TestEpochHelpers(unittest.TestCase):
    def test_split_index_and_factor(self):
        t0 = 1_577_836_800 - 100 * 3600           # 2020-01-01 minus 100 h
        n = 24 * 800
        sp = bt.split_index(t0, n)
        self.assertEqual(sp, (1_609_459_200 - t0) // 3600)       # 2021-01-01 00:00 UTC
        f = bt.epoch_cost_factor(n, t0)
        self.assertTrue(np.all(f[:sp] == 2.0) and np.all(f[sp:] == 1.0))
        self.assertEqual(bt.split_index(t0, 10), 10)              # Grenze hinter dem Gitter
        self.assertEqual(bt.split_index(1_700_000_000, 10), 0)    # Grenze vor dem Gitter

    def test_adjust_epoch_costs(self):
        cost = bt.cost_for("BTC")
        g = mk_grid(np.random.default_rng(1).normal(0, 0.003, 3000))
        h = hyp(H=24)
        tr = bt.trades_for(h, g, [(0, 3000)], cost)
        cf = np.ones(3000); cf[:1500] = 2.0
        adj = bt.adjust_epoch_costs(tr, cost, 24, cf)
        early = tr["i_entry"] < 1500
        self.assertTrue(np.allclose(tr["net_bp"][early] - adj["net_bp"][early], cost.cost_bp(24)))
        self.assertTrue(np.allclose(tr["net_bp"][~early], adj["net_bp"][~early]))
        self.assertTrue(np.allclose(adj["gross_bp"], tr["gross_bp"]))
        self.assertIs(bt.adjust_epoch_costs(tr, cost, 24, None), tr)

    def test_epoch_quality(self):
        n = 5000
        pres = np.ones(n, dtype=bool)
        q = bt.epoch_quality(pres, [(100, n)], 2000)
        self.assertTrue(q["E1"]["valid"] and q["E2"]["valid"])
        pres2 = pres.copy(); pres2[300:340] = False                 # 39 fehlende Stunden in E1
        q = bt.epoch_quality(pres2, [(100, n)], 2000)
        self.assertFalse(q["E1"]["valid"]); self.assertTrue(q["E2"]["valid"])
        self.assertEqual(q["E1"]["max_gap_h"], 40)
        pres3 = pres.copy(); pres3[2100:2500:2] = False              # 200 von ~3000 Bars = 6.7 % fehlend in E2
        q = bt.epoch_quality(pres3, [(100, n)], 2000)
        self.assertFalse(q["E2"]["valid"])
        self.assertGreater(q["E2"]["missing_pct"], 5.0)
        q = bt.epoch_quality(np.zeros(n, dtype=bool), [(100, n)], 2000)
        self.assertFalse(q["E1"]["valid"]); self.assertFalse(q["E2"]["valid"])
        q = bt.epoch_quality(pres, [(100, 1500)], 2000)              # E2 liegt hinter dem Fenster
        self.assertFalse(q["E2"]["valid"]); self.assertTrue(q["E1"]["valid"])

    def test_placebo_uses_epoch_costs(self):
        g = mk_grid(np.random.default_rng(3).normal(0, 0.003, 4000))
        h = hyp(H=24); cost = bt.cost_for("BTC")
        tr = bt.trades_for(h, g, [(0, 4000)], cost)
        cf = np.full(4000, 3.0)
        a = bt.placebo_means(h, g, [(0, 4000)], tr, cost, 0, 100, np.random.default_rng(2))
        b = bt.placebo_means(h, g, [(0, 4000)], tr, cost, 0, 100, np.random.default_rng(2), cf)
        self.assertTrue(np.allclose(a - b, 2.0 * cost.cost_bp(24)))


class TestEvaluateEpochs(unittest.TestCase):
    def two_halves(self, edge_first, edge_second, n=24 * 800, seed=5):
        rng = np.random.default_rng(seed)
        m = n // 2
        d = np.empty(n // 24 + 1); d[0] = 1.0
        for k in range(1, len(d)):
            d[k] = d[k - 1] if rng.random() < 0.8 else -d[k - 1]
        mu = np.where(np.arange(n) < m, edge_first, edge_second)
        r = (np.repeat(d, 24)[:n] * mu + rng.normal(0, 6.0, n)) * 1e-4
        return mk_grid(r), m

    def test_c7a_looks_only_at_e2(self):
        h = hyp("H1", params={"L": 24, "side": "both"}, H=24)
        g, m = self.two_halves(8.0, 0.0)
        cf = np.ones(len(g["o"])); cf[:m] = 2.0
        r = bt.evaluate_hypothesis(h, 0, g, [(336, len(g["o"]))], FH, nboot=50, nplacebo=20, cost_factor=cf, split_idx=m)
        self.assertGreater(r["net_mean_bp"], 0)                       # Edge in E1 traegt das Gesamtmittel
        self.assertFalse(r["c7a_epoch"])                              # E2 ohne Edge: nach Kosten negativ
        self.assertLess(r["e2_net_mean_bp"], 0)
        self.assertLess(r["e2_n"], r["n_trades"])
        g2, m2 = self.two_halves(0.0, 8.0)
        r2 = bt.evaluate_hypothesis(h, 0, g2, [(336, len(g2["o"]))], FH, nboot=50, nplacebo=20, cost_factor=cf, split_idx=m2)
        self.assertTrue(r2["c7a_epoch"]); self.assertGreater(r2["e2_net_mean_bp"], 10)

    def test_stress_values_include_epoch_costs(self):
        h = hyp("H1", params={"L": 24, "side": "both"}, H=24)
        g, m = self.two_halves(3.0, 3.0)
        n = len(g["o"])
        cf = np.ones(n); cf[:m] = 3.0
        w = [(336, n)]
        r = bt.evaluate_hypothesis(h, 0, g, w, FH, nboot=50, nplacebo=20, cost_factor=cf, split_idx=m)
        cost = bt.cost_for("BTC")
        base = bt.adjust_epoch_costs(bt.trades_for(h, g, w, cost, 0), cost, 24, cf)
        self.assertAlmostEqual(r["net_mean_bp"], float(base["net_bp"].mean()), places=9)
        # Kosten-Stress: gleiche Trades, Netto sinkt um 0.5 * Kosten * Epochenfaktor des Einstiegs
        exp = float(base["net_bp"].mean()) - 0.5 * cost.cost_bp(24) * float(cf[base["i_entry"].astype(int)].mean())
        self.assertAlmostEqual(r["stress_cost_net_bp"], exp, places=6)
        lat = bt.adjust_epoch_costs(bt.trades_for(h, g, w, cost, 1), cost, 24, cf)
        self.assertAlmostEqual(r["stress_latency_net_bp"], float(lat["net_bp"].mean()), places=9)


class TestDecideConfirm(unittest.TestCase):
    def mk(self, i, **kw):
        r = {"id": i, "p": 0.0001, "lcb95_bp": 5.0, "c1_power": True, "c3_placebo": True, "c4_stress": True,
             "c5_conc": True, "c7a_epoch": True}
        r.update(kw)
        return r

    def test_categories(self):
        rs = [self.mk("A"), self.mk("B", c1_power=False), self.mk("C", c3_placebo=False), self.mk("D", c7a_epoch=False),
              self.mk("E"), self.mk("F", p=0.9)]
        conf = bt.decide_confirm(rs, [r["id"] for r in rs], {"A": 3.0, "B": 3.0, "C": 3.0, "D": 3.0, "E": -1.0, "F": 3.0})
        cats = {r["id"]: r["category"] for r in rs}
        self.assertEqual(cats, {"A": "BESTAETIGT", "B": "POSITIV-UNTERPOWERT", "C": "NULLBEFUND", "D": "NULLBEFUND",
                                "E": "NULLBEFUND", "F": "NULLBEFUND"})
        self.assertEqual(conf, ["A"])

    def test_missing_a_result_is_not_positive(self):
        rs = [self.mk("A")]
        bt.decide_confirm(rs, ["A"], {"A": None})
        self.assertEqual(rs[0]["category"], "NULLBEFUND")

    def test_both_may_pass_no_single_candidate_rule(self):
        rs = [self.mk("A"), self.mk("B", lcb95_bp=9.0)]
        self.assertEqual(sorted(bt.decide_confirm(rs, ["A", "B"], {"A": 1, "B": 1})), ["A", "B"])

    def test_bh_over_list(self):
        rs = [self.mk("A", p=0.04), self.mk("B", p=0.9)]
        bt.decide_confirm(rs, ["A", "B"], {"A": 1, "B": 1})
        self.assertEqual(rs[0]["category"], "NULLBEFUND")        # m = 2: 0.04 > 0.025


class TestRunStageConfirm(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        n = 24 * 900
        self.n = n
        self.grid = regime_series(n, 3.0, 6.0, 0.8, 21)
        self.hyps = [hyp("H1", params={"L": 24, "side": "both"}, H=24)]
        self.payload, self.fh = bt.make_freeze(self.hyps, gate_stub(), "r" * 64, "b" * 64, {"A": "x"}, [])
        self.t0 = 1_546_300_800                    # 2019-01-01
        self.split = bt.split_index(self.t0, n)
        self.extras = {"cost_factor": {"BTC": bt.epoch_cost_factor(n, self.t0)}, "split_idx": {"BTC": self.split},
                       "epoch_quality": {"BTC": {"E1": {"valid": True}, "E2": {"valid": True}}}}

    def tearDown(self):
        self.tmp.cleanup()

    def run_stage(self, stage, extras=None):
        with mock.patch("lf1.backtest.NBOOT_P", 100), mock.patch("lf1.backtest.NPLACEBO", 30), \
                mock.patch("lf1.backtest.evaluate_hypothesis.__defaults__", (100, 30, None, None)):
            return bt.run_stage(stage, self.payload, self.fh, {"BTC": self.grid}, {"BTC": [(336, self.n)]}, self.tmp.name, extras=extras)

    def test_confirm_requires_stage_d_and_extras(self):
        with self.assertRaises(bt.FreezeError):
            self.run_stage("confirm")                                    # ohne extras
        with self.assertRaises(bt.FreezeError):
            self.run_stage("confirm", self.extras)                       # ohne Stufe D
        self.assertFalse(os.path.exists(os.path.join(self.tmp.name, "bt_lock_confirm.json")))   # Sperre nicht verbraucht

    def test_confirm_after_d_gives_category_and_epoch_fields(self):
        d = self.run_stage("discovery_A")
        self.assertEqual(d["verdict"], "BESCHREIBEND")
        res = self.run_stage("confirm", self.extras)
        r = res["results"][0]
        self.assertIn(r["category"], bt.CATEGORIES)
        self.assertEqual(res["stage_d_result_hash"], d["result_hash"])
        self.assertIn("e2_net_mean_bp", r); self.assertIn("c7a_epoch", r); self.assertIn("c7b_regime_a", r)
        self.assertEqual(r["a_net_mean_bp"], d["results"][0]["net_mean_bp"])
        self.assertGreater(r["net_mean_bp"], 5.0)                        # injizierter Edge, E1 mit doppelten Kosten
        with self.assertRaises(bt.FreezeError):
            self.run_stage("confirm", self.extras)                       # einmalig

    def test_tampered_stage_d_refused(self):
        self.run_stage("discovery_A")
        p = os.path.join(self.tmp.name, "bt_result_discovery_A.json")
        d = json.load(open(p)); d["results"][0]["net_mean_bp"] = 999.0; json.dump(d, open(p, "w"))
        with self.assertRaises(bt.FreezeError):
            self.run_stage("confirm", self.extras)

    def test_epoch_cost_changes_result_in_e1(self):
        self.run_stage("discovery_A")
        res = self.run_stage("confirm", self.extras)
        net_with = res["results"][0]["net_mean_bp"]
        cost = bt.cost_for("BTC")
        flat = dict(self.extras, cost_factor={"BTC": np.ones(self.n)})
        os.remove(os.path.join(self.tmp.name, "bt_lock_confirm.json"))
        res2 = self.run_stage("confirm", flat)
        self.assertGreater(res2["results"][0]["net_mean_bp"], net_with)
        self.assertLess(res2["results"][0]["net_mean_bp"] - net_with, cost.cost_bp(24) + 1e-9)


class TestCliConfirm(unittest.TestCase):
    def setup_case(self, d, gap=None):
        day0 = 17000
        dts, dclose = synth.daily_from_vol([(1700, 0.9), (900, 0.4)], day0, 11)
        members = {"XBTUSD_1440.csv": synth.to_csv(dts, dclose, dclose, dclose, dclose, np.ones(len(dts)))}
        n_h = 24 * 2600
        ts, o, h, l, c, v = synth.hourly_walk(n_h, 40.0, 1, day0 * 86400, drop_frac=0.0005, drift_bp=0.0)
        if gap is not None:                                    # (Tag ab Start, Stunden) fehlen
            keep = ~((ts >= (day0 + gap[0]) * 86400) & (ts < (day0 + gap[0]) * 86400 + gap[1] * 3600))
            ts, o, h, l, c, v = ts[keep], o[keep], h[keep], l[keep], c[keep], v[keep]
        members["XBTUSD_60.csv"] = synth.to_csv(ts, o, h, l, c, v)
        z = os.path.join(d, "k.zip"); synth.make_zip(z, members)
        out = os.path.join(d, "out")

        def run(argv):
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = cli.main(argv)
            return rc, buf.getvalue()

        rc, _ = run(["regime", "--zip", z, "--out", out, "--cutoff", regime.day_to_iso(day0 + 2599)]); self.assertEqual(rc, 0)
        rp = os.path.join(out, "regime_selection.json"); reg = json.load(open(rp))
        cells = [{"asset": a, "h_hours": hh, "class": "W", "evaluable": True, "mde_net_bp_full_exposure": 50.0, "n_eff": 200}
                 for a in ("BTC", "ETH", "SOL") for hh in (24, 72)]
        gp = os.path.join(d, "gate.json")
        json.dump({"window": "A", "regime_hash": reg["hash_sha256"], "result_hash": "g" * 64, "cells": cells,
                   "summary": {"lf1_status": "ZULAESSIG"}}, open(gp, "w"))
        hp = os.path.join(d, "h.json")
        json.dump([{"id": "H1", "rule": "TS_MOM", "params": {"L": 24, "side": "both"}, "asset": "BTC", "H": 24}], open(hp, "w"))
        sp = os.path.join(d, "spec.md"); open(sp, "w").write("x")
        rc, txt = run(["freeze", "--zip", z, "--regime", rp, "--gate", gp, "--hyps", hp, "--bau-spec", sp, "--out", out]); self.assertEqual(rc, 0, txt)
        fp = os.path.join(out, "freeze.json")
        base = ["--zip", z, "--regime", rp, "--freeze", fp, "--out", out]
        return run, base, out, reg

    def test_confirm_end_to_end_synthetic(self):
        with tempfile.TemporaryDirectory() as d:
            run, base, out, reg = self.setup_case(d)
            rc, txt = run(["backtest"] + base + ["--stage", "confirm"])
            self.assertEqual(rc, 4); self.assertIn("Stufe D", txt)
            rc, txt = run(["backtest"] + base + ["--stage", "discovery_A"]); self.assertEqual(rc, 0, txt)
            rc, txt = run(["backtest"] + base + ["--stage", "confirm"]); self.assertEqual(rc, 0, txt)
            res = json.load(open(os.path.join(out, "bt_result_confirm.json")))
            r = res["results"][0]
            self.assertIn(r["category"], bt.CATEGORIES)
            self.assertTrue(res["epoch_quality"]["BTC"]["E1"]["valid"] and res["epoch_quality"]["BTC"]["E2"]["valid"])
            self.assertGreater(r["n_trades"], 1000)
            self.assertTrue(0 < r["e2_n"] < r["n_trades"])
            a0, _a1 = regime.window_bounds_utc(reg, "A")
            self.assertEqual(res["window_e"]["BTC"]["end_ts_exclusive"], a0)
            rc, txt = run(["backtest"] + base + ["--stage", "confirm"])
            self.assertEqual(rc, 4); self.assertIn("einmalig", txt)

    def test_epoch_q_prints_only_counts(self):
        with tempfile.TemporaryDirectory() as d:
            run, base, out, reg = self.setup_case(d, gap=(300, 40))
            rc, txt = run(["epoch-q", "--zip", base[1], "--regime", base[3], "--out", out]); self.assertEqual(rc, 0, txt)
            res = json.load(open(os.path.join(out, "q_epochs.json")))
            q = res["assets"]["BTC"]["quality"]
            self.assertFalse(q["E1"]["valid"]); self.assertTrue(q["E2"]["valid"])
            self.assertEqual(q["E1"]["max_gap_h"], 40)
            a0, _ = regime.window_bounds_utc(reg, "A")
            self.assertEqual(res["e_end_ts_exclusive"], a0)
            blob = json.dumps(res).lower()
            for bad in ("net_", "gross", "return", "signal", "trade"):
                self.assertNotIn(bad, blob)                       # keine Signal-/Renditegroessen im Ergebnis
            self.assertFalse(os.path.exists(os.path.join(out, "bt_lock_confirm.json")))

    def test_invalid_e1_is_excluded_and_reported(self):
        with tempfile.TemporaryDirectory() as d:
            run, base, out, _reg = self.setup_case(d, gap=(300, 40))        # 40 h Luecke im Jahr 2017
            self.assertEqual(run(["backtest"] + base + ["--stage", "discovery_A"])[0], 0)
            rc, txt = run(["backtest"] + base + ["--stage", "confirm"]); self.assertEqual(rc, 0, txt)
            res = json.load(open(os.path.join(out, "bt_result_confirm.json")))
            self.assertFalse(res["epoch_quality"]["BTC"]["E1"]["valid"])
            r = res["results"][0]
            self.assertEqual(r["e2_n"], r["n_trades"])                       # nur E2-Trades

    def test_invalid_e2_refused_without_consuming_lock(self):
        with tempfile.TemporaryDirectory() as d:
            run, base, out, _reg = self.setup_case(d, gap=(1650, 40))       # Luecke im Jahr 2021
            self.assertEqual(run(["backtest"] + base + ["--stage", "discovery_A"])[0], 0)
            rc, txt = run(["backtest"] + base + ["--stage", "confirm"])
            self.assertEqual(rc, 4); self.assertIn("E2", txt)
            self.assertFalse(os.path.exists(os.path.join(out, "bt_lock_confirm.json")))


if __name__ == "__main__":
    unittest.main()
