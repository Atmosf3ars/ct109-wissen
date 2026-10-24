import hashlib
import json
import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
from lf1 import cli, paper_eval, runner  # noqa: E402
from test_runner import H1, Base, candles, cfg_dict, feed_replay, make_doc, open_files_under  # noqa: E402


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


class TestPaperEval(Base):
    def fill(self, cs, hyps=None, **kw):
        r = self.mk(hyps or [H1], **kw)
        feed_replay(r, "BTC", cs)
        r.close()
        return make_doc(hyps or [H1])

    def ev(self, doc, **kw):
        return paper_eval.evaluate_paper(self.db, doc, nboot=300, nplacebo=100, **kw)

    def test_gapfree_replay_is_equivalent_and_descriptive(self):
        doc = self.fill(candles(1300, 7, sig_bp=45.0, drift_bp=0.5))
        res = self.ev(doc)
        self.assertIn("keine Kategorie", res["label"])
        h = res["hypotheses"][0]
        self.assertEqual(h["status"], "ok")
        self.assertGreater(h["n_trades"], 10)
        eq = h["equivalence"]
        self.assertTrue(eq["applicable"])
        self.assertTrue(eq["equal"])
        self.assertEqual((eq["only_runner"], eq["only_backtest"]), (0, 0))
        self.assertEqual(eq["matched"], h["n_trades"])
        self.assertLess(eq["max_abs_net_diff_bp"], 1e-6)
        self.assertTrue(0 < h["placebo"]["p_ge_live"] <= 1)
        self.assertEqual(h["n_long"] + h["n_short"], h["n_trades"])
        for k in ("category", "verdict", "BESTAETIGT"):
            self.assertNotIn(k, json.dumps(res))

    def test_matches_runner_trades_and_stats(self):
        doc = self.fill(candles(1300, 7, sig_bp=45.0, drift_bp=0.5))
        r = self.mk([H1])
        live = r.trades("H1")
        h = self.ev(doc)["hypotheses"][0]
        self.assertEqual(h["n_trades"], len(live))
        self.assertAlmostEqual(h["net_mean_bp"], sum(t["net_bp"] for t in live) / len(live), places=9)
        self.assertAlmostEqual(h["gross_mean_bp"], sum(t["gross_bp"] for t in live) / len(live), places=9)

    def test_deterministic_and_seeded_by_freeze(self):
        doc = self.fill(candles(1300, 7, sig_bp=45.0, drift_bp=0.5))
        a, b = self.ev(doc), self.ev(doc)
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))
        d2 = make_doc([dict(H1, params={"L": 24, "side": "both"})])
        self.assertEqual(d2["freeze_hash"], doc["freeze_hash"])      # gleiche Liste => gleiche Seeds

    def test_does_not_touch_database(self):
        doc = self.fill(candles(1300, 7))
        before = sha(self.db)
        self.ev(doc)
        self.assertEqual(sha(self.db), before)
        self.assertEqual(open_files_under(self.tmp.name), [])

    def test_db_bound_to_freeze_and_hash_checked(self):
        doc = self.fill(candles(900, 3))
        other = make_doc([dict(H1, id="HX", params={"L": 48, "side": "both"})])
        with self.assertRaises(runner.StartRefused):
            self.ev(other)
        bad = json.loads(json.dumps(doc))
        bad["payload"]["hypotheses"][0]["params"]["L"] = 25
        with self.assertRaises(runner.StartRefused):
            self.ev(bad)
        with self.assertRaises(runner.StartRefused):
            paper_eval.evaluate_paper(os.path.join(self.tmp.name, "fehlt.sqlite"), doc)
        self.assertEqual(open_files_under(self.tmp.name), [])

    def test_gap_makes_equivalence_not_applicable(self):
        doc = self.fill(candles(1300, 7, sig_bp=45.0, skip=(700, 701, 702)))
        eq = self.ev(doc)["hypotheses"][0]["equivalence"]
        self.assertFalse(eq["applicable"])
        self.assertFalse(eq["equal"])
        self.assertIn("Luecken", eq["not_applicable_because"])

    def test_block_makes_equivalence_not_applicable(self):
        r = self.mk([H1], max_open=0)
        feed_replay(r, "BTC", candles(900, 5, sig_bp=45.0))
        r.close()
        h = self.ev(make_doc([H1]))["hypotheses"][0]
        self.assertTrue(h["blocked_decisions"])
        self.assertIn("Sperren", h["equivalence"]["not_applicable_because"])
        self.assertEqual(h["n_trades"], 0)
        self.assertIn("zu wenige", h["status"])

    def test_mismatch_is_reported_not_hidden(self):
        """Wird ein Runner-Trade nachtraeglich veraendert, muss der Vergleich es zeigen (sonst waere er wertlos)."""
        doc = self.fill(candles(1300, 7, sig_bp=45.0, drift_bp=0.5))
        con = sqlite3.connect(self.db)
        with con:
            dec = con.execute("SELECT dec_ts FROM trades ORDER BY dec_ts LIMIT 1").fetchone()[0]
            con.execute("UPDATE trades SET net_bp = net_bp + 5.0 WHERE dec_ts=?", (dec,))
        con.close()
        eq = self.ev(doc)["hypotheses"][0]["equivalence"]
        self.assertTrue(eq["applicable"])
        self.assertFalse(eq["equal"])
        self.assertAlmostEqual(eq["max_abs_net_diff_bp"], 5.0, places=6)
        con = sqlite3.connect(self.db)
        with con:
            con.execute("DELETE FROM trades WHERE dec_ts=?", (dec,))
        con.close()
        eq = self.ev(doc)["hypotheses"][0]["equivalence"]
        self.assertEqual(eq["only_backtest"], 1)
        self.assertFalse(eq["equal"])

    def test_extra_runner_trade_is_reported(self):
        doc = self.fill(candles(1300, 7, sig_bp=45.0, drift_bp=0.5))
        con = sqlite3.connect(self.db)
        with con:
            row = con.execute("SELECT * FROM trades ORDER BY dec_ts LIMIT 1").fetchone()
            dec = row[1] + 3600 * 5                      # eine Entscheidung, die der Backtest nicht trifft (Position noch offen)
            con.execute("INSERT INTO trades VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (row[0], dec, dec + 3600, dec + 3600 * 25, dec + 3600 * 25, 1, 100.0, 101.0, 100.0, 5.0, 5.0, 0.0, 95.0, 0))
        con.close()
        eq = self.ev(doc)["hypotheses"][0]["equivalence"]
        self.assertEqual(eq["only_runner"], 1)
        self.assertFalse(eq["equal"])

    def test_block_len_follows_entry_spacing(self):
        import math
        doc = self.fill(candles(1300, 7, sig_bp=45.0, drift_bp=0.5))
        r = self.mk([H1])
        ents = [t["entry_ts"] for t in r.trades("H1")]
        spacing = sum(b - a for a, b in zip(ents, ents[1:])) / (len(ents) - 1) / 3600.0
        want = max(2, int(math.ceil(6.0 * 24 / spacing)))
        self.assertGreater(want, 2)
        self.assertEqual(self.ev(doc)["hypotheses"][0]["block_len_trades"], want)

    def test_late_exit_excluded_from_equivalence_but_counted(self):
        doc = self.fill(candles(1300, 7, sig_bp=45.0, drift_bp=0.5))
        con = sqlite3.connect(self.db)
        with con:
            con.execute("UPDATE trades SET late_exit=1 WHERE dec_ts=(SELECT MIN(dec_ts) FROM trades)")
        con.close()
        h = self.ev(doc)["hypotheses"][0]
        self.assertEqual(h["n_late_exit"], 1)
        self.assertIn("late_exit", h["equivalence"]["not_applicable_because"])
        self.assertEqual(h["equivalence"]["only_backtest"], 1)

    def test_placebo_p_and_quantile_computed_from_simulations(self):
        import numpy as np
        from unittest import mock
        doc = self.fill(candles(1300, 7, sig_bp=45.0, drift_bp=0.5))
        fixed = np.arange(100.0) - 40.0
        with mock.patch("lf1.paper_eval.placebo_means", return_value=fixed):
            h = self.ev(doc)["hypotheses"][0]
        m = h["net_mean_bp"]
        pl = h["placebo"]
        self.assertAlmostEqual(pl["p_ge_live"], (int((fixed >= m).sum()) + 1) / 101.0, places=12)
        self.assertAlmostEqual(pl["q95_bp"], float(np.quantile(fixed, 0.95)), places=9)
        self.assertAlmostEqual(pl["mean_bp"], float(fixed.mean()), places=9)
        self.assertEqual(pl["live_above_q95"], bool(m > np.quantile(fixed, 0.95)))
        self.assertEqual(pl["n_sim"], 100)
        with mock.patch("lf1.paper_eval.placebo_means", return_value=None):
            self.assertIsNone(self.ev(doc)["hypotheses"][0]["placebo"])

    def test_gap_in_warmup_history_is_not_in_window(self):
        doc = self.fill(candles(1300, 7, sig_bp=45.0, drift_bp=0.5, skip=(100,)))
        h = self.ev(doc)["hypotheses"][0]
        self.assertEqual(h["missing_bars_in_window"], 0)
        self.assertEqual(h["gap_events"], 0)

    def test_bar_error_makes_equivalence_not_applicable(self):
        r = self.mk([H1])
        cs = candles(1100, 7, sig_bp=45.0, drift_bp=0.5)
        real, bad = r._decide, cs[700][0]
        def boom(h, asset, t, px_open, recv_ts):
            if t == bad:
                raise ValueError("x")
            return real(h, asset, t, px_open, recv_ts)
        r._decide = boom
        feed_replay(r, "BTC", cs)
        r.close()
        h = self.ev(make_doc([H1]))["hypotheses"][0]
        self.assertEqual(h["bar_error_events"], 1)
        self.assertIn("Kerzenfehler", h["equivalence"]["not_applicable_because"])

    def test_no_live_bars(self):
        r = self.mk([H1])
        r.close()
        h = self.ev(make_doc([H1]))["hypotheses"][0]
        self.assertEqual(h["status"], "keine Live-Kerzen")

    def test_window_starts_at_first_live_decision(self):
        """Warmup-Kerzen zaehlen nicht zum Fenster: Trades nur ab der ersten Live-Kerze."""
        doc = self.fill(candles(1300, 7, sig_bp=45.0, drift_bp=0.5))
        h = self.ev(doc)["hypotheses"][0]
        self.assertEqual(h["live_bars"], 1300 - 420)
        self.assertEqual(h["missing_bars_in_window"], 0)
        self.assertEqual(h["first_live_bar_ts"], candles(1300, 7)[420][0])


class TestReadOnlyRunner(Base):
    def test_readonly_cannot_write_and_leaves_db_unchanged(self):
        r = self.mk([H1])
        feed_replay(r, "BTC", candles(500, 2))
        r.close()
        before = sha(self.db)
        ro = runner.Runner(self.db, make_doc([H1]), read_only=True)
        self._open.append(ro)
        with self.assertRaises(sqlite3.OperationalError):
            ro.conn.execute("INSERT INTO events (ts, kind) VALUES (1,'x')")
        st = ro.status(10 ** 10)
        self.assertEqual(st["per_hypothesis"][0]["id"], "H1")
        ro.close()
        self.assertEqual(sha(self.db), before)

    def test_readonly_refuses_foreign_freeze_missing_db_and_closes(self):
        self.mk([H1]).close()
        with self.assertRaises(runner.StartRefused):
            runner.Runner(self.db, make_doc([dict(H1, id="HX", params={"L": 48, "side": "both"})]), read_only=True)
        with self.assertRaises(runner.StartRefused):
            runner.Runner(os.path.join(self.tmp.name, "fehlt.sqlite"), make_doc([H1]), read_only=True)
        self.assertFalse(os.path.exists(os.path.join(self.tmp.name, "fehlt.sqlite")))

    def test_readonly_does_not_hold_locks_for_running_runner(self):
        r = self.mk([H1])
        ro = runner.Runner(self.db, make_doc([H1]), read_only=True)
        self._open.append(ro)
        feed_replay(r, "BTC", candles(500, 2))       # Schreiben ist trotz offenem Status-Leser moeglich
        self.assertEqual(ro.status(10 ** 10)["last_bar_ts"]["BTC"], candles(500, 2)[-1][0])


class TestCli(unittest.TestCase):
    def test_paper_eval_cli_and_status_readonly(self):
        with tempfile.TemporaryDirectory() as d:
            db, fz, cfgp, out = (os.path.join(d, x) for x in ("r.sqlite", "freeze.json", "cfg.json", "out"))
            doc = make_doc([H1])
            with open(fz, "w", encoding="utf-8") as f:
                json.dump(doc, f)
            with open(cfgp, "w", encoding="utf-8") as f:
                json.dump(cfg_dict(doc, fz, db), f)
            with runner.Runner(db, doc) as r:
                feed_replay(r, "BTC", candles(1100, 4, sig_bp=45.0))
            before = sha(db)
            self.assertEqual(cli.main(["paper-eval", "--config", cfgp, "--out", out, "--nboot", "200", "--nplacebo", "50"]), 0)
            files = [x for x in os.listdir(out) if x.startswith("paper_eval_")]
            self.assertEqual(len(files), 1)
            with open(os.path.join(out, files[0]), encoding="utf-8") as f:
                res = json.load(f)
            self.assertEqual(res["freeze_hash"], doc["freeze_hash"])
            self.assertEqual(cli.main(["paper-status", "--config", cfgp]), 0)
            self.assertEqual(sha(db), before)
            other = make_doc([dict(H1, id="HX", params={"L": 48, "side": "both"})])
            with open(fz, "w", encoding="utf-8") as f:
                json.dump(other, f)
            self.assertEqual(cli.main(["paper-eval", "--config", cfgp, "--out", out]), 6)
            self.assertEqual(cli.main(["paper-status", "--config", cfgp]), 6)


if __name__ == "__main__":
    unittest.main()
