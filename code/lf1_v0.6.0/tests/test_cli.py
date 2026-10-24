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
from lf1 import cli, regime, util  # noqa: E402


class TestEndToEnd(unittest.TestCase):
    """Ablauf wie auf Andis PC: file-q -> regime -> window-q -> gate, mit synthetischen Daten."""

    def test_pipeline(self):
        with tempfile.TemporaryDirectory() as d:
            day0 = 16000
            dts, dclose = synth.daily_from_vol([(500, 0.9), (500, 0.3), (400, 0.5)], day0, 11)
            members = {"XBTUSD_1440.csv": synth.to_csv(dts, dclose, dclose, dclose, dclose, np.ones(len(dts)))}
            t0 = day0 * 86400
            n_h = 24 * 1400
            for name, seed, sig in (("XBTUSD", 1, 30.0), ("ETHUSD", 2, 40.0), ("SOLUSD", 3, 55.0)):
                ts, o, h, l, c, v = synth.hourly_walk(n_h, sig, seed, t0, drop_frac=0.001)
                members["%s_60.csv" % name] = synth.to_csv(ts, o, h, l, c, v)
            z = os.path.join(d, "Kraken_OHLCVT_Full.zip")
            synth.make_zip(z, members)
            out = os.path.join(d, "out")
            cutoff = regime.day_to_iso(day0 + 1399)
            spec = os.path.join(d, "GATE_SPEC_v1.md")
            open(spec, "w").write("platzhalter")
            ok = {"ok": True, "expected": util.SPEC_SHA256, "sha256_raw": "r", "sha256_lf_normalized": "l", "matched": "raw"}

            def run(argv):
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    rc = cli.main(argv)
                return rc, buf.getvalue()

            rc, txt = run(["selfcheck"]); self.assertEqual(rc, 0)
            rc, txt = run(["file-q", "--zip", z, "--out", out]); self.assertEqual(rc, 0)
            q = json.load(open(os.path.join(out, "q_files.json")))
            self.assertEqual(len(q["files"]), 4)
            rc, txt = run(["regime", "--zip", z, "--out", out, "--cutoff", cutoff]); self.assertEqual(rc, 0)
            self.assertIn("REGIME_HASH", txt)
            reg = json.load(open(os.path.join(out, "regime_selection.json")))
            self.assertEqual(reg["status"], "OK")
            rpath = os.path.join(out, "regime_selection.json")
            rc, txt = run(["window-q", "--zip", z, "--regime", rpath, "--out", out]); self.assertEqual(rc, 0)
            wq = json.load(open(os.path.join(out, "q_window_A.json")))
            self.assertTrue(wq["all_pass"])
            with mock.patch("lf1.gate.check_spec", return_value=ok):
                rc, txt = run(["gate", "--zip", z, "--regime", rpath, "--spec", spec, "--out", out]); self.assertEqual(rc, 0)
                res = json.load(open(os.path.join(out, "gate_result_A.json")))
                self.assertEqual(len(res["cells"]), 12)
                rc, txt = run(["gate", "--zip", z, "--regime", rpath, "--spec", spec, "--out", out])
                self.assertEqual(rc, 4); self.assertIn("einmalig", txt)

    @unittest.skipUnless(os.path.isdir("/proc/self/fd"), "nur Linux")
    def test_no_open_zip_handle_while_traceback_alive(self):
        # Windows-Fall: Der Traceback haelt den Frame, die ZIP-Datei darf trotzdem nicht offen bleiben
        import argparse
        with tempfile.TemporaryDirectory() as d:
            z = os.path.join(d, "k.zip")
            synth.make_zip(z, {"XBTUSD_1440.csv": b"1,2,3\n"})     # unlesbar -> DataError
            err = None
            try:
                cli.cmd_file_q(argparse.Namespace(zip=z, out=os.path.join(d, "o")))
            except Exception as e:      # bewusst gehalten: err.__traceback__ haelt die Frames
                err = e
            self.assertIsNotNone(err)
            real = os.path.realpath(z)
            held = [p for p in os.listdir("/proc/self/fd")
                    if os.path.realpath("/proc/self/fd/" + p) == real]
            self.assertEqual(held, [], "ZIP-Handle nach Fehler noch offen")

    def test_gate_refuses_real_spec_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            spec = os.path.join(d, "s.md"); open(spec, "w").write("anders")
            with contextlib.redirect_stdout(io.StringIO()):     # Negativtest: Ausgabe nicht auf die Konsole
                rc = cli.main(["selfcheck", "--spec", spec])
            self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
