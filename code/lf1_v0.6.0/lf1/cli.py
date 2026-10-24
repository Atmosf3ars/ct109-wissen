"""Kommandozeile fuer Andis PC. Alle Ausgaben: nur Aggregate (JSON), nie Rohdaten.

  python -m lf1 selfcheck --spec GATE_SPEC_v1.md
  python -m lf1 file-q  --zip Kraken_OHLCVT_Full.zip --out out
  python -m lf1 regime  --zip Kraken_OHLCVT_Full.zip --out out
  python -m lf1 window-q --zip Kraken_OHLCVT_Full.zip --regime out/regime_selection.json --out out [--window A]
  python -m lf1 gate    --zip Kraken_OHLCVT_Full.zip --regime out/regime_selection.json --spec GATE_SPEC_v1.md --out out
  python -m lf1 epoch-q --zip Kraken_OHLCVT_Full.zip --regime out/regime_selection.json --out out --assets BTC   (Spec v2 V2.2: nur Zaehler je Epoche)
  python -m lf1 freeze  --zip Kraken_OHLCVT_Full.zip --regime out/regime_selection.json --gate out/gate_result_A.json
                        --hyps hypotheses.json --bau-spec BAU_SPEC_S1S3_v1.md --out out        (schreibt out/freeze.json, einmalig)
  python -m lf1 paper-run --config runner_config.json [--once]     (Runner, nur oeffentliche GET-Abrufe, keine Schluessel)
  python -m lf1 paper-status --config runner_config.json            (Status als JSON)
  python -m lf1 feed-check                                          (ein Abruf je Quelle, nur Formatpruefung, keine Werte; kein Schreiben)
  python -m lf1 paper-eval --config runner_config.json --out out   (Offline-Auswertung der Runner-DB, nur lesend, beschreibend)
  python -m lf1 backtest --zip Kraken_OHLCVT_Full.zip --regime out/regime_selection.json --freeze out/freeze.json
                        --stage discovery_A --out out                                           (einmalig je Stufe)
"""
import argparse
import json
import os
import sys

import numpy as np

from . import __version__
from . import backtest as bt
from .data import DataError, Source, load_bars, to_grid
from .gate import GateError, run_gate
from .quality import check_file, check_window
from .regime import CUTOFF, select_regimes, window_bounds_utc
from .util import SPEC_SHA256, check_spec, code_hash, json_hash, sha256_bytes


def _dump(obj, path=None):
    s = json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False)
    if path:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(s + "\n")
    print(s)


def cmd_selfcheck(a):
    out = {
        "lf1_version": __version__,
        "code_hash": code_hash(),
        "python": sys.version.split()[0],
        "numpy": np.__version__,
    }
    if a.spec:
        out["spec_check"] = check_spec(a.spec)
    _dump(out)
    return 0 if (not a.spec or out["spec_check"]["ok"]) else 2


def cmd_file_q(a):
    res = {"tool": "lf1.file-q", "code_hash": code_hash(), "files": []}
    with Source(a.zip) as src:
        for asset, iv in (("BTC", 1440), ("BTC", 60), ("ETH", 60), ("SOL", 60)):
            res["files"].append(check_file(load_bars(src, asset, iv)))
    _dump(res, os.path.join(a.out, "q_files.json"))
    return 0


def cmd_regime(a):
    with Source(a.zip) as src:
        bars = load_bars(src, "BTC", 1440)
    order = np.argsort(bars.ts)
    reg = select_regimes(bars.ts[order], bars.c[order], cutoff=a.cutoff, input_sha256=bars.sha256)
    reg["code_hash"] = code_hash()
    _dump(reg, os.path.join(a.out, "regime_selection.json"))
    print("REGIME_HASH %s" % reg["hash_sha256"])
    return 0 if reg["status"] == "OK" else 3


def cmd_window_q(a):
    with open(a.regime, encoding="utf-8") as f:
        reg = json.load(f)
    if reg.get("status") != "OK":
        print("Regimewahl BLOCKED")
        return 3
    t0, t1 = window_bounds_utc(reg, a.window)
    res = {"tool": "lf1.window-q", "window": a.window, "bounds": reg[a.window], "quality": []}
    with Source(a.zip) as src:
        for asset in ("BTC", "ETH", "SOL"):
            res["quality"].append(check_window(load_bars(src, asset, 60), t0, t1))
    res["all_pass"] = all(q["passes"] for q in res["quality"])
    _dump(res, os.path.join(a.out, "q_window_%s.json" % a.window))
    return 0


def cmd_gate(a):
    with open(a.regime, encoding="utf-8") as f:
        reg = json.load(f)
    with Source(a.zip) as src:
        try:
            res = run_gate(src, reg, a.window, a.spec, a.out, freeze_hash=a.freeze_hash)
        except GateError as e:
            print("GATE ABGELEHNT: %s" % e)
            return 4
    _dump(res)
    return 0


def _assets_of(hyps):
    out = []
    for h in hyps:
        if h["asset"] not in out:
            out.append(h["asset"])
    return out


def _manifest(src, assets):
    man = []
    for asset in assets:
        b = load_bars(src, asset, 60)
        man.append({"asset": asset, "member": b.member, "bytes": int(b.nbytes), "sha256": b.sha256})
    return man


def _grids_for_window(src, assets, t0, t1):
    """Gitter [t0 - Vorlauf, t1); Fenster = [(Vorlauf, n)]. Gleiche Konstruktion fuer Freeze-Pruefung und Lauf."""
    pre = bt.MAX_LOOKBACK * 3600
    grids, windows = {}, {}
    for asset in assets:
        o, h, l, c, _v, _p = to_grid(load_bars(src, asset, 60), t0 - pre, t1)
        grids[asset] = {"o": o, "h": h, "l": l, "c": c}
        windows[asset] = [(bt.MAX_LOOKBACK, len(o))]
    return grids, windows


def _e_inputs(src, asset, a0):
    """Gitter und Epochenangaben fuer E (Spec v2 V2.2) eines Assets: (grid, wins, split, n, t0g, first, quality)."""
    first = int(load_bars(src, asset, 60).ts.min())
    g, w = _grids_for_window(src, [asset], first, a0)
    grid, wins = g[asset], w[asset]
    t0g = first - bt.MAX_LOOKBACK * 3600
    n = len(grid["o"])
    split = bt.split_index(t0g, n)
    q = bt.epoch_quality(np.isfinite(grid["o"]), wins, split)
    return grid, wins, split, n, t0g, first, q


def cmd_epoch_q(a):
    """Q-Pflicht V2.2: nur Zaehler je Epoche, keine Signale, keine Renditen."""
    with open(a.regime, encoding="utf-8") as f:
        reg = json.load(f)
    a0, _a1 = window_bounds_utc(reg, "A")
    res = {"tool": "lf1.epoch-q", "code_hash": code_hash(), "regime_hash": reg.get("hash_sha256"),
           "e_end_ts_exclusive": int(a0), "assets": {}}
    with Source(a.zip) as src:
        for asset in a.assets:
            _g, _w, split, n, t0g, first, q = _e_inputs(src, asset, a0)
            res["assets"][asset] = {"first_ts": first, "grid_bars": n, "split_idx": split, "quality": q}
    _dump(res, os.path.join(a.out, "q_epochs.json"))
    return 0


def cmd_freeze(a):
    out_path = os.path.join(a.out, "freeze.json")
    if os.path.exists(out_path):
        print("FREEZE ABGELEHNT: %s existiert bereits (Einfrieren ist einmalig)" % out_path)
        return 4
    with open(a.regime, encoding="utf-8") as f:
        reg = json.load(f)
    with open(a.gate, encoding="utf-8") as f:
        gate = json.load(f)
    with open(a.hyps, encoding="utf-8") as f:
        hyps = json.load(f)
    if reg.get("status") != "OK" or gate.get("summary", {}).get("lf1_status") != "ZULAESSIG":
        print("FREEZE ABGELEHNT: Regime oder Gate nicht OK")
        return 4
    if gate.get("window") != "A" or gate.get("regime_hash") != reg.get("hash_sha256"):
        print("FREEZE ABGELEHNT: Gate-Ergebnis passt nicht zur Regimewahl")
        return 4
    with open(a.bau_spec, "rb") as f:
        raw = f.read()
    spec_h = sha256_bytes(raw.replace(b"\r\n", b"\n"))
    try:
        with Source(a.zip) as src:
            man = _manifest(src, _assets_of(hyps))
        payload, fh = bt.make_freeze(hyps, gate, reg["hash_sha256"], spec_h, {"A": reg["A"]}, man)
    except bt.FreezeError as e:
        print("FREEZE ABGELEHNT: %s" % e)
        return 4
    doc = {"freeze_hash": fh, "payload": payload}
    _dump(doc, out_path)
    print("FREEZE_HASH %s" % fh)
    return 0


def cmd_backtest(a):
    with open(a.regime, encoding="utf-8") as f:
        reg = json.load(f)
    with open(a.freeze, encoding="utf-8") as f:
        doc = json.load(f)
    payload, fh = doc["payload"], doc["freeze_hash"]
    if json_hash(payload) != fh:
        print("BACKTEST ABGELEHNT: Freeze-Datei veraendert")
        return 4
    if payload["regime_hash"] != reg.get("hash_sha256"):
        print("BACKTEST ABGELEHNT: Regimewahl passt nicht zum Freeze")
        return 4
    assets = _assets_of(payload["hypotheses"])
    a0, a1 = window_bounds_utc(reg, "A")
    extras = None
    with Source(a.zip) as src:
        if _manifest(src, assets) != [m for m in payload["data_manifest"] if m["asset"] in assets]:
            print("BACKTEST ABGELEHNT: Daten weichen vom Freeze ab (C6)")
            return 4
        if a.stage == "confirm":
            grids, windows, extras = {}, {}, {"cost_factor": {}, "split_idx": {}, "epoch_quality": {}, "window_e": {}}
            for asset in assets:
                grid, wins, split, n, t0g, first, q = _e_inputs(src, asset, a0)
                extras["epoch_quality"][asset] = q
                extras["window_e"][asset] = {"first_ts": first, "end_ts_exclusive": int(t0g + n * 3600), "grid_start_ts": t0g}
                if not q["E2"]["valid"]:
                    print("BACKTEST ABGELEHNT: Epoche E2 fuer %s ungueltig (%s); Entscheid ueber Fenster vor dem Lauf noetig" % (asset, q["E2"]["reason"]))
                    return 4
                if not q["E1"]["valid"]:
                    wins = [(max(wins[0][0], split), wins[0][1])]
                grids[asset], windows[asset] = grid, wins
                extras["cost_factor"][asset] = bt.epoch_cost_factor(n, t0g)
                extras["split_idx"][asset] = split
        else:
            grids, windows = _grids_for_window(src, assets, a0, a1)
    try:
        res = bt.run_stage(a.stage, payload, fh, grids, windows, a.out, extras=extras)
    except bt.FreezeError as e:
        print("BACKTEST ABGELEHNT: %s" % e)
        return 4
    _dump(res)
    return 0


CONFIG_FIELDS = ("freeze", "db", "kill_flag", "max_daily_loss_bp", "max_open", "late_s", "shadow", "expected_freeze_hash", "expected_code_hash")


def _validate_config(cfg):
    """Strenge Pruefung der Runner-Konfiguration (QA2 M2): genau diese Felder, alle Pflicht, richtige Typen.
    Ein Tippfehler darf keine Sicherung stillschalten, ein fehlendes Feld darf nicht Paper statt Schatten bedeuten."""
    from .runner import StartRefused
    if not isinstance(cfg, dict):
        raise StartRefused("Konfiguration ist kein Objekt")
    unknown = sorted(set(cfg) - set(CONFIG_FIELDS))
    missing = sorted(set(CONFIG_FIELDS) - set(cfg))
    if unknown or missing:
        raise StartRefused("Konfiguration: unbekannte Felder %s, fehlende Felder %s" % (unknown, missing))
    for k in ("freeze", "db", "kill_flag"):
        if not isinstance(cfg[k], str) or not cfg[k]:
            raise StartRefused("Konfiguration: %s muss ein nichtleerer Text sein" % k)
    if not isinstance(cfg["shadow"], bool):
        raise StartRefused("Konfiguration: shadow muss true oder false sein")
    for k in ("max_open", "late_s"):
        if isinstance(cfg[k], bool) or not isinstance(cfg[k], int) or cfg[k] < 1:
            raise StartRefused("Konfiguration: %s muss eine ganze Zahl >= 1 sein" % k)
    v = cfg["max_daily_loss_bp"]
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not v > 0:
        raise StartRefused("Konfiguration: max_daily_loss_bp muss eine Zahl > 0 sein")
    for k in ("expected_freeze_hash", "expected_code_hash"):
        if not isinstance(cfg[k], str) or len(cfg[k]) != 64 or any(ch not in "0123456789abcdef" for ch in cfg[k]):
            raise StartRefused("Konfiguration: %s muss ein 64-stelliger kleingeschriebener Hex-Hash sein" % k)


def _runner_from_config(path, read_only=False):
    import time
    from .runner import Runner, StartRefused
    cfg = None
    try:
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
        _validate_config(cfg)
        with open(cfg["freeze"], encoding="utf-8") as f:
            doc = json.load(f)
        r = Runner(cfg["db"], doc, kill_flag=cfg["kill_flag"], max_daily_loss_bp=cfg["max_daily_loss_bp"],
                   max_open=cfg["max_open"], late_s=cfg["late_s"], read_only=read_only, shadow=cfg["shadow"],
                   expected_freeze_hash=cfg["expected_freeze_hash"], expected_code_hash=cfg["expected_code_hash"],
                   config_snapshot=cfg, start_ts=int(time.time()))
    except StartRefused as e:
        print("RUNNER START VERWEIGERT: %s" % e)
        return None, cfg
    except (OSError, ValueError) as e:        # Datei fehlt/unlesbar, kein gueltiges JSON
        print("RUNNER START VERWEIGERT: Konfiguration oder Freeze nicht lesbar: %s" % type(e).__name__)
        return None, cfg
    return r, cfg


def cmd_paper_run(a):
    import time
    from . import feed, loop
    r, cfg = _runner_from_config(a.config)
    if r is None:
        return 6
    assets = sorted({h["asset"] for h in r.hyps})
    print("RUNNER START freeze=%s code=%s assets=%s" % (r.fh[:16], r.code_hash[:16], ",".join(assets)))
    clock = lambda: int(time.time())
    try:
        loop.run_loop(r, assets, feed.fetch_ohlc, clock, time.sleep,
                      fetch_tickers=feed.fetch_tickers, max_cycles=1 if a.once else None)
    finally:
        r.close()
    return 0


def cmd_paper_status(a):
    import time
    r, _cfg = _runner_from_config(a.config, read_only=True)
    if r is None:
        return 6
    try:
        now = int(time.time())
        st = r.status(now)
        if a.html:
            from .statuspage import render
            tmp = a.html + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:       # atomar: erst schreiben, dann ersetzen (QA2 M3)
                f.write(render(st, r.recent_events()))
            os.replace(tmp, a.html)
        _dump(st)
        if a.max_age_s is not None:
            why = r.freshness_problem(now, a.max_age_s)
            if why is not None:
                print("PAPER-STATUS ALARM: %s" % why)
                return 8
    finally:
        r.close()
    return 0


def cmd_feed_check(a):
    """Prueft die beiden oeffentlichen Antwortformate gegen den Parser. Gibt nur Zaehler und Flags aus, keine Preise."""
    import time
    from . import feed
    res = {"tool": "lf1.feed-check", "lf1_version": __version__, "utc_now": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "ohlc": {}, "tickers": {}}
    ok = True
    now = int(time.time())
    for asset in sorted(feed.SPOT_PAIRS):
        try:
            cs = feed.fetch_ohlc(asset)
            ts = [c[0] for c in cs]
            res["ohlc"][asset] = {"ok": True, "n": len(cs), "first_ts": ts[0], "last_ts": ts[-1], "all_hour_aligned": all(t % 3600 == 0 for t in ts),
                                  "strictly_increasing": all(b > a for a, b in zip(ts, ts[1:])),
                                  "steps_hours": sorted({(b - a) // 3600 for a, b in zip(ts, ts[1:])}),
                                  "last_is_current_hour": ts[-1] == now // 3600 * 3600,
                                  "all_finite_positive": all(min(c[1:5]) > 0 and max(c[1:5]) < float("inf") for c in cs)}
            ok = ok and res["ohlc"][asset]["all_hour_aligned"] and res["ohlc"][asset]["strictly_increasing"] and res["ohlc"][asset]["all_finite_positive"]
        except Exception as e:                       # Formatabweichung ist das Ergebnis, kein Abbruch
            res["ohlc"][asset] = {"ok": False, "err": type(e).__name__ + ": " + str(e)[:200]}
            ok = False
    try:
        tk = feed.fetch_tickers(sorted(feed.PERP_SYMBOLS))
        for asset, sym in sorted(feed.PERP_SYMBOLS.items()):
            t = tk.get(sym)
            res["tickers"][asset] = {"symbol": sym, "found": t is not None,
                                     "fields_present": sorted(k for k, v in (t or {}).items() if v is not None)}
            ok = ok and t is not None and t.get("markPrice") is not None
    except Exception as e:
        res["tickers"] = {"ok": False, "err": type(e).__name__ + ": " + str(e)[:200]}
        ok = False
    res["ok"] = bool(ok)
    _dump(res)
    return 0 if ok else 7


def cmd_paper_eval(a):
    import time
    from .paper_eval import evaluate_paper
    from .runner import StartRefused
    with open(a.config, encoding="utf-8") as f:
        cfg = json.load(f)
    with open(cfg["freeze"], encoding="utf-8") as f:
        doc = json.load(f)
    try:
        res = evaluate_paper(cfg["db"], doc, nboot=a.nboot, nplacebo=a.nplacebo)
    except StartRefused as e:
        print("PAPER-EVAL VERWEIGERT: %s" % e)
        return 6
    os.makedirs(a.out, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    bt._write_json(os.path.join(a.out, "paper_eval_%s.json" % stamp), res)
    _dump(res)
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="lf1")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("selfcheck"); s.add_argument("--spec"); s.set_defaults(f=cmd_selfcheck)
    s = sub.add_parser("file-q"); s.add_argument("--zip", required=True); s.add_argument("--out", required=True); s.set_defaults(f=cmd_file_q)
    s = sub.add_parser("regime"); s.add_argument("--zip", required=True); s.add_argument("--out", required=True)
    s.add_argument("--cutoff", default=CUTOFF); s.set_defaults(f=cmd_regime)
    s = sub.add_parser("window-q"); s.add_argument("--zip", required=True); s.add_argument("--regime", required=True)
    s.add_argument("--out", required=True); s.add_argument("--window", default="A", choices=["A", "B"]); s.set_defaults(f=cmd_window_q)
    s = sub.add_parser("gate"); s.add_argument("--zip", required=True); s.add_argument("--regime", required=True)
    s.add_argument("--spec", required=True); s.add_argument("--out", required=True)
    s.add_argument("--window", default="A", choices=["A", "B"]); s.add_argument("--freeze-hash"); s.set_defaults(f=cmd_gate)
    s = sub.add_parser("epoch-q"); s.add_argument("--zip", required=True); s.add_argument("--regime", required=True)
    s.add_argument("--out", required=True); s.add_argument("--assets", nargs="+", default=["BTC"], choices=["BTC", "ETH", "SOL"]); s.set_defaults(f=cmd_epoch_q)
    s = sub.add_parser("freeze"); s.add_argument("--zip", required=True); s.add_argument("--regime", required=True)
    s.add_argument("--gate", required=True); s.add_argument("--hyps", required=True); s.add_argument("--bau-spec", required=True)
    s.add_argument("--out", required=True); s.set_defaults(f=cmd_freeze)
    s = sub.add_parser("backtest"); s.add_argument("--zip", required=True); s.add_argument("--regime", required=True)
    s.add_argument("--freeze", required=True); s.add_argument("--stage", required=True); s.add_argument("--out", required=True)
    s.add_argument("--window", choices=["A", "B"]); s.set_defaults(f=cmd_backtest)
    s = sub.add_parser("paper-run"); s.add_argument("--config", required=True); s.add_argument("--once", action="store_true"); s.set_defaults(f=cmd_paper_run)
    s = sub.add_parser("paper-status"); s.add_argument("--config", required=True); s.add_argument("--html")
    s.add_argument("--max-age-s", type=int, help="Exit 8, wenn eine Kerze fehlt oder aelter als N Sekunden (oder aus der Zukunft) ist"); s.set_defaults(f=cmd_paper_status)
    s = sub.add_parser("feed-check"); s.set_defaults(f=cmd_feed_check)
    s = sub.add_parser("paper-eval"); s.add_argument("--config", required=True); s.add_argument("--out", required=True)
    s.add_argument("--nboot", type=int, default=5000); s.add_argument("--nplacebo", type=int, default=1000); s.set_defaults(f=cmd_paper_eval)
    a = p.parse_args(argv)
    try:
        return a.f(a)
    except DataError as e:
        print("DATENFEHLER: %s" % e)
        return 5


if __name__ == "__main__":
    sys.exit(main())
