import copy
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
from lf1 import gate, util  # noqa: E402
from lf1.data import Source, to_grid  # noqa: E402

T0 = 1_600_000_000 - (1_600_000_000 % 86400)  # Tagesgrenze


class TestCell(unittest.TestCase):
    def grid(self, n=6480, sigma=30.0, seed=5, drop=0.0):
        ts, o, h, l, c, v = synth.hourly_walk(n, sigma, seed, T0, drop_frac=drop)
        class B: pass
        b = B(); b.ts, b.o, b.h, b.l, b.c, b.v = ts, o, h, l, c, v
        return to_grid(b, T0, T0 + 3600 * n)

    def test_random_walk_matches_theory(self):
        o, _h, _l, _c, _v, present = self.grid()
        for h in (1, 4, 24):
            cell = gate.evaluate_cell("BTC", h, o, present, True)
            expect = np.sqrt(2 / np.pi) * 30.0 * np.sqrt(h)
            # relativer Standardfehler von E|r| bei n/h unabhaengigen Fenstern: sqrt(pi/2 - 1)/sqrt(n/h)
            se_rel = np.sqrt(np.pi / 2 - 1) / np.sqrt(6480 / h)
            self.assertLess(abs(cell["mean_abs_r_bp"] - expect) / expect, 3 * se_rel, "h=%d" % h)
            self.assertLessEqual(cell["lcb95_bp"], cell["mean_abs_r_bp"])
            self.assertTrue(cell["evaluable"])

    def test_direction_blind_mirror_invariance(self):
        o, *_rest, present = self.grid(n=3000, seed=9)
        o_m = o[0] ** 2 / o     # spiegelt alle Log-Renditen: r -> -r
        for h in (1, 4, 24):
            a = gate.evaluate_cell("ETH", h, o, present, True)
            b = gate.evaluate_cell("ETH", h, o_m, present, True)
            for k in ("mean_abs_r_bp", "lcb95_bp", "rho_min_plus", "class", "n_eff", "n_windows"):
                if isinstance(a[k], float):
                    self.assertAlmostEqual(a[k], b[k], places=3, msg=k)
                else:
                    self.assertEqual(a[k], b[k], k)

    def test_output_has_only_scalars(self):
        o, *_r, present = self.grid(n=1500)
        cell = gate.evaluate_cell("SOL", 4, o, present, True)
        for k, v in cell.items():
            self.assertTrue(v is None or isinstance(v, (int, float, str, bool)), k)

    def test_empty_and_sparse_regimes_do_not_raise(self):
        o = np.full(500, np.nan)
        c = gate.evaluate_cell("BTC", 24, o, ~np.isnan(o), True)
        self.assertEqual(c["n_windows"], 0); self.assertEqual(c["class"], "X"); self.assertFalse(c["evaluable"])
        o2, *_r, p2 = self.grid(n=1000)
        c2 = gate.evaluate_cell("BTC", 72, o2, p2, True)     # n_eff = 13 < 60
        self.assertEqual(c2["class"], "X"); self.assertIn("n_eff", c2["reason"])

    def test_missing_endpoints_are_dropped(self):
        o = np.array([100, np.nan, 102, 103, np.nan, 105, 106.0])
        r = gate.window_returns(o, 1)
        self.assertEqual(len(r), 2)         # nur (2,3) und (5,6); alle Paare mit NaN-Endpunkt entfallen
        r2 = gate.window_returns(o, 2)
        self.assertEqual(len(r2), 2)        # (0,2) und (3,5); (1,3), (2,4), (4,6) haben NaN-Endpunkt

    def test_q_fail_blocks_cell(self):
        o, *_r, present = self.grid(n=3000)
        self.assertEqual(gate.evaluate_cell("BTC", 4, o, present, False)["class"], "X")

    def test_cost_mutation_changes_class(self):
        o, *_r, present = self.grid(n=6480, sigma=30.0)
        base = gate.evaluate_cell("BTC", 4, o, present, True)
        free = gate.evaluate_cell("BTC", 4, o, present, True, cost_override=0.0)
        self.assertEqual(free["class"], "P")
        self.assertGreater(base["rho_min_plus"], free["rho_min_plus"])

    def test_class_boundaries(self):
        self.assertEqual(gate.classify(0.05), "P"); self.assertEqual(gate.classify(0.0501), "W")
        self.assertEqual(gate.classify(0.10), "W"); self.assertEqual(gate.classify(0.1001), "X")
        self.assertEqual(gate.classify(None), "X")

    def test_deterministic(self):
        o, *_r, present = self.grid(n=3000, seed=2)
        a = gate.evaluate_cell("BTC", 24, o, present, True)
        b = gate.evaluate_cell("BTC", 24, o, present, True)
        self.assertEqual(a, b)

    def test_cost_formula_matches_spec(self):
        self.assertAlmostEqual(gate.c_gate("BTC", 24), 1.25 * 10.1 + 3.0)
        self.assertAlmostEqual(gate.c_gate("SOL", 1), 1.25 * 16.0 + 1.0 / 8)


class TestRunAndLock(unittest.TestCase):
    def setUp(self):
        self._sources = []
        self.tmp = tempfile.TemporaryDirectory()
        n = 24 * 60
        members = {}
        for name, seed, sig in (("XBTUSD", 1, 35.0), ("ETHUSD", 2, 45.0), ("SOLUSD", 3, 60.0)):
            ts, o, h, l, c, v = synth.hourly_walk(n, sig, seed, T0, drop_frac=0.002)
            members["%s_60.csv" % name] = synth.to_csv(ts, o, h, l, c, v)
        self.zip = os.path.join(self.tmp.name, "k.zip")
        synth.make_zip(self.zip, members)
        d0 = T0 // 86400
        self.regime = {
            "status": "OK", "hash_sha256": "abc",
            "A": {"start": synth_day(d0), "end": synth_day(d0 + 59)},
            "B": {"start": synth_day(d0), "end": synth_day(d0 + 59)},
        }
        self.spec = os.path.join(self.tmp.name, "spec.md")
        open(self.spec, "w").write("x")
        self.ok = {"ok": True, "expected": util.SPEC_SHA256, "sha256_raw": "r", "sha256_lf_normalized": "l", "matched": "raw"}

    def S(self):
        s = Source(self.zip)
        self._sources.append(s)
        return s

    def tearDown(self):
        for s in self._sources:       # Windows: offene ZIP-Handles blockieren das Loeschen
            s.close()
        self.tmp.cleanup()

    def test_full_run_then_second_run_refused(self):
        out = os.path.join(self.tmp.name, "out")
        with mock.patch("lf1.gate.check_spec", return_value=self.ok):
            res = gate.run_gate(self.S(), self.regime, "A", self.spec, out)
            self.assertEqual(len(res["cells"]), 12)
            self.assertEqual(res["summary"]["lf1_status"] in ("ZULAESSIG", "NULLBEFUND"), True)
            with self.assertRaises(gate.GateError):
                gate.run_gate(self.S(), self.regime, "A", self.spec, out)
        saved = json.load(open(os.path.join(out, "gate_result_A.json")))
        self.assertEqual(saved["result_hash"], res["result_hash"])
        blob = json.dumps(saved)
        self.assertLess(len(blob), 40000)            # nur Aggregate

    def test_result_hash_reproducible_across_dirs(self):
        with mock.patch("lf1.gate.check_spec", return_value=self.ok):
            a = gate.run_gate(self.S(), self.regime, "A", self.spec, os.path.join(self.tmp.name, "o1"))
            b = gate.run_gate(self.S(), self.regime, "A", self.spec, os.path.join(self.tmp.name, "o2"))
        self.assertEqual(a["result_hash"], b["result_hash"])

    def test_technical_error_allows_identical_rerun_only(self):
        out = os.path.join(self.tmp.name, "out")
        with mock.patch("lf1.gate.check_spec", return_value=self.ok):
            with mock.patch("lf1.gate.load_bars", side_effect=RuntimeError("boom")):
                with self.assertRaises(RuntimeError):
                    gate.run_gate(self.S(), self.regime, "A", self.spec, out)
            lk = json.load(open(os.path.join(out, "gate_lock_A.json")))
            self.assertEqual(lk["status"], "error")
            res = gate.run_gate(self.S(), self.regime, "A", self.spec, out)     # identischer Code/Regime
            self.assertIn("cells", res)
            lk = json.load(open(os.path.join(out, "gate_lock_A.json")))
            self.assertEqual((lk["status"], lk["attempts"]), ("done", 2))

    def test_changed_regime_blocks_rerun_after_error(self):
        out = os.path.join(self.tmp.name, "out")
        with mock.patch("lf1.gate.check_spec", return_value=self.ok):
            with mock.patch("lf1.gate.load_bars", side_effect=RuntimeError("boom")):
                with self.assertRaises(RuntimeError):
                    gate.run_gate(self.S(), self.regime, "A", self.spec, out)
            other = copy.deepcopy(self.regime); other["hash_sha256"] = "zzz"
            with self.assertRaises(gate.GateError):
                gate.run_gate(self.S(), other, "A", self.spec, out)

    def test_window_b_requires_freeze_hash(self):
        with mock.patch("lf1.gate.check_spec", return_value=self.ok):
            with self.assertRaises(gate.GateError):
                gate.run_gate(self.S(), self.regime, "B", self.spec, os.path.join(self.tmp.name, "o"))

    def test_wrong_spec_hash_refused(self):
        with self.assertRaises(gate.GateError):
            gate.run_gate(self.S(), self.regime, "A", self.spec, os.path.join(self.tmp.name, "o"))

    def test_blocked_regime_refused(self):
        with mock.patch("lf1.gate.check_spec", return_value=self.ok):
            with self.assertRaises(gate.GateError):
                gate.run_gate(self.S(), {"status": "BLOCKED"}, "A", self.spec, os.path.join(self.tmp.name, "o"))


class TestSpecHash(unittest.TestCase):
    def test_crlf_variant_accepted_and_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            lf = b"# spec\nzeile\n"
            p = os.path.join(d, "s.md")
            with mock.patch("lf1.util.SPEC_SHA256", util.sha256_bytes(lf)):
                open(p, "wb").write(lf)
                self.assertEqual(util.check_spec(p)["matched"], "raw")
                open(p, "wb").write(lf.replace(b"\n", b"\r\n"))
                self.assertEqual(util.check_spec(p)["matched"], "lf_normalized")
                open(p, "wb").write(lf + b"x")
                self.assertFalse(util.check_spec(p)["ok"])


def synth_day(day):
    import datetime as dt
    return (dt.date(1970, 1, 1) + dt.timedelta(days=int(day))).isoformat()


if __name__ == "__main__":
    unittest.main()
