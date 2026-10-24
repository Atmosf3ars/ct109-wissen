"""paper-eval: Offline-Auswertung der Runner-Datenbank (Spec v2 V2.6a). Rein lesend, rein beschreibend.

Der Runner speichert Kerzen, Entscheidungen und Trades. Hier werden dieselben Funktionen wie im Backtest benutzt
(Bootstrap, Placebo-Zwillinge mit festen Seeds aus dem Freeze-Hash, Trade-Simulation), damit gilt: ein Code.
Es gibt bewusst **keine Kategorie** (BESTAETIGT usw.): Paper-Daten sind Vorwaertsdaten mit kleinem n und ersetzen
keine Bestaetigung. Zusaetzlich wird der Runner gegen den Backtest auf denselben gespeicherten Kerzen verglichen.
"""
import numpy as np

from . import __version__, core
from .backtest import _rng, block_bootstrap, block_len, cost_for, placebo_means, top_share, trades_for
from .runner import HOUR, open_readonly, verify_start
from .util import code_hash

EQ_TOL = 1e-6
NBOOT = 5000
NPLACEBO = 1000
LABEL = "BESCHREIBEND: Paper-Vorwaertsdaten, keine Bestaetigung, keine Kategorie (Spec v2 V2.6a)"


def _grid(conn, asset):
    rows = conn.execute("SELECT ts,o,h,l,c FROM bars WHERE asset=? ORDER BY ts", (asset,)).fetchall()
    if not rows:
        return None, None
    t0, t1 = rows[0]["ts"], rows[-1]["ts"]
    n = (t1 - t0) // HOUR + 1
    g = {k: np.full(n, np.nan) for k in "ohlc"}
    for r in rows:
        if (r["ts"] - t0) % HOUR == 0:
            j = (r["ts"] - t0) // HOUR
            g["o"][j], g["h"][j], g["l"][j], g["c"][j] = r["o"], r["h"], r["l"], r["c"]
    return g, t0


def _runner_trades(conn, hyp_id, t0):
    rows = conn.execute("SELECT * FROM trades WHERE hyp_id=? ORDER BY dec_ts", (hyp_id,)).fetchall()
    arr = np.zeros(len(rows), dtype=core.TRADE_DTYPE)
    for k, r in enumerate(rows):
        arr[k] = ((r["dec_ts"] - t0) // HOUR, (r["entry_ts"] - t0) // HOUR, (r["exit_ts"] - t0) // HOUR, r["side"],
                  r["entry_px"], r["exit_px"], r["gross_bp"], r["cost_bp"], r["net_bp"])
    return arr, [r["late_exit"] for r in rows]


def _count(conn, sql, args=()):
    return int(conn.execute(sql, args).fetchone()[0])


def _equivalence(h, grid, window, rt, late):
    """Vergleich Runner gegen Backtest auf denselben gespeicherten Kerzen (nur Trades ohne late_exit)."""
    keep = np.array([x == 0 for x in late], dtype=bool) if len(late) else np.zeros(0, dtype=bool)
    rt = rt[keep]
    bt_tr = trades_for(h, grid, [window], cost_for(h["asset"]), 0)
    r_idx = {int(x): k for k, x in enumerate(rt["i_dec"])}
    b_idx = {int(x): k for k, x in enumerate(bt_tr["i_dec"])}
    both = sorted(set(r_idx) & set(b_idx))
    diff = max((abs(float(rt["net_bp"][r_idx[i]]) - float(bt_tr["net_bp"][b_idx[i]])) for i in both), default=0.0)
    return {"n_runner": len(r_idx), "n_backtest": len(b_idx), "matched": len(both),
            "only_runner": len(set(r_idx) - set(b_idx)), "only_backtest": len(set(b_idx) - set(r_idx)),
            "max_abs_net_diff_bp": float(diff)}


def evaluate_paper(db_path, doc, nboot=NBOOT, nplacebo=NPLACEBO, pkg_dir=None):
    payload, fh = verify_start(doc, pkg_dir)           # StartRefused bei Hash-Abweichung
    conn = open_readonly(db_path, fh)                  # nur lesend, an den Freeze gebunden
    try:
        meta = {r["k"]: r["v"] for r in conn.execute("SELECT k,v FROM meta")}
        out = {"tool": "lf1.paper-eval", "lf1_version": __version__, "code_hash": code_hash(pkg_dir), "freeze_hash": fh,
               "db_code_hash": meta.get("code_hash"), "db_lf1_version": meta.get("lf1_version"), "label": LABEL,
               "hypotheses": []}
        for idx, h in enumerate(payload["hypotheses"]):
            out["hypotheses"].append(_one(conn, idx, h, fh, nboot, nplacebo))
        return out
    finally:
        conn.close()


def _one(conn, idx, h, fh, nboot, nplacebo):
    hid, asset = h["id"], h["asset"]
    res = {"id": hid, "asset": asset, "H": h["H"]}
    grid, t0 = _grid(conn, asset)
    live = conn.execute("SELECT MIN(ts) AS a, MAX(ts) AS b, COUNT(*) AS n FROM processed WHERE asset=? AND kind='live'", (asset,)).fetchone()
    if grid is None or live["n"] == 0:
        res["status"] = "keine Live-Kerzen"
        return res
    n = len(grid["o"])
    s = max(0, (live["a"] - HOUR - t0) // HOUR)           # erste Entscheidung = Kerze vor der ersten Live-Kerze
    window = (int(s), int(n))
    rt, late = _runner_trades(conn, hid, t0)
    blocked = {r["reason"]: r["n"] for r in conn.execute(
        "SELECT reason, COUNT(*) AS n FROM decisions WHERE hyp_id=? AND action='blocked' GROUP BY reason", (hid,))}
    events = {r["kind"]: r["n"] for r in conn.execute("SELECT kind, COUNT(*) AS n FROM events GROUP BY kind")}
    res.update({"first_live_bar_ts": int(live["a"]), "last_bar_ts": int(t0 + HOUR * (n - 1)), "live_bars": int(live["n"]),
                "missing_bars_in_window": int(np.isnan(grid["o"][window[0]:window[1]]).sum()),
                "n_trades": int(len(rt)), "n_late_exit": int(sum(late)), "blocked_decisions": blocked,
                "gap_events": int(events.get("gap", 0)), "open_changed_events": int(events.get("open_changed", 0)), "bar_error_events": int(events.get("bar_error", 0)),
                "fetch_errors": int(events.get("fetch_error", 0)),
                "open_position": _count(conn, "SELECT COUNT(*) FROM positions WHERE hyp_id=?", (hid,)) > 0})
    # Aequivalenz Runner = Backtest (nur aussagekraeftig, wenn nichts Betriebliches eingegriffen hat)
    eq = _equivalence(h, grid, window, rt, late)
    why = [k for k, v in (("Luecken", res["missing_bars_in_window"] or res["gap_events"]), ("Sperren", bool(blocked)),
                          ("late_exit", res["n_late_exit"]), ("Open-Aenderungen", res["open_changed_events"]),
                          ("Kerzenfehler", res["bar_error_events"])) if v]
    eq["applicable"] = not why
    eq["not_applicable_because"] = why
    eq["equal"] = bool(eq["applicable"] and eq["only_runner"] == 0 and eq["only_backtest"] == 0 and eq["max_abs_net_diff_bp"] < EQ_TOL)
    res["equivalence"] = eq
    if len(rt) < 2:
        res["status"] = "zu wenige Trades fuer Statistik (n=%d)" % len(rt)
        return res
    net = rt["net_bp"].astype(float)
    bl = block_len(h["H"], rt, [window])
    bb = block_bootstrap(net, bl, nboot, _rng(fh, idx, 11))
    res.update({"net_mean_bp": float(net.mean()), "gross_mean_bp": float(rt["gross_bp"].mean()), "block_len_trades": bl,
                "p_one_sided": bb["p"], "lcb95_bp": bb["lcb95"], "top5_share": top_share(net),
                "n_long": int((rt["side"] > 0).sum()), "n_short": int((rt["side"] < 0).sum())})
    pm = placebo_means(h, grid, [window], rt, cost_for(asset), 0, nplacebo, _rng(fh, idx, 12))
    if pm is None:
        res["placebo"] = None
    else:
        m = float(net.mean())
        res["placebo"] = {"n_sim": int(len(pm)), "q95_bp": float(np.quantile(pm, 0.95)), "mean_bp": float(pm.mean()),
                          "p_ge_live": float((np.sum(pm >= m) + 1) / (len(pm) + 1)), "live_above_q95": bool(m > np.quantile(pm, 0.95))}
    res["status"] = "ok"
    return res
