"""paper_runner (S3): vollautomatische interne Simulation. Keine Netzwerk-, Broker- oder Schluesselzugriffe.

Eingang sind nur fertige Stundenkerzen (ts, o, h, l, c, v) und die Empfangszeit. Die Signal- und Kostenlogik
kommt aus lf1.core / lf1.backtest (ein Code). Zustand liegt in SQLite; jede Kerze wird in genau einer
Transaktion verarbeitet (Absturz => Rueckabwicklung => erneute Verarbeitung ohne Doppel-Einstieg).

Zeitregel wie im Backtest: Entscheidung zum Close der Kerze i (Daten <= i), Einstieg zum Open der Kerze i+1,
Ausstieg zum Open der Kerze i+1+H. Alles in UTC-Epochensekunden.
Bekannte, dokumentierte Abweichung: fehlt die Ausstiegskerze, schliesst der Runner zur ersten spaeter
verfuegbaren Kerze (Flag late_exit); der Backtest verwirft so einen Trade. Der Aequivalenztest gilt luckenfrei.
"""
import json
import math
import os
import pathlib
import sqlite3
import sys

import numpy as np

from . import __version__
from .backtest import MAX_HYP, MAX_LOOKBACK, FreezeError, build_signals, cost_for, validate_hypothesis
from .util import code_hash, json_hash

HOUR = 3600
SLICE = MAX_LOOKBACK + 64        # Kerzen Rueckblick fuer die Signalberechnung
DEFAULT_LATE_S = 300             # Kerze muss spaetestens 5 min nach Beginn gesehen werden, sonst kein Einstieg


class StartRefused(Exception):
    pass


def candle_problem(o, h, l, c, v):
    """Gibt None zurueck, wenn die Kerze plausibel ist, sonst den Grund (QA2 M5). Gilt fuer Eingang und Speicherung."""
    try:
        vals = [float(x) for x in (o, h, l, c, v)]
    except (TypeError, ValueError):
        return "not_numeric"
    if not all(math.isfinite(x) for x in vals):
        return "not_finite"
    o, h, l, c, v = vals
    if min(o, h, l, c) <= 0.0:
        return "non_positive_price"
    if v < 0.0:
        return "negative_volume"
    tol = 1e-9 * max(h, 1.0)
    if h < max(o, c) - tol or l > min(o, c) + tol or h < l - tol:
        return "ohlc_inconsistent"
    return None


def verify_start(doc, pkg_dir=None, expected_freeze_hash=None, expected_code_hash=None):
    """Start-Waechter (S3 3.3): Freeze-Hash und Code-Hash muessen passen, Hypothesen muessen gueltig sein.
    Sind expected_* gesetzt (im Betrieb Pflicht, QA2 M1), muessen sie zusaetzlich mit den von aussen festgelegten Werten uebereinstimmen."""
    try:
        payload, fh = doc["payload"], doc["freeze_hash"]
    except (KeyError, TypeError):
        raise StartRefused("Freeze-Datei unvollstaendig")
    if json_hash(payload) != fh:
        raise StartRefused("Freeze-Hash passt nicht zur Nutzlast")
    if payload.get("code_hash") != code_hash(pkg_dir):
        raise StartRefused("Code-Hash weicht vom Freeze ab")
    if expected_freeze_hash is not None and fh != expected_freeze_hash:
        raise StartRefused("Freeze-Hash weicht vom erwarteten (von aussen festgelegten) Wert ab")
    if expected_code_hash is not None and code_hash(pkg_dir) != expected_code_hash:
        raise StartRefused("Code-Hash weicht vom erwarteten (von aussen festgelegten) Wert ab")
    hyps = payload.get("hypotheses", [])
    if not 1 <= len(hyps) <= MAX_HYP:
        raise StartRefused("Hypothesenzahl ausserhalb 1..%d" % MAX_HYP)
    try:
        for h in hyps:
            validate_hypothesis(h)
    except FreezeError as e:
        raise StartRefused(str(e))
    return payload, fh


SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS bars (asset TEXT NOT NULL, ts INTEGER NOT NULL, o REAL, h REAL, l REAL, c REAL, v REAL,
    recv_ts INTEGER NOT NULL, PRIMARY KEY (asset, ts));
CREATE TABLE IF NOT EXISTS processed (asset TEXT NOT NULL, ts INTEGER NOT NULL, kind TEXT NOT NULL, PRIMARY KEY (asset, ts));
CREATE TABLE IF NOT EXISTS decisions (hyp_id TEXT NOT NULL, bar_ts INTEGER NOT NULL, signal INTEGER NOT NULL,
    action TEXT NOT NULL, reason TEXT, recv_ts INTEGER, close_px REAL, PRIMARY KEY (hyp_id, bar_ts));
CREATE TABLE IF NOT EXISTS positions (hyp_id TEXT PRIMARY KEY, dec_ts INTEGER NOT NULL, entry_ts INTEGER NOT NULL,
    planned_exit_ts INTEGER NOT NULL, side INTEGER NOT NULL, entry_px REAL NOT NULL, recv_ts INTEGER);
CREATE TABLE IF NOT EXISTS trades (hyp_id TEXT NOT NULL, dec_ts INTEGER NOT NULL, entry_ts INTEGER NOT NULL,
    exit_ts INTEGER NOT NULL, planned_exit_ts INTEGER NOT NULL, side INTEGER NOT NULL, entry_px REAL NOT NULL,
    exit_px REAL NOT NULL, gross_bp REAL NOT NULL, cost_bp REAL NOT NULL, roundtrip_bp REAL NOT NULL,
    funding_bp REAL NOT NULL, net_bp REAL NOT NULL, late_exit INTEGER NOT NULL, PRIMARY KEY (hyp_id, dec_ts));
CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, ts INTEGER NOT NULL, kind TEXT NOT NULL, detail TEXT);
"""


def open_readonly(db_path, fh):
    """Oeffnet die Runner-Datenbank nur lesend und prueft die Bindung an den Freeze (kein Schreibzugriff, kein Anlegen)."""
    uri = pathlib.Path(db_path).resolve().as_uri() + "?mode=ro"
    try:
        conn = sqlite3.connect(uri, uri=True)
    except sqlite3.Error as e:
        raise StartRefused("Datenbank nicht lesbar: %s" % e)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("SELECT v FROM meta WHERE k='freeze_hash'").fetchone()
        if row is None or row["v"] != fh:
            raise StartRefused("Datenbank gehoert nicht zu diesem Freeze")
    except sqlite3.Error as e:
        conn.close()
        raise StartRefused("Datenbank nicht lesbar: %s" % e)
    except BaseException:
        conn.close()
        raise
    return conn


class Runner:
    def __init__(self, db_path, doc, kill_flag=None, max_daily_loss_bp=None, max_open=2, late_s=DEFAULT_LATE_S, pkg_dir=None,
                 read_only=False, shadow=False, expected_freeze_hash=None, expected_code_hash=None, config_snapshot=None, start_ts=0):
        self._lock = None
        self.payload, self.fh = verify_start(doc, pkg_dir, expected_freeze_hash, expected_code_hash)
        self.hyps = self.payload["hypotheses"]
        self.kill_flag = kill_flag
        self.max_daily_loss_bp = max_daily_loss_bp
        self.max_open = int(max_open)
        self.late_s = int(late_s)
        self.code_hash = code_hash(pkg_dir)
        self.read_only = bool(read_only)
        self.shadow = bool(shadow)       # Schattenbetrieb: Kerzen, Signale und Sperren laufen, es gibt nie einen Einstieg
        if self.read_only:               # Status/Auswertung duerfen den laufenden Runner nie stoeren oder die DB veraendern
            self.conn = open_readonly(db_path, self.fh)
            return
        self._acquire_lock(db_path)
        try:
            self.conn = sqlite3.connect(db_path)
        except BaseException:
            self._release_lock()
            raise
        self.conn.row_factory = sqlite3.Row
        mode = "shadow" if self.shadow else "paper"
        try:
            with self.conn:
                for stmt in SCHEMA.strip().split(";"):
                    if stmt.strip():
                        self.conn.execute(stmt)
                row = self.conn.execute("SELECT v FROM meta WHERE k='freeze_hash'").fetchone()
                if row is not None and row["v"] != self.fh:
                    raise StartRefused("Datenbank gehoert zu einem anderen Freeze (%s)" % row["v"][:12])
                row = self.conn.execute("SELECT v FROM meta WHERE k='mode'").fetchone()
                if row is not None and row["v"] != mode:
                    raise StartRefused("Datenbank gehoert zum Modus %s, Konfiguration verlangt %s (Wechsel nur mit frischer Datenbank)" % (row["v"], mode))
                self.conn.execute("INSERT OR IGNORE INTO meta VALUES ('freeze_hash', ?)", (self.fh,))
                self.conn.execute("INSERT OR IGNORE INTO meta VALUES ('mode', ?)", (mode,))
                self.conn.execute("INSERT OR IGNORE INTO meta VALUES ('created_utc', ?)", (str(int(start_ts)),))
                self.conn.execute("INSERT OR REPLACE INTO meta VALUES ('code_hash', ?)", (self.code_hash,))
                self.conn.execute("INSERT OR REPLACE INTO meta VALUES ('lf1_version', ?)", (__version__,))
                snap = {"mode": mode, "lf1_version": __version__, "code_hash": self.code_hash, "freeze_hash": self.fh,
                        "python": sys.version.split()[0], "numpy": np.__version__, "late_s": self.late_s, "max_open": self.max_open,
                        "max_daily_loss_bp": self.max_daily_loss_bp, "kill_flag": self.kill_flag,
                        "config": config_snapshot}
                self._event(int(start_ts), "start", snap)
        except sqlite3.DatabaseError as e:
            self.conn.close()
            self._release_lock()
            raise StartRefused("Datenbank nicht nutzbar: %s" % e)
        except BaseException:
            self.conn.close()                    # abgelehnter Start darf kein Datei-Handle zuruecklassen (Windows: Sperre)
            self._release_lock()
            raise

    def _acquire_lock(self, db_path):
        """Einzelinstanz-Schutz (QA2 m4): exklusive Sperre auf <db>.lock; nur wo fcntl existiert (Linux), sonst ohne."""
        try:
            import fcntl
        except ImportError:
            return
        fh = open(str(db_path) + ".lock", "a")
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            fh.close()
            raise StartRefused("zweiter Runner-Prozess auf derselben Datenbank")
        self._lock = fh

    def _release_lock(self):
        if self._lock is not None:
            try:
                self._lock.close()
            finally:
                self._lock = None

    def close(self):
        self.conn.close()
        self._release_lock()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False

    # ------------------------------------------------------------------ Hilfen
    def _event(self, ts, kind, detail=None):
        self.conn.execute("INSERT INTO events (ts, kind, detail) VALUES (?,?,?)",
                          (int(ts), kind, json.dumps(detail, sort_keys=True) if detail is not None else None))

    def _grid(self, asset, t_last, n=SLICE):
        """Gitter der n Kerzen mit der letzten bei t_last; fehlende = NaN. Gibt (grid, Anzahl vorhandener Kerzen, frueheste ts)."""
        s0 = t_last - HOUR * (n - 1)
        rows = self.conn.execute("SELECT ts,o,h,l,c FROM bars WHERE asset=? AND ts>=? AND ts<=? ORDER BY ts",
                                 (asset, s0, t_last)).fetchall()
        g = {k: np.full(n, np.nan) for k in "ohlc"}
        for r in rows:
            j = (r["ts"] - s0) // HOUR
            if (r["ts"] - s0) % HOUR == 0:
                g["o"][j], g["h"][j], g["l"][j], g["c"][j] = r["o"], r["h"], r["l"], r["c"]
        first = self.conn.execute("SELECT MIN(ts) AS m FROM bars WHERE asset=?", (asset,)).fetchone()["m"]
        return g, first, s0

    def _open_count(self):
        return self.conn.execute("SELECT COUNT(*) AS n FROM positions").fetchone()["n"]

    def _daily_net(self, ts):
        day = ts // 86400
        r = self.conn.execute("SELECT COALESCE(SUM(net_bp),0) AS s FROM trades WHERE exit_ts/86400=?", (day,)).fetchone()
        return float(r["s"])

    # ------------------------------------------------------------------ Eingang
    def _decided(self, asset, ts):
        ids = [h["id"] for h in self.hyps if h["asset"] == asset]
        if not ids:
            return False
        q = "SELECT 1 FROM decisions WHERE bar_ts=? AND hyp_id IN (%s) LIMIT 1" % ",".join("?" * len(ids))
        return self.conn.execute(q, [int(ts)] + ids).fetchone() is not None

    def ingest(self, asset, candles, recv_ts):
        """candles: Liste (ts, o, h, l, c, v), aufsteigend; die letzte darf die laufende Kerze sein.
        Nicht stundengenaue, zukuenftige (ts > Beginn der aktuellen Stunde) und unplausible Kerzen werden nicht gespeichert (QA2 B1/M5)."""
        recv_ts = int(recv_ts)
        cur_open = recv_ts // HOUR * HOUR
        cs = []
        with self.conn:
            if not candles:
                self._event(recv_ts, "empty_candles", {"asset": asset})
            for cd in sorted(candles, key=lambda x: x[0]):
                ts, o, h, l, c, v = cd
                ts = int(ts)
                if ts % HOUR != 0:
                    self._event(recv_ts, "bad_ts", {"asset": asset, "ts": ts})
                    continue
                if ts > cur_open:
                    self._event(recv_ts, "future_bar", {"asset": asset, "ts": ts, "cur_open": cur_open})
                    continue
                why = candle_problem(o, h, l, c, v)
                if why is not None:
                    self._event(recv_ts, "bad_candle", {"asset": asset, "ts": ts, "why": why})
                    continue
                cs.append((ts, o, h, l, c, v))
                cur = self.conn.execute("SELECT o,h,l,c FROM bars WHERE asset=? AND ts=?", (asset, ts)).fetchone()
                if cur is None:
                    self.conn.execute("INSERT INTO bars VALUES (?,?,?,?,?,?,?,?)", (asset, ts, o, h, l, c, v, recv_ts))
                else:
                    if abs(cur["o"] - o) > 1e-9 * max(abs(o), 1.0):
                        self._event(recv_ts, "open_changed", {"asset": asset, "ts": ts, "old": cur["o"], "new": o})
                    if any(abs(cur[k] - x) > 1e-9 * max(abs(x), 1.0) for k, x in (("h", h), ("l", l), ("c", c))) and self._decided(asset, ts):
                        self._event(recv_ts, "bar_revised", {"asset": asset, "ts": ts, "old": [cur["h"], cur["l"], cur["c"]], "new": [h, l, c]})
                    self.conn.execute("UPDATE bars SET h=?, l=?, c=?, v=? WHERE asset=? AND ts=?", (h, l, c, v, asset, ts))
        done = {r["ts"] for r in self.conn.execute("SELECT ts FROM processed WHERE asset=?", (asset,))}
        last_done = max(done) if done else None
        for ts, *_ in cs:
            if ts in done:
                continue
            if last_done is None:
                self._mark(asset, ts, "warmup")
            elif ts < last_done:
                self._mark(asset, ts, "backfilled")
            else:
                try:
                    self._on_bar(asset, ts, recv_ts)
                except (sqlite3.OperationalError, OSError):
                    raise                   # voruebergehender Plattenfehler/Sperre: Zyklus abbrechen, Kerze bleibt unverarbeitet und wird wiederholt (QA2 m2)
                except Exception as e:      # eine unverarbeitbare Kerze darf den unbeaufsichtigten Lauf nicht dauerhaft blockieren
                    with self.conn:
                        self._event(recv_ts, "bar_error", {"asset": asset, "ts": ts, "err": type(e).__name__ + ": " + str(e)[:200]})
                    self._mark(asset, ts, "error")
                last_done = ts
            done.add(ts)

    def _mark(self, asset, ts, kind):
        with self.conn:
            self.conn.execute("INSERT OR IGNORE INTO processed VALUES (?,?,?)", (asset, ts, kind))

    # ------------------------------------------------------------------ Verarbeitung einer neuen Kerze t
    def _on_bar(self, asset, t, recv_ts):
        with self.conn:
            prev = self.conn.execute("SELECT MAX(ts) AS m FROM processed WHERE asset=?", (asset,)).fetchone()["m"]
            self.conn.execute("INSERT INTO processed VALUES (?,?,?)", (asset, t, "live"))
            if prev is not None and t - prev > HOUR:
                self._event(recv_ts, "gap", {"asset": asset, "missing": (t - prev) // HOUR - 1, "from": prev, "to": t})
            bar = self.conn.execute("SELECT o FROM bars WHERE asset=? AND ts=?", (asset, t)).fetchone()
            px_open = float(bar["o"])
            for idx, h in enumerate(self.hyps):
                if h["asset"] != asset:
                    continue
                self._exit_if_due(h, t, px_open)
                self._decide(h, asset, t, px_open, recv_ts)
            self._event(recv_ts, "heartbeat", {"asset": asset, "bar_ts": t, "open_positions": self._open_count()})

    def _exit_if_due(self, h, t, px_open):
        pos = self.conn.execute("SELECT * FROM positions WHERE hyp_id=?", (h["id"],)).fetchone()
        if pos is None or t < pos["planned_exit_ts"]:
            return
        cost = cost_for(h["asset"])
        hold_h = h["H"]
        rt = cost.mult * cost.roundtrip_bp
        fund = cost.mult * cost.funding_bp_per_8h * hold_h / 8.0
        cb = cost.cost_bp(hold_h)
        gross = pos["side"] * (px_open / pos["entry_px"] - 1.0) * 1e4
        late = 1 if t > pos["planned_exit_ts"] else 0
        self.conn.execute("INSERT INTO trades VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                          (h["id"], pos["dec_ts"], pos["entry_ts"], t, pos["planned_exit_ts"], pos["side"], pos["entry_px"],
                           px_open, gross, cb, rt, fund, gross - cb, late))
        self.conn.execute("DELETE FROM positions WHERE hyp_id=?", (h["id"],))

    def _decide(self, h, asset, t, px_open, recv_ts):
        i_ts = t - HOUR
        g, first, s0 = self._grid(asset, i_ts)
        warm = first is not None and first <= s0
        sig = 0
        close_px = float(g["c"][-1]) if np.isfinite(g["c"][-1]) else None
        if warm:
            sig = int(build_signals(h, g)[-1])
        action, reason = "none", None
        if not warm:
            action, reason = "blocked", "warmup"
        elif sig != 0:
            if self.conn.execute("SELECT 1 FROM positions WHERE hyp_id=?", (h["id"],)).fetchone() is not None:
                action = "skip_open"
            else:
                reason = self._block_reason(t, recv_ts)
                if reason is None and (not np.isfinite(px_open) or px_open <= 0):
                    reason = "bad_price"
                if reason is None:
                    action = "enter"
                    self.conn.execute("INSERT INTO positions VALUES (?,?,?,?,?,?,?)",
                                      (h["id"], i_ts, t, t + HOUR * h["H"], sig, px_open, recv_ts))
                else:
                    action = "blocked"
        self.conn.execute("INSERT OR IGNORE INTO decisions VALUES (?,?,?,?,?,?,?)", (h["id"], i_ts, sig, action, reason, recv_ts, close_px))

    def _block_reason(self, t, recv_ts):
        if self.shadow:
            return "shadow"
        if recv_ts - t > self.late_s:
            return "late"
        if self.kill_flag and os.path.exists(self.kill_flag):
            return "kill_flag"
        if self.max_daily_loss_bp is not None and self._daily_net(t) <= -abs(self.max_daily_loss_bp):
            return "daily_loss"
        if self._open_count() >= self.max_open:
            return "max_open"
        return None

    # ------------------------------------------------------------------ Ausgabe
    def trades(self, hyp_id=None):
        q = "SELECT * FROM trades" + (" WHERE hyp_id=?" if hyp_id else "") + " ORDER BY hyp_id, dec_ts"
        return [dict(r) for r in self.conn.execute(q, (hyp_id,) if hyp_id else ())]

    def recent_events(self, n=15):
        return [dict(r) for r in self.conn.execute(
            "SELECT ts, kind, detail FROM events WHERE kind!='heartbeat' ORDER BY id DESC LIMIT ?", (int(n),))]

    def status(self, now_ts):
        c = self.conn
        last = {r["asset"]: r["m"] for r in c.execute("SELECT asset, MAX(ts) AS m FROM bars GROUP BY asset")}
        per = []
        for h in self.hyps:
            r = c.execute("SELECT COUNT(*) AS n, COALESCE(SUM(net_bp),0) AS s FROM trades WHERE hyp_id=?", (h["id"],)).fetchone()
            blocked = {x["reason"]: x["n"] for x in c.execute(
                "SELECT reason, COUNT(*) AS n FROM decisions WHERE hyp_id=? AND action='blocked' GROUP BY reason", (h["id"],))}
            per.append({"id": h["id"], "trades": r["n"], "net_sum_bp": float(r["s"]), "blocked": blocked})
        gaps = c.execute("SELECT COUNT(*) AS n FROM events WHERE kind='gap'").fetchone()["n"]
        assets = sorted({h["asset"] for h in self.hyps})
        errs = c.execute("SELECT COUNT(*) AS n FROM events WHERE ts>=? AND kind IN "
                         "('fetch_error','bar_error','bad_candle','future_bar','bad_ts','empty_candles','ticker_error')",
                         (int(now_ts) - 86400,)).fetchone()["n"]
        mode = c.execute("SELECT v FROM meta WHERE k='mode'").fetchone()
        return {"mode": mode["v"] if mode else None, "missing_assets": [a for a in assets if a not in last], "errors_24h": int(errs),
                "freeze_hash": self.fh, "code_hash": self.code_hash, "lf1_version": __version__, "now_ts": int(now_ts),
                "last_bar_ts": last, "age_s": {a: int(now_ts) - t for a, t in last.items()},
                "open_positions": self._open_count(), "per_hypothesis": per, "gap_events": gaps,
                "kill_flag": bool(self.kill_flag and os.path.exists(self.kill_flag))}

    def freshness_problem(self, now_ts, max_age_s):
        """Gibt None zurueck, wenn jedes Asset der Hypothesen eine Kerze hat und das Alter in [0, max_age_s] liegt (QA2 M3), sonst den Grund."""
        st = self.status(now_ts)
        if st["missing_assets"]:
            return "keine Kerze fuer %s" % ",".join(st["missing_assets"])
        for a, age in sorted(st["age_s"].items()):
            if age < 0:
                return "negatives Kerzenalter bei %s (%d s)" % (a, age)
            if age > max_age_s:
                return "Kerzenalter bei %s: %d s > %d s" % (a, age, max_age_s)
        return None
