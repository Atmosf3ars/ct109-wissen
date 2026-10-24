"""Tests zu den Befunden der unabhaengigen Zweitpruefung (QA2, 23.10.2026): jeder Test haelt ein behobenes Fehlverhalten fest."""
import contextlib
import io
import json
import os
import sqlite3
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
from lf1 import cli, feed, loop, runner  # noqa: E402
from test_runner import H1, HOUR, Base, candles, cfg_dict, feed_replay, make_doc  # noqa: E402


def n_events(r, kind):
    return r.conn.execute("SELECT COUNT(*) FROM events WHERE kind=?", (kind,)).fetchone()[0]


def n_live(r):
    return r.conn.execute("SELECT COUNT(*) FROM processed WHERE kind='live'").fetchone()[0]


class TestFutureAndBadCandles(Base):
    def test_future_bar_is_dropped_and_later_bars_still_processed(self):
        cs = candles(520, 3)
        r = self.mk([H1]); feed_replay(r, "BTC", cs[:500])
        t = cs[499][0]
        far = t + 1000 * HOUR
        r.ingest("BTC", [cs[499], (far, 100.0, 101.0, 99.0, 100.5, 1.0)], t + 5)
        self.assertEqual(n_events(r, "future_bar"), 1)
        self.assertIsNone(r.conn.execute("SELECT 1 FROM bars WHERE ts=?", (far,)).fetchone())
        before = n_live(r)
        feed_replay_tail = cs[499:520]
        for k in range(1, len(feed_replay_tail)):
            r.ingest("BTC", feed_replay_tail[k - 1:k + 1], feed_replay_tail[k][0] + 5)
        self.assertEqual(n_live(r), before + 20)             # echte Kerzen laufen weiter (vorher: alle als backfilled)
        self.assertEqual(r.conn.execute("SELECT COUNT(*) FROM processed WHERE kind='backfilled'").fetchone()[0], 0)
        self.assertGreaterEqual(r.status(cs[519][0] + 60)["age_s"]["BTC"], 0)

    def test_current_hour_bar_is_accepted(self):
        cs = candles(430, 3)
        r = self.mk([H1]); feed_replay(r, "BTC", cs)
        self.assertEqual(n_events(r, "future_bar"), 0)

    def test_implausible_candles_are_skipped_and_logged(self):
        cs = candles(430, 3)
        r = self.mk([H1]); feed_replay(r, "BTC", cs)
        t = cs[-1][0]
        bad = {
            "nan_open": (t + HOUR, float("nan"), 101.0, 99.0, 100.0, 1.0),
            "inf_close": (t + HOUR, 100.0, 101.0, 99.0, float("inf"), 1.0),
            "zero_close": (t + HOUR, 100.0, 101.0, 0.0, 0.0, 1.0),
            "high_below_open": (t + HOUR, 100.0, 99.0, 98.0, 98.5, 1.0),
            "low_above_close": (t + HOUR, 100.0, 101.0, 100.5, 100.2, 1.0),
            "negative_volume": (t + HOUR, 100.0, 101.0, 99.0, 100.0, -1.0),
            "text": (t + HOUR, "x", 101.0, 99.0, 100.0, 1.0),
        }
        for name, cd in bad.items():
            r.ingest("BTC", [cd], t + HOUR + 5)
            self.assertIsNone(r.conn.execute("SELECT 1 FROM bars WHERE ts=?", (t + HOUR,)).fetchone(), name)
        self.assertEqual(n_events(r, "bad_candle"), len(bad))
        self.assertEqual(n_events(r, "fetch_error"), 0)
        good = (t + HOUR, 100.0, 100.5, 99.5, 100.2, 1.0)
        before = n_live(r)
        r.ingest("BTC", [good], t + HOUR + 5)                # danach laeuft die Aufnahme normal weiter
        self.assertEqual(n_live(r), before + 1)

    def test_candle_problem_accepts_valid_and_boundary(self):
        self.assertIsNone(runner.candle_problem(100, 101, 99, 100.5, 0.0))
        self.assertIsNone(runner.candle_problem(100, 100, 100, 100, 0))      # flache Kerze
        self.assertEqual(runner.candle_problem(100, 101, 99, 100.5, float("nan")), "not_finite")

    def test_empty_candle_list_is_logged(self):
        r = self.mk([H1])
        r.ingest("BTC", [], 1_760_000_000)
        self.assertEqual(n_events(r, "empty_candles"), 1)


class TestDecisionRecord(Base):
    def test_decision_stores_close_and_revision_is_logged(self):
        cs = candles(430, 4)
        r = self.mk([H1]); feed_replay(r, "BTC", cs)
        i_ts = cs[-2][0]                                     # letzte entschiedene Kerze (Entscheidung beim Open der letzten)
        row = r.conn.execute("SELECT close_px FROM decisions WHERE bar_ts=?", (i_ts,)).fetchone()
        self.assertAlmostEqual(row["close_px"], cs[-2][4], places=9)
        self.assertEqual(n_events(r, "bar_revised"), 0)
        o, h, l, c, v = cs[-2][1:]
        r.ingest("BTC", [(i_ts, o, h * 1.001, l, c * 1.0005, v)], cs[-1][0] + 60)
        self.assertEqual(n_events(r, "bar_revised"), 1)
        self.assertAlmostEqual(r.conn.execute("SELECT close_px FROM decisions WHERE bar_ts=?", (i_ts,)).fetchone()[0], cs[-2][4], places=9)

    def test_update_of_live_bar_before_decision_is_not_a_revision(self):
        cs = candles(430, 4)
        r = self.mk([H1]); feed_replay(r, "BTC", cs[:429])
        t = cs[429][0]
        o, h, l, c, v = cs[429][1:]
        r.ingest("BTC", [(t, o, h, l, c, v)], t + 5)
        r.ingest("BTC", [(t, o, h * 1.0001, l, c * 1.00005, v)], t + 600)    # laufende Kerze waechst
        self.assertEqual(n_events(r, "bar_revised"), 0)


class TestStartGuardExternal(Base):
    def test_expected_hashes_must_match(self):
        doc = make_doc([H1])
        from lf1.util import code_hash
        with self.assertRaises(runner.StartRefused):
            runner.Runner(self.db, doc, expected_freeze_hash="0" * 64)
        with self.assertRaises(runner.StartRefused):
            runner.Runner(self.db, doc, expected_code_hash="0" * 64)
        r = runner.Runner(self.db, doc, expected_freeze_hash=doc["freeze_hash"], expected_code_hash=code_hash())
        self._open.append(r)

    def test_re_hashed_modified_freeze_is_refused_with_external_hash(self):
        orig = make_doc([H1])
        changed = make_doc([dict(H1, params={"L": 30, "side": "both"})])     # selbstkonsistent, aber anderer Inhalt
        with self.assertRaises(runner.StartRefused):
            runner.Runner(self.db, changed, expected_freeze_hash=orig["freeze_hash"])

    def test_start_event_and_meta_record_environment_and_mode(self):
        r = self.mk([H1], shadow=True, config_snapshot={"x": 1}, start_ts=1_760_000_000)
        ev = json.loads(r.conn.execute("SELECT detail FROM events WHERE kind='start'").fetchone()[0])
        self.assertEqual(ev["mode"], "shadow")
        self.assertIn("python", ev); self.assertIn("numpy", ev); self.assertEqual(ev["config"], {"x": 1})
        meta = dict(r.conn.execute("SELECT k, v FROM meta").fetchall())
        self.assertEqual(meta["mode"], "shadow"); self.assertEqual(meta["created_utc"], "1760000000")

    def test_mode_switch_on_existing_db_is_refused(self):
        self.mk([H1], shadow=True).close()
        with self.assertRaises(runner.StartRefused):
            runner.Runner(self.db, make_doc([H1]), shadow=False)
        self.mk([H1], shadow=True).close()                   # gleicher Modus: ok
        db2 = os.path.join(self.tmp.name, "p.sqlite")
        runner.Runner(db2, make_doc([H1]), shadow=False).close()
        with self.assertRaises(runner.StartRefused):
            runner.Runner(db2, make_doc([H1]), shadow=True)

    @unittest.skipUnless(sys.platform != "win32", "fcntl nur unter Linux")
    def test_second_process_on_same_db_is_refused(self):
        r = self.mk([H1])
        with self.assertRaises(runner.StartRefused):
            runner.Runner(self.db, make_doc([H1]))
        r.close()
        self.mk([H1])                                       # nach Freigabe wieder moeglich

    def test_corrupt_db_is_start_refused_not_crash(self):
        with open(self.db, "wb") as f:
            f.write(b"das ist keine sqlite datei" * 200)
        with self.assertRaises(runner.StartRefused):
            runner.Runner(self.db, make_doc([H1]))


class TestConfigStrict(Base):
    def run_cli(self, cfg_obj, *extra, cmd="paper-status"):
        cfg = os.path.join(self.tmp.name, "cfg.json")
        with open(cfg, "w") as f:
            json.dump(cfg_obj, f)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cli.main([cmd, "--config", cfg] + list(extra))
        return rc, buf.getvalue()

    def setUp(self):
        super().setUp()
        self.fz = os.path.join(self.tmp.name, "freeze.json")
        self.doc = make_doc([H1])
        json.dump(self.doc, open(self.fz, "w"))
        self.good = cfg_dict(self.doc, self.fz, self.db, kill=self.kill)
        self.mk([H1]).close()

    def test_valid_config_ok(self):
        rc, _ = self.run_cli(self.good)
        self.assertEqual(rc, 0)

    def test_typo_missing_unknown_and_wrong_types_refused(self):
        cases = {
            "typo kill_flag": {k.replace("kill_flag", "kill_flg"): v for k, v in self.good.items()},
            "missing shadow": {k: v for k, v in self.good.items() if k != "shadow"},
            "missing loss": {k: v for k, v in self.good.items() if k != "max_daily_loss_bp"},
            "extra field": dict(self.good, shadw=True),
            "shadow text": dict(self.good, shadow="false"),
            "shadow int": dict(self.good, shadow=0),
            "loss zero": dict(self.good, max_daily_loss_bp=0),
            "loss bool": dict(self.good, max_daily_loss_bp=True),
            "max_open float": dict(self.good, max_open=2.5),
            "late_s zero": dict(self.good, late_s=0),
            "hash upper": dict(self.good, expected_freeze_hash=self.doc["freeze_hash"].upper()),
            "hash short": dict(self.good, expected_code_hash="abc"),
            "hash placeholder": dict(self.good, expected_code_hash="<hier>"),
            "wrong freeze hash": dict(self.good, expected_freeze_hash="0" * 64),
        }
        for name, c in cases.items():
            rc, out = self.run_cli(c)
            self.assertEqual(rc, 6, name)
            self.assertIn("RUNNER START VERWEIGERT", out, name)

    def test_unreadable_or_invalid_json_is_refused_with_6(self):
        cfg = os.path.join(self.tmp.name, "cfg.json")
        open(cfg, "w").write("{kaputt")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(cli.main(["paper-status", "--config", cfg]), 6)
            self.assertEqual(cli.main(["paper-status", "--config", os.path.join(self.tmp.name, "fehlt.json")]), 6)

    def test_corrupt_db_via_cli_exit_6(self):
        db2 = os.path.join(self.tmp.name, "kaputt.sqlite")
        with open(db2, "wb") as f:
            f.write(b"x" * 5000)
        rc, out = self.run_cli(dict(self.good, db=db2), cmd="paper-run")
        self.assertEqual(rc, 6)


class TestStatusAlarm(Base):
    def setUp(self):
        super().setUp()
        self.fz = os.path.join(self.tmp.name, "freeze.json")
        self.doc = make_doc([H1])
        json.dump(self.doc, open(self.fz, "w"))
        self.cfg = os.path.join(self.tmp.name, "cfg.json")
        json.dump(cfg_dict(self.doc, self.fz, self.db, kill=self.kill), open(self.cfg, "w"))

    def status(self, now, *extra):
        buf = io.StringIO()
        with mock.patch("time.time", return_value=float(now)), contextlib.redirect_stdout(buf):
            rc = cli.main(["paper-status", "--config", self.cfg] + list(extra))
        return rc, buf.getvalue()

    def test_exit_8_for_empty_stale_future_and_0_for_fresh(self):
        self.mk([H1]).close()
        rc, out = self.status(1_800_000_000, "--max-age-s", "7800")
        self.assertEqual(rc, 8); self.assertIn("keine Kerze", out)         # leere DB / Asset ohne Kerzen
        cs = candles(430, 4)
        r = self.mk([H1]); feed_replay(r, "BTC", cs); r.close()
        t = cs[-1][0]
        self.assertEqual(self.status(t + 3700, "--max-age-s", "7800")[0], 0)
        self.assertEqual(self.status(t + 7800, "--max-age-s", "7800")[0], 0)   # Grenze selbst ist noch ok
        rc, out = self.status(t + 7801, "--max-age-s", "7800")
        self.assertEqual(rc, 8); self.assertIn("Kerzenalter", out)
        rc, out = self.status(t - 100, "--max-age-s", "7800")
        self.assertEqual(rc, 8); self.assertIn("negatives", out)
        self.assertEqual(self.status(t + 99999)[0], 0)                          # ohne --max-age-s nur Anzeige

    def test_html_is_written_atomically_and_flags_problems(self):
        out = os.path.join(self.tmp.name, "s.html")
        self.mk([H1]).close()
        self.status(1_800_000_000, "--html", out)
        self.assertFalse(os.path.exists(out + ".tmp"))
        self.assertIn("KEINE KERZE", open(out, encoding="utf-8").read())
        cs = candles(430, 4)
        r = self.mk([H1]); feed_replay(r, "BTC", cs); r.close()
        self.status(cs[-1][0] - 500, "--html", out)
        self.assertIn("ZUKUNFT", open(out, encoding="utf-8").read())
        self.assertFalse(os.path.exists(out + ".tmp"))


class TestFeedAndLoopHardening(Base):
    def test_redirect_is_refused(self):
        h = feed._NoRedirect()
        with self.assertRaises(feed.FeedError):
            h.redirect_request(mock.Mock(), None, 302, "Found", {}, "https://evil.example/x")

    def test_oversized_response_is_refused_and_opener_has_no_redirects(self):
        class Resp:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self, n): return b"x" * n
        opener = mock.Mock(); opener.open.return_value = Resp()
        with mock.patch("lf1.feed.urllib.request.build_opener", return_value=opener) as bo:
            with self.assertRaises(feed.FeedError):
                feed._get(feed.OHLC_URL, {"pair": "XBTUSD"})
        self.assertTrue(any(isinstance(a, type) and issubclass(a, feed._NoRedirect) for a in bo.call_args[0]))

    def test_transient_sqlite_error_does_not_mark_bar_as_error(self):
        cs = candles(430, 4)
        r = self.mk([H1]); feed_replay(r, "BTC", cs[:429])
        t = cs[429][0]
        real = r._on_bar
        calls = {"n": 0}
        def flaky(asset, ts, recv):
            calls["n"] += 1
            if calls["n"] == 1:
                raise sqlite3.OperationalError("disk I/O error")
            return real(asset, ts, recv)
        with mock.patch.object(r, "_on_bar", flaky):
            with self.assertRaises(sqlite3.OperationalError):
                r.ingest("BTC", cs[428:430], t + 5)
            self.assertEqual(r.conn.execute("SELECT COUNT(*) FROM processed WHERE ts=?", (t,)).fetchone()[0], 0)
            self.assertEqual(n_events(r, "bar_error"), 0)
            r.ingest("BTC", cs[428:430], t + 50)              # Wiederholung verarbeitet die Kerze
        self.assertEqual(r.conn.execute("SELECT kind FROM processed WHERE ts=?", (t,)).fetchone()[0], "live")

    def test_cycle_retries_when_current_bar_missing(self):
        cs = candles(430, 4)
        r = self.mk([H1]); feed_replay(r, "BTC", cs[:429])
        t = cs[429][0]
        answers = [cs[427:429], cs[427:430]]                 # erst ohne aktuelle Kerze, dann mit
        fetched, slept = [], []
        def fetch(asset):
            fetched.append(asset); return answers[min(len(fetched) - 1, 1)]
        loop.run_cycle(r, ["BTC"], fetch, lambda: t + 25, slept.append)
        self.assertEqual(len(fetched), 2); self.assertEqual(slept, [loop.RETRY_S])
        self.assertEqual(n_events(r, "bar_missing"), 1)
        self.assertEqual(r.conn.execute("SELECT kind FROM processed WHERE ts=?", (t,)).fetchone()[0], "live")

    def test_cycle_gives_up_after_retries_without_error(self):
        cs = candles(430, 4)
        r = self.mk([H1]); feed_replay(r, "BTC", cs[:429])
        t = cs[429][0]
        slept = []
        loop.run_cycle(r, ["BTC"], lambda a: cs[427:429], lambda: t + 25, slept.append)
        self.assertEqual(len(slept), loop.RETRIES - 1)
        self.assertEqual(n_events(r, "bar_missing"), loop.RETRIES - 1)

    def test_empty_ticker_is_logged(self):
        cs = candles(430, 4)
        r = self.mk([H1]); feed_replay(r, "BTC", cs)
        loop.run_cycle(r, ["BTC"], lambda a: cs[-2:], lambda: cs[-1][0] + 25, lambda s: None, fetch_tickers=lambda assets: {})
        self.assertEqual(n_events(r, "ticker_empty"), 1)


class TestSurvivorsFromMutationRun(Base):
    """Ungetestetes Verhalten, das die Mutationsliste der Zweitpruefung gefunden hat (M05, M25, M14, M16, M17, M24)."""

    def test_trade_row_stores_cost_components_and_net_identity(self):
        from lf1.backtest import cost_for
        cs = candles(900, 5, sig_bp=45.0)
        r = self.mk([H1]); feed_replay(r, "BTC", cs)
        trades = r.trades("H1")
        self.assertGreater(len(trades), 3)
        cost = cost_for("BTC")
        for tr in trades:
            self.assertAlmostEqual(tr["roundtrip_bp"], cost.mult * cost.roundtrip_bp, places=9)
            self.assertAlmostEqual(tr["funding_bp"], cost.mult * cost.funding_bp_per_8h * 24 / 8.0, places=9)
            self.assertAlmostEqual(tr["cost_bp"], cost.cost_bp(24), places=9)
            self.assertAlmostEqual(tr["net_bp"], tr["gross_bp"] - tr["cost_bp"], places=9)
        self.assertGreater(trades[0]["funding_bp"], 0.0)

    def test_daily_net_uses_utc_day_boundary(self):
        r = self.mk([H1])
        day = 20_000
        rows = [(day * 86400 - 1, -100.0), (day * 86400, -7.0), (day * 86400 + 86399, -3.0), ((day + 1) * 86400, -50.0)]
        for i, (xt, net) in enumerate(rows):
            r.conn.execute("INSERT INTO trades VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                           ("H1", i, xt - 7200, xt, xt, 1, 100.0, 100.0, 0.0, 0.0, 0.0, 0.0, net, 0))
        r.conn.commit()
        self.assertAlmostEqual(r._daily_net(day * 86400 + 5), -10.0)
        self.assertAlmostEqual(r._daily_net((day - 1) * 86400 + 5), -100.0)

    def test_decision_stores_recv_ts(self):
        cs = candles(430, 4)
        r = self.mk([H1]); feed_replay(r, "BTC", cs, late=7)
        row = r.conn.execute("SELECT recv_ts FROM decisions ORDER BY bar_ts DESC LIMIT 1").fetchone()
        self.assertEqual(row["recv_ts"], cs[-1][0] + 7)

    def test_single_missing_bar_is_a_gap_event(self):
        cs = candles(440, 4, skip=(430,))
        r = self.mk([H1]); feed_replay(r, "BTC", cs)
        gaps = [json.loads(x[0]) for x in r.conn.execute("SELECT detail FROM events WHERE kind='gap'")]
        self.assertEqual([g["missing"] for g in gaps], [1])

    def test_heartbeat_event_per_live_bar(self):
        cs = candles(440, 4)
        r = self.mk([H1]); feed_replay(r, "BTC", cs)
        self.assertEqual(n_events(r, "heartbeat"), n_live(r))
        self.assertGreater(n_live(r), 10)

    def test_hash_fields_must_be_exactly_64_hex(self):
        doc = make_doc([H1])
        good = cfg_dict(doc, "f", "d")
        cli._validate_config(good)
        for bad in ("a" * 63, "a" * 65, "g" * 64):
            with self.assertRaises(runner.StartRefused):
                cli._validate_config(dict(good, expected_code_hash=bad))


if __name__ == "__main__":
    unittest.main()
