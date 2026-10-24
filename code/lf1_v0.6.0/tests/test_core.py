import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lf1 import core  # noqa: E402


def rand_series(n=400, seed=1):
    rng = np.random.default_rng(seed)
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, n)))
    o = np.concatenate(([100.0], c[:-1]))
    h = np.maximum(o, c) * 1.002
    l = np.minimum(o, c) * 0.998
    return o, h, l, c


class TestSignals(unittest.TestCase):
    def test_breakout_known(self):
        # konsistente Bars (low <= close <= high): ein Fenster, das die aktuelle Bar enthaelt, koennte nie ausbrechen
        h = np.array([10, 11, 12, 11, 13.5, 12.0])
        l = np.array([9, 10, 11, 10, 12, 7.5])
        c = np.array([9.5, 10.5, 11.5, 10.5, 13.0, 8.0])
        s = core.signals_breakout(h, l, c, L=3, side="both")
        # i=4: close 13 > max(h[1..3]) = 12 -> long ; i=5: 8 < min(l[2..4]) = 10 -> short
        self.assertEqual(list(s), [0, 0, 0, 0, 1, -1])
        s2 = core.signals_breakout(h, l, c, L=3, side="long")
        self.assertEqual(list(s2), [0, 0, 0, 0, 1, 0])

    def test_ts_mom_known(self):
        c = np.array([100, 101, 103, 102, 99.0])
        s = core.signals_ts_mom(c, L=2, side="both")
        self.assertEqual(list(s), [0, 0, 1, 1, -1])
        self.assertEqual(list(core.signals_ts_mom(c, 2, "long")), [0, 0, 1, 1, 0])

    def test_shock_fade_known(self):
        rng = np.random.default_rng(0)
        r = rng.normal(0, 0.001, 60)
        c = 100 * np.exp(np.cumsum(r))
        c[50:] *= 1.03           # Sprung +3 % bei Bar 50
        s = core.signals_shock_fade(c, w=1, k=8.0, N=40)
        self.assertEqual(int(s[50]), -1)      # Gegenrichtung zum Anstieg
        self.assertEqual(int(np.sum(s != 0)), 1)

    def test_nan_gives_no_signal(self):
        o, h, l, c = rand_series()
        c2 = c.copy(); c2[100] = np.nan
        for s in (core.signals_ts_mom(c2, 5), core.signals_shock_fade(c2, 3, 1.0, 30),
                  core.signals_breakout(h, l, c2, 10, "both")):
            self.assertEqual(int(s[100]), 0)

    def test_lookahead_guard_prefix_equals_full(self):
        o, h, l, c = rand_series(500, seed=7)
        full = {
            "bo": core.signals_breakout(h, l, c, 20, "both"),
            "mom": core.signals_ts_mom(c, 24),
            "shock": core.signals_shock_fade(c, 3, 2.0, 48),
        }
        for cut in (60, 101, 250, 499):
            part = {
                "bo": core.signals_breakout(h[:cut], l[:cut], c[:cut], 20, "both"),
                "mom": core.signals_ts_mom(c[:cut], 24),
                "shock": core.signals_shock_fade(c[:cut], 3, 2.0, 48),
            }
            for k in full:
                self.assertTrue(np.array_equal(full[k][:cut], part[k]), "Lookahead in %s bei cut=%d" % (k, cut))

    def test_future_change_does_not_alter_past(self):
        o, h, l, c = rand_series(300, seed=3)
        a = core.signals_shock_fade(c, 2, 1.5, 40)
        c2 = c.copy(); c2[200:] *= 1.3
        b = core.signals_shock_fade(c2, 2, 1.5, 40)
        self.assertTrue(np.array_equal(a[:200], b[:200]))


class TestSimulate(unittest.TestCase):
    def test_entry_exit_prices_and_cost(self):
        o = np.array([100, 101, 102, 104, 105, 107, 106, 108.0])
        sig = np.zeros(8, dtype=np.int8); sig[1] = 1
        cm = core.CostModel(roundtrip_bp=10.0, funding_bp_per_8h=0.0)
        t = core.simulate(o, sig, H=3, cost=cm)
        self.assertEqual(len(t), 1)
        r = t[0]
        self.assertEqual((r["i_dec"], r["i_entry"], r["i_exit"]), (1, 2, 5))
        self.assertAlmostEqual(r["entry"], 102.0); self.assertAlmostEqual(r["exit"], 107.0)
        gross = (107 / 102 - 1) * 1e4
        self.assertAlmostEqual(r["gross_bp"], gross, places=6)
        self.assertAlmostEqual(r["net_bp"], gross - 10.0, places=6)

    def test_short_side_sign(self):
        o = np.array([100, 100, 100, 90, 90.0])
        sig = np.zeros(5, dtype=np.int8); sig[0] = -1
        t = core.simulate(o, sig, H=2, cost=core.CostModel(0.0))
        self.assertGreater(t[0]["gross_bp"], 0)

    def test_no_overlap_and_no_double_count(self):
        n = 60
        o = 100 + np.arange(n, dtype=float)
        sig = np.ones(n, dtype=np.int8)      # Signal in jeder Bar
        t = core.simulate(o, sig, H=5, cost=core.CostModel(0.0))
        self.assertTrue(np.all(t["i_entry"][1:] >= t["i_exit"][:-1]))
        self.assertEqual(len(np.unique(t["i_entry"])), len(t))

    def test_gap_skips_trade(self):
        o = np.array([100, 101, np.nan, 103, 104, 105.0])
        sig = np.zeros(6, dtype=np.int8); sig[1] = 1       # Einstieg Bar 2 = NaN
        self.assertEqual(len(core.simulate(o, sig, 2, core.CostModel(0.0))), 0)
        sig2 = np.zeros(6, dtype=np.int8); sig2[0] = 1      # Einstieg 1, Ausstieg 3: ok
        self.assertEqual(len(core.simulate(o, sig2, 2, core.CostModel(0.0))), 1)

    def test_cost_zero_mutation_changes_result(self):
        o, h, l, c = rand_series(300, seed=11)
        sig = core.signals_ts_mom(c, 6)
        t1 = core.simulate(o, sig, 4, core.CostModel(12.0, 1.0))
        t0 = core.simulate(o, sig, 4, core.CostModel(0.0, 0.0))
        self.assertLess(core.expectancy_bp(t1), core.expectancy_bp(t0))
        self.assertAlmostEqual(core.expectancy_bp(t0) - core.expectancy_bp(t1), 12.0 + 4 / 8.0, places=6)

    def test_latency_shifts_entry(self):
        o = np.arange(100, 120, dtype=float)
        sig = np.zeros(20, dtype=np.int8); sig[2] = 1
        t0 = core.simulate(o, sig, 3, core.CostModel(0.0), latency_bars=0)
        t1 = core.simulate(o, sig, 3, core.CostModel(0.0), latency_bars=1)
        self.assertEqual(int(t1[0]["i_entry"]), int(t0[0]["i_entry"]) + 1)

    def test_funding_uses_hold_hours(self):
        o = np.full(30, 100.0); sig = np.zeros(30, dtype=np.int8); sig[0] = 1
        cm = core.CostModel(roundtrip_bp=0.0, funding_bp_per_8h=1.0)
        t = core.simulate(o, sig, H=16, cost=cm)
        self.assertAlmostEqual(t[0]["cost_bp"], 2.0)

    def test_gate_consistent_cost(self):
        cm = core.gate_consistent_cost(10.1)
        self.assertAlmostEqual(cm.roundtrip_bp, 12.625)
        self.assertAlmostEqual(cm.cost_bp(24), 12.625 + 3.0)

    def test_importverbot_keine_netz_oder_broker_module(self):
        import re
        base = os.path.join(os.path.dirname(__file__), "..", "lf1")
        bad = re.compile(r"^\s*(import|from)\s+(requests|urllib|socket|http|ccxt|ib_insync|ibapi|krakenex|websockets|aiohttp)\b", re.M)
        bad_feed = re.compile(r"^\s*(import|from)\s+(requests|socket|http|ccxt|ib_insync|ibapi|krakenex|websockets|aiohttp)\b", re.M)
        for fn in os.listdir(base):
            if fn.endswith(".py"):
                with open(os.path.join(base, fn), encoding="utf-8") as f:
                    # feed.py ist das einzige Modul mit Netzzugriff (nur urllib, nur GET, zwei URLs: tests/test_runner.py)
                    self.assertIsNone((bad_feed if fn == "feed.py" else bad).search(f.read()), "verbotener Import in %s" % fn)


if __name__ == "__main__":
    unittest.main()
