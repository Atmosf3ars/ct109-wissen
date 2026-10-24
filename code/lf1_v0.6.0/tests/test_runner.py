import json
import os
import re
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
from lf1 import backtest as bt  # noqa: E402
from lf1 import core, feed, loop, runner  # noqa: E402
from lf1.util import json_hash  # noqa: E402

T0 = 1_760_000_000 // 3600 * 3600          # Stundenraster
H1 = dict(id="H1", rule="TS_MOM", params={"L": 24, "side": "both"}, asset="BTC", H=24)
H2 = dict(id="H2", rule="BREAKOUT", params={"L": 48, "side": "both"}, asset="ETH", H=72)


def gate_stub():
    cells = [{"asset": a, "h_hours": h, "class": "W", "evaluable": True, "mde_net_bp_full_exposure": 50.0, "n_eff": 200}
             for a in ("BTC", "ETH", "SOL") for h in (24, 72)]
    return {"result_hash": "g" * 64, "cells": cells}


def make_doc(hyps):
    payload, fh = bt.make_freeze(hyps, gate_stub(), "r" * 64, "b" * 64, {}, [])
    return {"freeze_hash": fh, "payload": payload}


def cfg_dict(doc, fz, db, shadow=False, kill="/nonexistent/KILL", **over):
    """Vollstaendige, gueltige Runner-Konfiguration (alle Felder Pflicht, QA2 M2)."""
    from lf1.util import code_hash
    c = {"freeze": fz, "db": db, "kill_flag": kill, "max_daily_loss_bp": 1500, "max_open": 2, "late_s": 300, "shadow": shadow,
         "expected_freeze_hash": doc["freeze_hash"], "expected_code_hash": code_hash()}
    c.update(over)
    return c


def candles(n, seed, sig_bp=40.0, drift_bp=0.0, t0=T0, skip=()):
    rng = np.random.default_rng(seed)
    lr = (drift_bp + rng.normal(0, sig_bp, n)) * 1e-4
    p = 100.0 * np.exp(np.concatenate(([0.0], np.cumsum(lr))))
    c = p[1:]
    o = p[:-1] * (1.0 + rng.normal(0, 3e-4, n))       # Open weicht vom Vor-Close ab (Luecken/Spread), sonst waeren Open[i+1] und Close[i] gleich
    h, l = np.maximum(o, c) * 1.0002, np.minimum(o, c) * 0.9998
    return [(t0 + HOUR * i, o[i], h[i], l[i], c[i], 1.0) for i in range(n) if i not in skip]


HOUR = 3600


def feed_replay(r, asset, cs, warm=420, late=5, batch_with_prev=True):
    """Spielt Kerzen so ein, wie der Live-Abruf: Warmup-Block, danach je Stunde die letzten 2 Kerzen (Vor-Kerze final)."""
    r.ingest(asset, cs[:warm], cs[warm - 1][0] + late)
    for k in range(warm, len(cs)):
        chunk = cs[max(0, k - 1):k + 1] if batch_with_prev else cs[k:k + 1]
        r.ingest(asset, chunk, cs[k][0] + late)


def open_files_under(path):
    """Offene Datei-Handles dieses Prozesses unter path (nur Linux, /proc). Sonst leer: dort sperrt das OS selbst."""
    fd_dir = "/proc/self/fd"
    if not os.path.isdir(fd_dir):
        return []
    root, out = os.path.realpath(path), []
    for fd in os.listdir(fd_dir):
        try:
            t = os.readlink(os.path.join(fd_dir, fd))
        except OSError:
            continue
        if t.startswith(root):
            out.append(t)
    return out


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "r.sqlite")
        self.kill = os.path.join(self.tmp.name, "KILL")

        self._open = []

    def tearDown(self):
        for r in self._open:                  # Windows haelt SQLite-Dateien gesperrt, bis die Verbindung zu ist
            r.close()
        self._open = []
        self.assertEqual(open_files_under(self.tmp.name), [])   # Linux-Nachbildung der Windows-Sperre
        self.tmp.cleanup()

    def mk(self, hyps=None, **kw):
        kw.setdefault("kill_flag", self.kill)
        r = runner.Runner(self.db, make_doc(hyps or [H1]), **kw)
        self._open.append(r)
        return r


class TestStartGuard(Base):
    def test_bad_hash_refused(self):
        doc = make_doc([H1])
        doc["payload"]["hypotheses"][0]["params"]["L"] = 25
        with self.assertRaises(runner.StartRefused):
            runner.Runner(self.db, doc)

    def test_code_hash_mismatch_refused(self):
        with mock.patch("lf1.runner.code_hash", return_value="f" * 64):
            with self.assertRaises(runner.StartRefused):
                runner.Runner(self.db, make_doc([H1]))

    def test_db_bound_to_freeze(self):
        self.mk().close()
        with self.assertRaises(runner.StartRefused):
            runner.Runner(self.db, make_doc([H2]))
        self.mk().close()                                    # gleicher Freeze: ok

    def test_refused_start_closes_connection(self):
        """Windows-Befund 23.10.: abgelehnter Start liess r.sqlite offen, Datei war nicht loeschbar."""
        import sqlite3
        self.mk().close()
        real, made = sqlite3.connect, []
        def spy(*a, **k):
            c = real(*a, **k); made.append(c); return c
        with mock.patch("lf1.runner.sqlite3.connect", spy):
            with self.assertRaises(runner.StartRefused):
                runner.Runner(self.db, make_doc([H2]))
        self.assertEqual(len(made), 1)
        with self.assertRaises(sqlite3.ProgrammingError):
            made[0].execute("SELECT 1")

    def test_context_manager_closes(self):
        import sqlite3
        with runner.Runner(self.db, make_doc([H1])) as r:
            r.conn.execute("SELECT 1")
        with self.assertRaises(sqlite3.ProgrammingError):
            r.conn.execute("SELECT 1")

    def test_incomplete_doc_refused(self):
        with self.assertRaises(runner.StartRefused):
            runner.Runner(self.db, {"payload": {}})
        doc = make_doc([H1]); doc["payload"]["hypotheses"] = []
        doc["freeze_hash"] = json_hash(doc["payload"])
        with self.assertRaises(runner.StartRefused):
            runner.Runner(self.db, doc)


class TestEquivalence(Base):
    def test_runner_equals_backtest_trade_for_trade(self):
        cs = candles(1300, 7, sig_bp=45.0, drift_bp=0.5)
        r = self.mk([H1])
        feed_replay(r, "BTC", cs)
        live = r.trades("H1")
        self.assertGreater(len(live), 20)
        o = np.array([c[1] for c in cs]); h = np.array([c[2] for c in cs]); l = np.array([c[3] for c in cs]); c_ = np.array([c[4] for c in cs])
        grid = {"o": o, "h": h, "l": l, "c": c_}
        # Backtest ueber die Zeit nach dem Warmup (Entscheidungen ab Bar 419, Einstieg ab 420)
        bt_tr = bt.trades_for(H1, grid, [(419, len(cs))], bt.cost_for("BTC"))
        n = len(live)
        self.assertEqual(n, len(bt_tr))
        for k, row in enumerate(live):
            self.assertEqual(row["dec_ts"], cs[int(bt_tr["i_dec"][k])][0])
            self.assertEqual(row["entry_ts"], cs[int(bt_tr["i_entry"][k])][0])
            self.assertEqual(row["exit_ts"], cs[int(bt_tr["i_exit"][k])][0])
            self.assertEqual(row["side"], int(bt_tr["side"][k]))
            self.assertAlmostEqual(row["entry_px"], float(bt_tr["entry"][k]), places=9)
            self.assertAlmostEqual(row["exit_px"], float(bt_tr["exit"][k]), places=9)
            self.assertAlmostEqual(row["net_bp"], float(bt_tr["net_bp"][k]), places=9)
            self.assertEqual(row["late_exit"], 0)

    def test_equivalence_other_rules(self):
        cs = candles(1100, 3, sig_bp=60.0)
        grid = {k: np.array([c[j] for c in cs]) for k, j in (("o", 1), ("h", 2), ("l", 3), ("c", 4))}
        for hy in (H2, dict(H2, id="H3", asset="BTC", rule="SHOCK_FADE", params={"w": 2, "k": 1.5, "N": 48}, H=24)):
            r = self.mk([hy])
            feed_replay(r, hy["asset"], cs)
            live = r.trades(hy["id"])
            bt_tr = bt.trades_for(hy, grid, [(419, len(cs))], bt.cost_for(hy["asset"]))
            self.assertEqual(len(live), len(bt_tr), hy["rule"])
            self.assertGreater(len(live), 3, hy["rule"])
            for k, row in enumerate(live):
                self.assertAlmostEqual(row["net_bp"], float(bt_tr["net_bp"][k]), places=9)
            self.tearDown(); self.setUp()

    def test_double_fill_would_be_detected(self):
        """Doppel-Fill-Mutation: ein zweiter Einstieg waehrend offener Position muss die Gleichheit brechen."""
        cs = candles(900, 5, sig_bp=45.0)
        r = self.mk([H1])
        orig = r._decide
        def mutant(h, asset, t, px, recv):
            orig(h, asset, t, px, recv)
            r.conn.execute("DELETE FROM positions WHERE hyp_id=? AND entry_ts<?", (h["id"], t))   # erlaubt Ueberlappung
        r._decide = mutant
        feed_replay(r, "BTC", cs)
        grid = {k: np.array([c[j] for c in cs]) for k, j in (("o", 1), ("h", 2), ("l", 3), ("c", 4))}
        bt_tr = bt.trades_for(H1, grid, [(419, len(cs))], bt.cost_for("BTC"))
        self.assertNotEqual(len(r.trades("H1")), len(bt_tr))


class TestState(Base):
    def test_restart_mid_position_equals_uninterrupted(self):
        cs = candles(1000, 9, sig_bp=45.0)
        a = self.mk([H1]); feed_replay(a, "BTC", cs); full = a.trades("H1"); a.close()
        os.remove(self.db)
        b = self.mk([H1])
        b.ingest("BTC", cs[:420], cs[419][0] + 5)
        cut = 420
        while True:       # bis eine Position offen ist
            b.ingest("BTC", cs[cut - 1:cut + 1], cs[cut][0] + 5); cut += 1
            if b._open_count() > 0:
                break
        b.close()
        c = self.mk([H1])                                  # Neustart mitten in der Position
        for k in range(cut, len(cs)):
            c.ingest("BTC", cs[k - 1:k + 1], cs[k][0] + 5)
        self.assertEqual(c.trades("H1"), full)

    def test_reingest_is_idempotent(self):
        cs = candles(600, 2, sig_bp=45.0)
        r = self.mk([H1]); feed_replay(r, "BTC", cs); before = r.trades("H1")
        nd = r.conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
        for k in range(500, 600):
            r.ingest("BTC", cs[k - 5:k + 1], cs[k][0] + 9)     # alles erneut
        self.assertEqual(r.trades("H1"), before)
        self.assertEqual(r.conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0], nd)

    def test_crash_in_bar_processing_rolls_back(self):
        cs = candles(600, 4, sig_bp=45.0)
        r = self.mk([H1])
        r.ingest("BTC", cs[:420], cs[419][0] + 5)
        with mock.patch.object(r, "_decide", side_effect=KeyboardInterrupt("harter Abbruch")):    # BaseException: kein Fang, Rueckabwicklung
            with self.assertRaises(KeyboardInterrupt):
                r.ingest("BTC", cs[419:421], cs[420][0] + 5)
        self.assertEqual(r.conn.execute("SELECT COUNT(*) FROM processed WHERE ts=?", (cs[420][0],)).fetchone()[0], 0)
        r.ingest("BTC", cs[419:421], cs[420][0] + 5)
        self.assertEqual(r.conn.execute("SELECT COUNT(*) FROM processed WHERE ts=?", (cs[420][0],)).fetchone()[0], 1)

    def test_open_price_change_logged_not_applied(self):
        cs = candles(430, 4)
        r = self.mk([H1]); feed_replay(r, "BTC", cs)
        t, o = cs[-1][0], cs[-1][1]
        r.ingest("BTC", [(t, o * 1.01, max(cs[-1][2], o * 1.01), cs[-1][3], cs[-1][4], 1.0)], t + 100)
        self.assertEqual(r.conn.execute("SELECT o FROM bars WHERE ts=?", (t,)).fetchone()[0], o)
        self.assertEqual(r.conn.execute("SELECT COUNT(*) FROM events WHERE kind='open_changed'").fetchone()[0], 1)

    def test_warmup_blocks_decisions(self):
        cs = candles(300, 4, sig_bp=60.0)
        r = self.mk([H1]); feed_replay(r, "BTC", cs, warm=100)
        self.assertEqual(r.conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0], 0)
        acts = {x[0] for x in r.conn.execute("SELECT DISTINCT action FROM decisions")}
        self.assertEqual(acts, {"blocked"})

    def test_utc_dst_night_has_no_effect(self):
        switch = 1_792_890_000        # 2026-10-25 01:00:00 UTC (lokal 03:00 -> 02:00, Berlin)
        t0 = switch - 700 * 3600
        cs = candles(1000, 6, sig_bp=50.0, t0=t0)
        r = self.mk([H1]); feed_replay(r, "BTC", cs)
        tr = r.trades("H1")
        self.assertTrue(any(x["entry_ts"] < switch <= x["exit_ts"] for x in tr))      # Position ueber die Umstellung
        self.assertTrue(all((x["exit_ts"] - x["entry_ts"]) == 24 * HOUR for x in tr))  # Haltedauer exakt 24 h UTC
        self.assertEqual(r.conn.execute("SELECT COUNT(*) FROM events WHERE kind='gap'").fetchone()[0], 0)


class TestGapsAndBlocks(Base):
    def test_feed_gap_counted_and_not_interpolated(self):
        cs = candles(700, 8, sig_bp=45.0, skip={500, 501, 502})
        r = self.mk([H1]); feed_replay(r, "BTC", cs)
        ev = [json.loads(x[0]) for x in r.conn.execute("SELECT detail FROM events WHERE kind='gap'")]
        self.assertEqual(len(ev), 1); self.assertEqual(ev[0]["missing"], 3)
        self.assertEqual(r.conn.execute("SELECT COUNT(*) FROM bars WHERE asset='BTC'").fetchone()[0], 697)

    def test_backfilled_bar_is_stored_but_not_decided(self):
        cs = candles(700, 8, sig_bp=45.0, skip={500, 501, 502})
        full = candles(700, 8, sig_bp=45.0)
        r = self.mk([H1]); feed_replay(r, "BTC", cs)
        nd = r.conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
        tr = r.trades("H1"); op = r._open_count()
        r.ingest("BTC", [full[500], full[501], full[502]], full[-1][0] + 4000)
        self.assertEqual(r.conn.execute("SELECT COUNT(*) FROM bars WHERE asset='BTC'").fetchone()[0], 700)
        kinds = [x[0] for x in r.conn.execute("SELECT kind FROM processed WHERE ts IN (?,?,?)", (full[500][0], full[501][0], full[502][0]))]
        self.assertEqual(kinds, ["backfilled"] * 3)
        self.assertEqual(r.conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0], nd)
        self.assertEqual(r.trades("H1"), tr)
        self.assertEqual(r._open_count(), op)

    def test_missing_exit_bar_closes_late_and_flagged(self):
        cs = candles(700, 8, sig_bp=45.0)
        r0 = self.mk([H1]); feed_replay(r0, "BTC", cs)
        victim = r0.trades("H1")[0]; r0.close(); os.remove(self.db)
        miss = (victim["planned_exit_ts"] - T0) // HOUR
        cs2 = candles(700, 8, sig_bp=45.0, skip={miss})
        r = self.mk([H1]); feed_replay(r, "BTC", cs2)
        tr = [x for x in r.trades("H1") if x["dec_ts"] == victim["dec_ts"]]
        self.assertEqual(len(tr), 1)
        self.assertEqual(tr[0]["late_exit"], 1)
        self.assertEqual(tr[0]["exit_ts"], victim["planned_exit_ts"] + HOUR)

    def test_late_bar_blocks_entry(self):
        cs = candles(900, 5, sig_bp=45.0)
        r = self.mk([H1], late_s=300)
        feed_replay(r, "BTC", cs, late=400)
        self.assertEqual(r.conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0], 0)
        reasons = {x[0] for x in r.conn.execute("SELECT DISTINCT reason FROM decisions WHERE action='blocked'")}
        self.assertEqual(reasons, {"late"})

    def test_kill_flag_blocks_new_entries_but_open_positions_close(self):
        cs = candles(1100, 5, sig_bp=45.0)
        r = self.mk([H1])
        feed_replay(r, "BTC", cs[:700])
        n_before = len(r.trades("H1"))
        open(self.kill, "w").close()
        for k in range(700, 1100):
            r.ingest("BTC", cs[k - 1:k + 1], cs[k][0] + 5)
        n_after = len(r.trades("H1"))
        self.assertLessEqual(n_after - n_before, 1)             # nur die zum Zeitpunkt des Flags offene Position
        self.assertEqual(r._open_count(), 0)
        self.assertGreater(r.conn.execute("SELECT COUNT(*) FROM decisions WHERE reason='kill_flag'").fetchone()[0], 0)
        os.remove(self.kill)
        for k in range(1100, 1100):
            pass

    def test_daily_loss_blocks_rest_of_day(self):
        cs = candles(900, 5, sig_bp=45.0)
        r = self.mk([H1], max_daily_loss_bp=0.0001)
        with mock.patch.object(r, "_daily_net", return_value=-5.0):
            feed_replay(r, "BTC", cs)
        self.assertEqual(r.conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0], 0)
        self.assertGreater(r.conn.execute("SELECT COUNT(*) FROM decisions WHERE reason='daily_loss'").fetchone()[0], 0)

    def test_max_open_blocks(self):
        cs = candles(900, 5, sig_bp=45.0)
        r = self.mk([H1], max_open=0)
        feed_replay(r, "BTC", cs)
        self.assertEqual(r.conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0], 0)
        self.assertGreater(r.conn.execute("SELECT COUNT(*) FROM decisions WHERE reason='max_open'").fetchone()[0], 0)

    def test_status_shape(self):
        cs = candles(600, 5)
        r = self.mk([H1]); feed_replay(r, "BTC", cs)
        st = r.status(cs[-1][0] + 60)
        self.assertEqual(st["freeze_hash"], r.fh)
        self.assertEqual(st["age_s"]["BTC"], 60)
        self.assertEqual(st["per_hypothesis"][0]["id"], "H1")


class TestFeedAndLoop(unittest.TestCase):
    OHLC = {"error": [], "result": {"XXBTZUSD": [[1688671200, "30306.1", "30306.2", "30305.7", "30305.7", "30306.1", "3.39", 23],
                                                  [1688674800, "30305.7", "30400.0", "30300.0", "30390.0", "30350", "1.5", 9]], "last": 1688672160}}

    def test_parse_ohlc(self):
        c = feed.parse_ohlc(self.OHLC)
        self.assertEqual(c[0], (1688671200, 30306.1, 30306.2, 30305.7, 30305.7, 3.39))
        self.assertEqual(len(c), 2)
        for bad in ({"error": ["EQuery:Unknown asset pair"]}, {"error": [], "result": {"last": 1}},
                    {"error": [], "result": {"A": [], "B": [], "last": 1}}, {"error": [], "result": {"A": [[1, "x"]]}}):
            with self.assertRaises(feed.FeedError):
                feed.parse_ohlc(bad)

    def test_parse_tickers(self):
        obj = {"result": "success", "tickers": [{"symbol": "PF_XBTUSD", "markPrice": 1.0, "indexPrice": 2.0, "last": 3, "fundingRate": 1e-7, "x": 1},
                                                {"symbol": "OTHER", "markPrice": 9}]}
        self.assertEqual(feed.parse_tickers(obj, ["PF_XBTUSD"]), {"PF_XBTUSD": {"markPrice": 1.0, "indexPrice": 2.0, "last": 3, "fundingRate": 1e-7}})
        with self.assertRaises(feed.FeedError):
            feed.parse_tickers({"result": "error"}, [])

    def test_get_rejects_foreign_url(self):
        with self.assertRaises(feed.FeedError):
            feed._get("https://example.com/x", {})

    def test_next_fetch_ts(self):
        self.assertEqual(loop.next_fetch_ts(3600 * 10 + 5), 3600 * 10 + 20)
        self.assertEqual(loop.next_fetch_ts(3600 * 10 + 20), 3600 * 11 + 20)
        self.assertEqual(loop.next_fetch_ts(3600 * 10 + 3599), 3600 * 11 + 20)

    def test_cycle_retries_logs_errors_and_continues(self):
        with tempfile.TemporaryDirectory() as d, runner.Runner(os.path.join(d, "r.sqlite"), make_doc([H1])) as r:
            cs = candles(430, 1)
            calls = {"n": 0}
            def fetch(asset):
                calls["n"] += 1
                if calls["n"] < 3:
                    raise OSError("netz weg")
                return cs
            sleeps = []
            loop.run_cycle(r, ["BTC"], fetch, lambda: cs[-1][0] + 10, sleeps.append, fetch_tickers=lambda a: {"PF_XBTUSD": {"markPrice": 1}})
            self.assertEqual(calls["n"], 3)
            self.assertEqual(sleeps, [loop.RETRY_S, loop.RETRY_S])
            kinds = [x[0] for x in r.conn.execute("SELECT kind FROM events")]
            self.assertEqual(kinds.count("fetch_error"), 2)
            self.assertIn("basis_log", kinds)
            self.assertEqual(r.conn.execute("SELECT COUNT(*) FROM bars").fetchone()[0], 430)

    def test_all_retries_fail_does_not_raise(self):
        with tempfile.TemporaryDirectory() as d, runner.Runner(os.path.join(d, "r.sqlite"), make_doc([H1])) as r:
            loop.run_cycle(r, ["BTC"], lambda a: (_ for _ in ()).throw(OSError("x")), lambda: 1000, lambda s: None)
            self.assertEqual(r.conn.execute("SELECT COUNT(*) FROM events WHERE kind='fetch_error'").fetchone()[0], loop.RETRIES)

    def test_run_loop_respects_max_cycles(self):
        with tempfile.TemporaryDirectory() as d, runner.Runner(os.path.join(d, "r.sqlite"), make_doc([H1])) as r:
            slept = []
            n = loop.run_loop(r, ["BTC"], lambda a: candles(430, 1), lambda: 3600 * 100 + 25, slept.append, max_cycles=3)
            self.assertEqual(n, 3)
            self.assertTrue(all(s >= 1 for s in slept))


class TestFeedCheck(unittest.TestCase):
    def run_check(self, ohlc, tick):
        import contextlib, io, time
        from lf1 import cli
        buf = io.StringIO()
        with mock.patch.object(feed, "fetch_ohlc", ohlc), mock.patch.object(feed, "fetch_tickers", tick):
            with contextlib.redirect_stdout(buf):
                rc = cli.main(["feed-check"])
        return rc, json.loads(buf.getvalue())

    def good_candles(self):
        import time
        now = int(time.time()) // 3600 * 3600
        return [(now - 3600 * k, 61234.5 + k, 61300.5, 61100.5, 61250.5, 1.0) for k in range(5, -1, -1)]

    def tickers(self, assets, missing=()):
        return {feed.PERP_SYMBOLS[a]: {"markPrice": 61234.5, "indexPrice": 61230.5, "last": 61231.5, "fundingRate": 1e-7}
                for a in assets if a not in missing}

    def test_ok_prints_flags_not_prices(self):
        rc, res = self.run_check(lambda a: self.good_candles(), lambda assets: self.tickers(assets))
        self.assertEqual(rc, 0)
        self.assertTrue(res["ok"])
        self.assertTrue(res["ohlc"]["BTC"]["last_is_current_hour"])
        self.assertEqual(res["ohlc"]["BTC"]["steps_hours"], [1])
        self.assertEqual(res["tickers"]["BTC"]["fields_present"], ["fundingRate", "indexPrice", "last", "markPrice"])
        txt = json.dumps(res)
        for v in ("61234", "61300", "61100", "61250"):
            self.assertNotIn(v, txt)                                 # keine Preise in der Ausgabe

    def test_format_errors_fail_with_exit_7(self):
        def bad(a):
            raise feed.FeedError("kein result")
        rc, res = self.run_check(bad, lambda assets: self.tickers(assets))
        self.assertEqual(rc, 7)
        self.assertFalse(res["ohlc"]["BTC"]["ok"])
        rc, res = self.run_check(lambda a: self.good_candles(), lambda assets: self.tickers(assets, missing=("SOL",)))
        self.assertEqual(rc, 7)
        self.assertFalse(res["tickers"]["SOL"]["found"])
        rc, res = self.run_check(lambda a: self.good_candles(), lambda assets: (_ for _ in ()).throw(feed.FeedError("x")))
        self.assertEqual(rc, 7)
        c = self.good_candles(); c[2] = (c[2][0] + 7, *c[2][1:])     # nicht an der Stunde ausgerichtet
        rc, res = self.run_check(lambda a: c, lambda assets: self.tickers(assets))
        self.assertEqual(rc, 7)
        self.assertFalse(res["ohlc"]["BTC"]["all_hour_aligned"])


class TestShadow(Base):
    def test_shadow_never_enters_but_logs_signals(self):
        cs = candles(900, 5, sig_bp=45.0)
        r = self.mk([H1], shadow=True)
        feed_replay(r, "BTC", cs)
        self.assertEqual(r.conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0], 0)
        self.assertEqual(r.conn.execute("SELECT COUNT(*) FROM positions").fetchone()[0], 0)
        n_sig = r.conn.execute("SELECT COUNT(*) FROM decisions WHERE signal!=0").fetchone()[0]
        n_sh = r.conn.execute("SELECT COUNT(*) FROM decisions WHERE action='blocked' AND reason='shadow'").fetchone()[0]
        self.assertGreater(n_sig, 5)
        self.assertEqual(n_sig, n_sh)                       # jedes Signal ist als shadow gesperrt, keines verschwindet
        self.assertEqual(r.status(10 ** 10)["per_hypothesis"][0]["blocked"], {"shadow": n_sh})

    def test_default_is_not_shadow_and_cli_reads_flag(self):
        import contextlib, io
        from lf1 import cli
        self.assertFalse(self.mk([H1]).shadow)
        cfg = os.path.join(self.tmp.name, "cfg.json"); fz = os.path.join(self.tmp.name, "freeze.json")
        json.dump(make_doc([H1]), open(fz, "w"))
        doc = make_doc([H1])
        db_s, db_p = os.path.join(self.tmp.name, "s.sqlite"), os.path.join(self.tmp.name, "p.sqlite")
        json.dump(cfg_dict(doc, fz, db_s, shadow=True), open(cfg, "w"))
        r, _ = cli._runner_from_config(cfg)
        self._open.append(r)
        self.assertTrue(r.shadow)
        json.dump(cfg_dict(doc, fz, db_p, shadow=False), open(cfg, "w"))
        r2, _ = cli._runner_from_config(cfg)
        self._open.append(r2)
        self.assertFalse(r2.shadow)


class TestBarError(Base):
    def test_bad_bar_is_logged_and_does_not_stall_later_bars(self):
        cs = candles(600, 9, sig_bp=45.0)
        r = self.mk([H1])
        real = r._decide
        bad_ts = cs[500][0]
        def boom(h, asset, t, px_open, recv_ts):
            if t == bad_ts:
                raise ValueError("kaputte Kerze")
            return real(h, asset, t, px_open, recv_ts)
        r._decide = boom
        feed_replay(r, "BTC", cs)
        kinds = [x[0] for x in r.conn.execute("SELECT kind FROM events")]
        self.assertEqual(kinds.count("bar_error"), 1)
        self.assertEqual(r.conn.execute("SELECT kind FROM processed WHERE ts=?", (bad_ts,)).fetchone()[0], "error")
        self.assertEqual(r.conn.execute("SELECT COUNT(*) FROM decisions WHERE bar_ts=?", (bad_ts - 3600,)).fetchone()[0], 0)  # zurueckgerollt
        later = r.conn.execute("SELECT COUNT(*) FROM processed WHERE ts>? AND kind='live'", (bad_ts,)).fetchone()[0]
        self.assertEqual(later, 99)                                    # 600 - 501 Kerzen nach der kaputten laufen weiter
        self.assertIn("bar_error", json.dumps(r.recent_events(50)))

    def test_bad_bar_rolled_back_not_half_applied(self):
        cs = candles(600, 9, sig_bp=45.0)
        r = self.mk([H1])
        real = r._decide
        bad_ts = cs[450][0]
        def boom(h, asset, t, px_open, recv_ts):
            real(h, asset, t, px_open, recv_ts)         # schreibt zuerst, dann Fehler
            if t == bad_ts:
                raise ValueError("nach dem Schreiben")
        r._decide = boom
        feed_replay(r, "BTC", cs)
        self.assertEqual(r.conn.execute("SELECT COUNT(*) FROM decisions WHERE bar_ts=?", (bad_ts - 3600,)).fetchone()[0], 0)
        self.assertEqual(r.conn.execute("SELECT COUNT(*) FROM positions WHERE entry_ts=?", (bad_ts,)).fetchone()[0], 0)


class TestStaticImportBan(unittest.TestCase):
    """S3 3.7: statische Pruefung der Laufzeit-Module gegen verbotene Zugriffe; nur zwei GET-Ziele."""
    PKG = os.path.join(os.path.dirname(__file__), "..", "lf1")
    FORBIDDEN = ["AddOrder", "CancelOrder", "EditOrder", "/private", "API-Key", "API-Sign", "apikey", "api_key", "secret",
                 "hmac", "ccxt", "krakenex", "websocket", "requests", "socket", "subprocess", "getenv", "environ",
                 "POST", "base64", "keyfile", ".pem", ".env"]

    def src(self, name):
        return open(os.path.join(self.PKG, name), encoding="utf-8").read()

    def test_no_forbidden_tokens_in_runtime_modules(self):
        for name in ("runner.py", "feed.py", "loop.py"):
            text = self.src(name)
            for tok in self.FORBIDDEN:
                self.assertNotIn(tok, text, "%s enthaelt %r" % (name, tok))

    def test_only_feed_imports_network_modules(self):
        for name in os.listdir(self.PKG):
            if not name.endswith(".py"):
                continue
            text = self.src(name)
            uses_net = re.search(r"^\s*(import|from)\s+(urllib|http|ssl|ftplib|smtplib)", text, re.M)
            self.assertEqual(bool(uses_net), name == "feed.py", name)

    def test_urls_only_the_two_allowed(self):
        found = set()
        for name in os.listdir(self.PKG):
            if name.endswith(".py"):
                found |= set(re.findall(r"https?://[^\s\"']+", self.src(name)))
        self.assertEqual(found, set(feed.ALLOWED_URLS))

    def test_no_wallclock_or_local_time_in_core_runtime(self):
        for name in ("runner.py", "loop.py"):
            text = self.src(name)
            for tok in ("localtime", "datetime", "time.time", "strftime", "tzinfo"):
                self.assertNotIn(tok, text, "%s: %r" % (name, tok))

    def test_only_get(self):
        self.assertIn('method="GET"', self.src("feed.py"))
        self.assertEqual(len(re.findall(r"\.open\(", self.src("feed.py"))), 1)
        self.assertNotIn("urlopen(", self.src("feed.py"))
        self.assertIn("build_opener(_NoRedirect)", self.src("feed.py"))


if __name__ == "__main__":
    unittest.main()


class TestStatusPage(Base):
    def test_render_escapes_flags_stale_and_has_no_external_resources(self):
        from lf1 import statuspage
        cs = candles(600, 5)
        r = self.mk([H1]); feed_replay(r, "BTC", cs)
        r.conn.execute("INSERT INTO events (ts, kind, detail) VALUES (?,?,?)", (cs[-1][0], "fetch_error", "<script>alert(1)</script>"))
        r.conn.commit()
        fresh = statuspage.render(r.status(cs[-1][0] + 60), r.recent_events())
        stale = statuspage.render(r.status(cs[-1][0] + 5 * 3600), r.recent_events())
        self.assertNotIn("VERALTET", fresh)
        self.assertIn("VERALTET", stale)
        self.assertRegex(stale, r"class=bad>\d+ s VERALTET")
        self.assertNotRegex(fresh, r"class=bad>\d+ s")
        self.assertNotIn("<script", fresh.lower())
        self.assertIn("&lt;script&gt;", fresh)
        self.assertIn(r.fh[:16], fresh)
        self.assertNotRegex(fresh, r"(src|href)\s*=|https?://|@import|url\(")
        open(self.kill, "w").close()
        self.assertIn("KILL-FLAG GESETZT", statuspage.render(r.status(cs[-1][0] + 60)))

    def test_cli_status_html(self):
        import contextlib, io
        from lf1 import cli
        cfg = os.path.join(self.tmp.name, "cfg.json"); fz = os.path.join(self.tmp.name, "freeze.json")
        json.dump(make_doc([H1]), open(fz, "w"))
        json.dump(cfg_dict(make_doc([H1]), fz, self.db), open(cfg, "w"))
        out = os.path.join(self.tmp.name, "s.html")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(cli.main(["paper-status", "--config", cfg, "--html", out]), 6)   # Status legt keine DB an
        self.assertFalse(os.path.exists(self.db))
        self.mk([H1]).close()
        with contextlib.redirect_stdout(buf):
            rc = cli.main(["paper-status", "--config", cfg, "--html", out])
        self.assertEqual(rc, 0)
        self.assertIn("CT109 Paper-Runner", open(out, encoding="utf-8").read())
        json.dump(cfg_dict(make_doc([H1]), fz, os.path.join(self.tmp.name, "other.sqlite")), open(cfg, "w"))
        doc = json.load(open(fz)); doc["payload"]["hypotheses"][0]["asset"] = "ETH"; json.dump(doc, open(fz, "w"))
        with contextlib.redirect_stdout(buf):
            self.assertEqual(cli.main(["paper-status", "--config", cfg]), 6)
