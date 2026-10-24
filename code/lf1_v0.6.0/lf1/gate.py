"""Bewegungsbudget-Gate nach GATE_SPEC_v1 §4-§6 (richtungsblind: nur Betraege von Renditen).

Rendite r = 1e4 * ln(P_{t+h} / P_t) mit P = OPEN des Stundenbars (Auslegung, siehe
BAU_SPEC_S1S3_v1 §1.4); Fenster starten stuendlich, beide Endpunkt-Bars muessen im Fenster
A (bzw. B) liegen und vorhanden sein.
Ausgabe: nur Aggregate je Zelle. Keine Zeitreihen, keine Vorzeichenstatistik.
Einmal-Lauf: Sperrdatei je Fenster; Wiederholung nur nach technischem Fehler mit identischem Code-Hash.
"""
import datetime as dt
import json
import os
from statistics import NormalDist

import numpy as np

from .data import load_bars, to_grid
from .quality import check_window
from .regime import window_bounds_utc
from .util import SEED, SPEC_SHA256, check_spec, code_hash, json_hash

ASSETS = ("BTC", "ETH", "SOL")
HORIZONS_H = (1, 4, 24, 72)
C0_BP = {"BTC": 10.1, "ETH": 10.4, "SOL": 16.0}   # Annahme A3 (SOL = Obergrenze, nicht gemessen)
COST_FACTOR = 1.25                                # Annahme A2
FUND_BP_PER_8H = 1.0                              # Annahme A4
RHO_P = 0.05                                      # Annahme A1
RHO_W = 0.10
NEFF_MIN = 60
BLOCK_H = 168
NBOOT = 2000
ALPHA_PRIME = 0.05 / 8
BETA = 0.2


class GateError(Exception):
    pass


def c_gate(asset, h_hours):
    return COST_FACTOR * C0_BP[asset] + FUND_BP_PER_8H * h_hours / 8.0


def window_returns(o, h):
    """Renditen in bp fuer alle stuendlichen Startpunkte, deren Start- UND Endbar vorhanden sind."""
    n = len(o)
    if n <= h:
        return np.array([])
    a, b = o[:-h], o[h:]
    with np.errstate(invalid="ignore"):
        ok = ~np.isnan(a) & ~np.isnan(b) & (a > 0) & (b > 0)
    return 1e4 * np.log(b[ok] / a[ok])


def mbb_lcb(x, block, nboot, rng, q=0.05):
    """5-%-Quantil des Mittelwerts aus Moving-Block-Bootstrap (volle Bloecke)."""
    n = len(x)
    if n < block:
        return None
    nb = -(-n // block)
    cs = np.concatenate(([0.0], np.cumsum(x)))
    starts = rng.integers(0, n - block + 1, size=(nboot, nb))
    means = (cs[starts + block] - cs[starts]).sum(axis=1) / (nb * block)
    return float(np.quantile(means, q))


def classify(rho_plus):
    if rho_plus is None or not np.isfinite(rho_plus):
        return "X"
    if rho_plus <= RHO_P:
        return "P"
    if rho_plus <= RHO_W:
        return "W"
    return "X"


def evaluate_cell(asset, h_hours, o, present, q_ok, cost_override=None):
    """Eine (Asset, Horizont)-Zelle im Fenster. o = Open-Gitter (NaN = fehlt)."""
    r = window_returns(o, h_hours)
    absr = np.abs(r)
    valid_hours = int(np.sum(present))
    n_eff = valid_hours // h_hours
    cell = {
        "asset": asset,
        "h_hours": h_hours,
        "n_windows": int(len(r)),
        "n_eff": int(n_eff),
        "mean_abs_r_bp": None,
        "lcb95_bp": None,
        "rms_bp": None,
        "c_gate_bp": round(c_gate(asset, h_hours) if cost_override is None else cost_override, 6),
        "rho_min_mean": None,
        "rho_min_plus": None,
        "mde_net_bp_full_exposure": None,
        "class": "X",
        "evaluable": False,
        "reason": None,
    }
    if not q_ok:
        cell["reason"] = "Q-Pruefung nicht bestanden"
        return cell
    if len(r) == 0:
        cell["reason"] = "keine gueltigen Fenster"
        return cell
    if n_eff < NEFF_MIN:
        cell["reason"] = "n_eff < %d (nicht bewertbar)" % NEFF_MIN
        cell["mean_abs_r_bp"] = round(float(absr.mean()), 6)
        return cell
    rng = np.random.default_rng([SEED, ASSETS.index(asset), h_hours])
    lcb = mbb_lcb(absr, BLOCK_H, NBOOT, rng)
    mean_abs = float(absr.mean())
    rms = float(np.sqrt(np.mean(r * r)))
    c = cell["c_gate_bp"]
    cell["mean_abs_r_bp"] = round(mean_abs, 6)
    cell["rms_bp"] = round(rms, 6)
    cell["rho_min_mean"] = round(c / mean_abs, 6) if mean_abs > 0 else None
    # Zusatzausgabe (nicht Teil der Spec-Klassen): kleinster nachweisbarer Netto-Effekt je Trade
    # bei voller Auslastung (n_eff Trades), einseitig, alpha' = 0.05/8, Power 0.8. Vorzeichenfrei (RMS).
    za = NormalDist().inv_cdf(1 - ALPHA_PRIME)
    zb = NormalDist().inv_cdf(1 - BETA)
    cell["mde_net_bp_full_exposure"] = round((za + zb) * rms / np.sqrt(n_eff), 3)
    if lcb is None or lcb <= 0:
        cell["reason"] = "kein Bootstrap-LCB (n < Block) oder LCB <= 0"
        return cell
    cell["lcb95_bp"] = round(lcb, 6)
    rho_plus = c / lcb
    cell["rho_min_plus"] = round(rho_plus, 6)
    cell["class"] = classify(rho_plus)
    cell["evaluable"] = True
    return cell


def summarize(cells):
    allowed = [c for c in cells if c["class"] in ("P", "W")]
    per_h = {}
    for h in HORIZONS_H:
        al = [c["asset"] for c in allowed if c["h_hours"] == h]
        per_h[str(h)] = {"allowed_assets": al, "blocked": len(al) == 0}
    return {
        "allowed_cells": len(allowed),
        "class_P_cells": sum(1 for c in cells if c["class"] == "P"),
        "class_W_cells": sum(1 for c in cells if c["class"] == "W"),
        "per_horizon": per_h,
        "lf1_status": "ZULAESSIG" if allowed else "NULLBEFUND",
        "freeze_rule": {"max_hypotheses": 8, "max_class_W_hypotheses": 2},
    }


def _now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)


def _acquire_lock(path, code_h, regime_h):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            lk = json.load(f)
        if lk.get("status") == "error" and lk.get("code_hash") == code_h and lk.get("regime_hash") == regime_h:
            lk["status"] = "started"
            lk["attempts"] = int(lk.get("attempts", 1)) + 1
            lk["restarted_utc"] = _now()
            _write_json(path, lk)
            return lk
        raise GateError(
            "Gate-Lauf ist einmalig (Spec §8.5/8.6). Sperre vorhanden, status=%s. "
            "Wiederholung nur nach technischem Fehler mit identischem Code- und Regime-Hash." % lk.get("status")
        )
    lk = {"status": "started", "code_hash": code_h, "regime_hash": regime_h, "started_utc": _now(), "attempts": 1}
    _write_json(path, lk)
    return lk


def run_gate(src, regime, window_key, spec_path, out_dir, freeze_hash=None):
    """Fuehrt den Gate-Lauf fuer Fenster A (Gate/Discovery) oder B (nur Bestaetigung) aus."""
    spec = check_spec(spec_path)
    if not spec["ok"]:
        raise GateError("GATE_SPEC_v1.md hat nicht den eingefrorenen Hash (%s)" % spec["sha256_raw"])
    if regime.get("status") != "OK":
        raise GateError("Regimewahl ist BLOCKED: kein Gate-Lauf auf Historie")
    if window_key not in ("A", "B"):
        raise GateError("Fenster muss A oder B sein")
    if window_key == "B" and not freeze_hash:
        raise GateError("Fenster B nur zur Bestaetigung: --freeze-hash der eingefrorenen Liste angeben")
    os.makedirs(out_dir, exist_ok=True)
    ch = code_hash()
    lock_path = os.path.join(out_dir, "gate_lock_%s.json" % window_key)
    _acquire_lock(lock_path, ch, regime["hash_sha256"])
    try:
        t0, t1 = window_bounds_utc(regime, window_key)
        cells, qs, manifest = [], [], []
        for asset in ASSETS:
            bars = load_bars(src, asset, 60)
            q = check_window(bars, t0, t1)
            qs.append(q)
            manifest.append({"asset": asset, "member": bars.member, "sha256": bars.sha256, "bytes": bars.nbytes})
            o, _h, _l, _c, _v, present = to_grid(bars, t0, t1)
            for h in HORIZONS_H:
                cells.append(evaluate_cell(asset, h, o, present, q["passes"]))
        result = {
            "tool": "lf1.gate",
            "window": window_key,
            "window_bounds": {"start": regime[window_key]["start"], "end": regime[window_key]["end"]},
            "spec_check": spec,
            "code_hash": ch,
            "regime_hash": regime["hash_sha256"],
            "seed": SEED,
            "freeze_hash": freeze_hash,
            "assumptions": {
                "c0_bp": C0_BP, "cost_factor": COST_FACTOR, "funding_bp_per_8h": FUND_BP_PER_8H,
                "rho_plausible": RHO_P, "rho_wide": RHO_W, "neff_min": NEFF_MIN,
                "block_h": BLOCK_H, "n_boot": NBOOT,
            },
            "data_manifest": manifest,
            "quality": qs,
            "cells": cells,
            "summary": summarize(cells),
            "run_utc": _now(),
        }
        result["result_hash"] = json_hash({k: v for k, v in result.items() if k != "run_utc"})
        _write_json(os.path.join(out_dir, "gate_result_%s.json" % window_key), result)
        with open(lock_path, encoding="utf-8") as f:
            lk = json.load(f)
        lk["status"] = "done"
        lk["result_hash"] = result["result_hash"]
        lk["finished_utc"] = _now()
        _write_json(lock_path, lk)
        return result
    except Exception as e:  # technischer Fehler: Sperre auf "error", nie Inhalte protokollieren
        with open(lock_path, encoding="utf-8") as f:
            lk = json.load(f)
        lk["status"] = "error"
        lk["error_class"] = type(e).__name__
        lk["error_utc"] = _now()
        _write_json(lock_path, lk)
        raise
