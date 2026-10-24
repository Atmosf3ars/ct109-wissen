import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
import synth  # noqa: E402
from lf1 import cli, regime  # noqa: E402


def run(argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = cli.main(argv)
    return rc, buf.getvalue()


class TestFreezeBacktestCli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = self.tmp.name
        self.d = d
        day0 = 16000
        dts, dclose = synth.daily_from_vol([(500, 0.9), (500, 0.3), (400, 0.5)], day0, 11)
        members = {"XBTUSD_1440.csv": synth.to_csv(dts, dclose, dclose, dclose, dclose, np.ones(len(dts)))}
        n_h = 24 * 1400
        for name, seed, sig in (("XBTUSD", 1, 30.0), ("ETHUSD", 2, 40.0), ("SOLUSD", 3, 55.0)):
            ts, o, h, l, c, v = synth.hourly_walk(n_h, sig, seed, day0 * 86400, drop_frac=0.001)
            members["%s_60.csv" % name] = synth.to_csv(ts, o, h, l, c, v)
        self.z = os.path.join(d, "k.zip")
        synth.make_zip(self.z, members)
        self.out = os.path.join(d, "out")
        rc, _ = run(["regime", "--zip", self.z, "--out", self.out, "--cutoff", regime.day_to_iso(day0 + 1399)])
        self.assertEqual(rc, 0)
        self.rpath = os.path.join(self.out, "regime_selection.json")
        self.reg = json.load(open(self.rpath))
        cells = [{"asset": a, "h_hours": h, "class": "W" if h in (24, 72) else "X", "evaluable": True,
                  "mde_net_bp_full_exposure": 50.0, "n_eff": 269} for a in ("BTC", "ETH", "SOL") for h in (1, 4, 24, 72)]
        self.gate = os.path.join(d, "gate_result_A.json")
        json.dump({"window": "A", "regime_hash": self.reg["hash_sha256"], "result_hash": "g" * 64, "cells": cells,
                   "summary": {"lf1_status": "ZULAESSIG"}}, open(self.gate, "w"))
        self.hyps = os.path.join(d, "hyps.json")
        json.dump([{"id": "H1", "rule": "TS_MOM", "params": {"L": 24, "side": "both"}, "asset": "BTC", "H": 24}], open(self.hyps, "w"))
        self.spec = os.path.join(d, "BAU.md")
        open(self.spec, "w").write("bau spec platzhalter")

    def tearDown(self):
        self.tmp.cleanup()

    def freeze(self):
        return run(["freeze", "--zip", self.z, "--regime", self.rpath, "--gate", self.gate, "--hyps", self.hyps,
                    "--bau-spec", self.spec, "--out", self.out])

    def backtest(self, stage="discovery_A"):
        return run(["backtest", "--zip", self.z, "--regime", self.rpath, "--freeze", os.path.join(self.out, "freeze.json"),
                    "--stage", stage, "--out", self.out])

    def test_freeze_then_backtest_once(self):
        rc, txt = self.freeze()
        self.assertEqual(rc, 0, txt)
        self.assertIn("FREEZE_HASH", txt)
        doc = json.load(open(os.path.join(self.out, "freeze.json")))
        self.assertEqual(len(doc["payload"]["data_manifest"]), 1)
        rc, txt = self.freeze()
        self.assertEqual(rc, 4); self.assertIn("einmalig", txt)
        rc, txt = self.backtest()
        self.assertEqual(rc, 0, txt)
        res = json.load(open(os.path.join(self.out, "bt_result_discovery_A.json")))
        self.assertEqual(res["freeze_hash"], doc["freeze_hash"])
        self.assertEqual(res["verdict"], "BESCHREIBEND")
        self.assertIsNone(res["candidate"])
        self.assertGreater(res["results"][0]["n_trades"], 100)
        rc, txt = self.backtest()
        self.assertEqual(rc, 4); self.assertIn("einmalig", txt)

    def test_tampered_freeze_and_wrong_gate_refused(self):
        self.assertEqual(self.freeze()[0], 0)
        p = os.path.join(self.out, "freeze.json")
        doc = json.load(open(p))
        doc["payload"]["hypotheses"][0]["params"]["L"] = 25
        json.dump(doc, open(p, "w"))
        rc, txt = self.backtest()
        self.assertEqual(rc, 4); self.assertIn("veraendert", txt)
        os.remove(p)
        g = json.load(open(self.gate)); g["regime_hash"] = "x"; json.dump(g, open(self.gate, "w"))
        self.assertEqual(self.freeze()[0], 4)

    def test_blocked_cell_refused(self):
        json.dump([{"id": "H1", "rule": "TS_MOM", "params": {"L": 24, "side": "both"}, "asset": "BTC", "H": 4}], open(self.hyps, "w"))
        rc, txt = self.freeze()
        self.assertEqual(rc, 4); self.assertIn("gesperrt", txt)
        self.assertFalse(os.path.exists(os.path.join(self.out, "freeze.json")))

    def test_changed_data_refused(self):
        self.assertEqual(self.freeze()[0], 0)
        import zipfile
        z2 = os.path.join(self.d, "k2.zip")
        with zipfile.ZipFile(self.z) as zi, zipfile.ZipFile(z2, "w") as zo:
            for n in zi.namelist():
                b = zi.read(n)
                zo.writestr(n, b + b"1,1,1,1,1,1,1\n" if n.endswith("XBTUSD_60.csv") else b)
        self.z = z2
        rc, txt = self.backtest()
        self.assertEqual(rc, 4); self.assertIn("Daten", txt)


if __name__ == "__main__":
    unittest.main()
