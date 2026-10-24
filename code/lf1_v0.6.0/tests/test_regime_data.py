import math
import os
import statistics
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
import synth  # noqa: E402
from lf1 import data, quality, regime  # noqa: E402

DAY0 = 16000


def brute_rv30(close):
    n = len(close)
    lr = [float("nan")] + [math.log(close[i] / close[i - 1]) for i in range(1, n)]
    rv = [float("nan")] * n
    for t in range(29, n):
        seg = lr[t - 29:t + 1]
        if any(math.isnan(x) for x in seg):
            continue
        rv[t] = math.sqrt(365) * statistics.stdev(seg)
    return rv


class TestRegime(unittest.TestCase):
    def test_rv30_matches_bruteforce(self):
        ts, c = synth.daily_from_vol([(200, 0.6)], DAY0, 1)
        first, rv = regime.daily_rv30(ts, c, DAY0 + 10_000)
        ref = brute_rv30(list(c))
        for a, b in zip(rv, ref):
            if math.isnan(b):
                self.assertTrue(math.isnan(a))
            else:
                self.assertAlmostEqual(a, b, places=9)

    def test_selection_matches_bruteforce_and_rules(self):
        ts, c = synth.daily_from_vol([(450, 0.9), (400, 0.3), (250, 0.5)], DAY0, 4)
        last = regime.day_to_iso(DAY0 + len(c) - 1)
        res = regime.select_regimes(ts, c, cutoff=last)
        self.assertEqual(res["status"], "OK")
        W = res["W"]
        rv = brute_rv30(list(c))
        scores = {}
        for s in range(0, len(c) - W + 1):
            seg = rv[s:s + W]
            if any(math.isnan(x) for x in seg):
                continue
            scores[s] = statistics.median(seg)
        lv = [s for s, m in scores.items() if m <= 0.45]
        a_start = max(lv, key=lambda s: s + W - 1)
        self.assertEqual(res["A"]["start"], regime.day_to_iso(DAY0 + a_start))
        a_end = a_start + W - 1
        hv = [s for s, m in scores.items() if m >= 0.55 and max(s - a_end - 1, a_start - (s + W - 1) - 1) >= 14]
        b_start = max(hv, key=lambda s: s + W - 1)
        self.assertEqual(res["B"]["start"], regime.day_to_iso(DAY0 + b_start))
        self.assertLessEqual(res["A"]["median_rv30"], 0.45)
        self.assertGreaterEqual(res["B"]["median_rv30"], 0.55)

    def test_fallback_w180(self):
        ts, c = synth.daily_from_vol([(215, 1.0), (330, 0.25)], DAY0, 8)    # HV nur ~215 Tage
        last = regime.day_to_iso(DAY0 + len(c) - 1)
        res = regime.select_regimes(ts, c, cutoff=last)
        self.assertEqual((res["status"], res["W"]), ("OK", 180))

    def test_blocked_when_no_pair(self):
        ts, c = synth.daily_from_vol([(700, 0.5)], DAY0, 9)      # weder LV noch HV
        last = regime.day_to_iso(DAY0 + len(c) - 1)
        res = regime.select_regimes(ts, c, cutoff=last)
        self.assertEqual(res["status"], "BLOCKED")

    def test_cutoff_excludes_later_days(self):
        ts, c = synth.daily_from_vol([(450, 0.9), (400, 0.3), (250, 0.5)], DAY0, 4)
        cut = regime.day_to_iso(DAY0 + 899)
        res = regime.select_regimes(ts, c, cutoff=cut)
        self.assertLessEqual(res["A"]["end"], cut)
        self.assertLessEqual(res["B"]["end"], cut)

    def test_hash_is_deterministic_and_input_sensitive(self):
        ts, c = synth.daily_from_vol([(450, 0.9), (400, 0.3), (250, 0.5)], DAY0, 4)
        last = regime.day_to_iso(DAY0 + len(c) - 1)
        a = regime.select_regimes(ts, c, cutoff=last)
        b = regime.select_regimes(ts, c, cutoff=last)
        self.assertEqual(a["hash_sha256"], b["hash_sha256"])
        c2 = synth.daily_from_vol([(450, 0.9), (400, 0.3), (250, 0.5)], DAY0, 5)[1]
        self.assertNotEqual(a["hash_sha256"], regime.select_regimes(ts, c2, cutoff=last)["hash_sha256"])

    def test_gap_day_makes_window_invalid(self):
        ts, c = synth.daily_from_vol([(700, 0.3)], DAY0, 3)
        keep = np.ones(len(ts), bool); keep[350] = False
        first, rv = regime.daily_rv30(ts[keep], c[keep], DAY0 + 10_000)
        self.assertTrue(np.isnan(rv[350]))
        self.assertTrue(np.isnan(rv[351]))        # Rendite ueber die Luecke fehlt (NaN)
        self.assertFalse(np.isnan(rv[400]))


class TestDataQuality(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.doCleanups()          # Handles zuerst schliessen (Windows)
        self.tmp.cleanup()

    def test_loader_zip_alias_and_no_fill(self):
        t0 = 1_600_041_600
        ts, o, h, l, c, v = synth.hourly_walk(500, 20.0, 1, t0, drop_frac=0.1)
        p = os.path.join(self.tmp.name, "k.zip")
        synth.make_zip(p, {"XBTUSD_60.csv": synth.to_csv(ts, o, h, l, c, v)})
        src = data.Source(p)
        self.addCleanup(src.close)
        b = data.load_bars(src, "BTC", 60)
        self.assertEqual(len(b.ts), len(ts))
        self.assertTrue(np.array_equal(b.ts, ts))
        og, *_r, present = data.to_grid(b, t0, t0 + 3600 * 500)
        self.assertEqual(int(present.sum()), len(ts))
        self.assertTrue(np.all(np.isnan(og[~present])))      # nichts aufgefuellt
        with self.assertRaises(data.DataError):
            data.load_bars(src, "ETH", 60)
        src.close()
        with self.assertRaises(data.DataError):      # geschlossen -> kein stilles Weiterlesen
            src.read("XBTUSD_60.csv")

    def test_parse_errors_do_not_leak_content(self):
        with self.assertRaises(data.DataError) as cm:
            data.parse_ohlcvt(b"1,2,3\n4,5\n")
        self.assertNotIn("4,5", str(cm.exception))

    def test_ambiguous_member_rejected(self):
        p = os.path.join(self.tmp.name, "k.zip")
        ts, o, h, l, c, v = synth.hourly_walk(50, 20.0, 1, 1_600_041_600)
        raw = synth.to_csv(ts, o, h, l, c, v)
        synth.make_zip(p, {"XBTUSD_60.csv": raw, "sub/XBTUSD_60.csv": raw})
        with data.Source(p) as src:
            with self.assertRaises(data.DataError):
                data.load_bars(src, "BTC", 60)

    def test_window_quality_metrics(self):
        t0 = 1_600_041_600
        n = 2000
        ts, o, h, l, c, v = synth.hourly_walk(n, 20.0, 2, t0)
        keep = np.ones(n, bool); keep[100:110] = False           # 10-h-Luecke
        keep[500] = False
        b = type("B", (), {})(); b.asset = "BTC"
        for k, arr in zip("ts o h l c v".split(), (ts, o, h, l, c, v)):
            setattr(b, k, arr[keep])
        q = quality.check_window(b, t0, t0 + 3600 * n)
        self.assertEqual(q["present_bars"], n - 11)
        self.assertEqual(q["max_gap_hours"], 10)
        self.assertFalse(q["passes"])
        self.assertTrue(any("Luecke" in r for r in q["reasons"]))
        # sauber
        b2 = type("B", (), {})(); b2.asset = "BTC"
        for k, arr in zip("ts o h l c v".split(), (ts, o, h, l, c, v)):
            setattr(b2, k, arr)
        self.assertTrue(quality.check_window(b2, t0, t0 + 3600 * n)["passes"])

    def test_big_move_review_list_not_removed(self):
        t0 = 1_600_041_600
        ts, o, h, l, c, v = synth.hourly_walk(300, 10.0, 3, t0)
        c = c.copy(); c[150:] *= 1.5                              # +50 %-Sprung
        b = type("B", (), {})(); b.asset = "BTC"
        for k, arr in zip("ts o h l c v".split(), (ts, o, h, l, c, v)):
            setattr(b, k, arr)
        q = quality.check_window(b, t0, t0 + 3600 * 300)
        self.assertEqual(q["big_move_count"], 1)
        self.assertEqual(len(q["big_move_review_list"]), 1)
        self.assertEqual(q["present_bars"], 300)


if __name__ == "__main__":
    unittest.main()
