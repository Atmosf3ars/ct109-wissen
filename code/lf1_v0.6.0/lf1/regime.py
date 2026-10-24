"""Regimewahl nach GATE_SPEC_v1 §3 aus BTC/USD-Tagesschlusskursen (UTC) bis 2026-06-30.

RV30(t) = sqrt(365) * Std_{ddof=1}(ln(C_k/C_{k-1}), k = t-29..t), nur Information <= t.
Fenster der Laenge W Tage (Start taeglich), Score M = Median(RV30) im Fenster.
LV: M <= 0.45, HV: M >= 0.55.
A = LV-Fenster mit spaetestem Ende <= Stichtag.
B = HV-Fenster mit spaetestem Ende, das A nicht ueberlappt und mindestens 14 volle Tage Abstand hat
    (Auslegung: Anzahl Tage zwischen den Fenstern >= 14).
W = 270; fehlt A oder B: W = 180; fehlt dann noch eines: BLOCKED.
Keine Zufallsgroessen. Ergebnis wird gehasht, bevor der Gate-Lauf startet.
"""
import datetime as dt

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

from .util import json_hash

LV_MAX = 0.45
HV_MIN = 0.55
MIN_GAP_DAYS = 14
RV_DAYS = 30
CUTOFF = "2026-06-30"


def day_to_iso(day):
    return (dt.date(1970, 1, 1) + dt.timedelta(days=int(day))).isoformat()


def iso_to_day(s):
    return (dt.date.fromisoformat(s) - dt.date(1970, 1, 1)).days


def daily_rv30(ts, close, cutoff_day):
    """Gibt (first_day, rv30_array) zurueck; Index i entspricht Tag first_day+i. Luecken -> NaN."""
    days = (ts // 86400).astype(np.int64)
    keep = days <= cutoff_day
    days, close = days[keep], close[keep]
    if len(days) == 0:
        return 0, np.array([])
    first, last = int(days.min()), int(days.max())
    cal = np.full(last - first + 1, np.nan)
    cal[days - first] = close
    with np.errstate(divide="ignore", invalid="ignore"):
        lr = np.log(cal[1:] / cal[:-1])
    lr = np.concatenate(([np.nan], lr))
    rv = np.full(len(cal), np.nan)
    if len(cal) >= RV_DAYS:
        win = sliding_window_view(lr, RV_DAYS)  # Fenster endet bei Index j+RV_DAYS-1
        sd = np.std(win, axis=1, ddof=1)        # NaN, wenn ein Wert NaN
        rv[RV_DAYS - 1:] = np.sqrt(365.0) * sd
    return first, rv


def window_scores(rv, W):
    """Median-RV30 je Fenster (Start s, Ende s+W-1); NaN wenn ein Wert fehlt."""
    if len(rv) < W:
        return np.array([])
    win = sliding_window_view(rv, W)
    bad = np.isnan(win).any(axis=1)
    m = np.median(win, axis=1)
    m[bad] = np.nan
    return m


def _gap_days(a_start, a_end, b_start, b_end):
    return max(b_start - a_end - 1, a_start - b_end - 1)


def select_regimes(ts, close, cutoff=CUTOFF, input_sha256=None):
    cutoff_day = iso_to_day(cutoff)
    first, rv = daily_rv30(ts, close, cutoff_day)
    result = {
        "spec": "GATE_SPEC_v1 §3",
        "cutoff": cutoff,
        "thresholds": {"LV_max": LV_MAX, "HV_min": HV_MIN, "min_gap_days": MIN_GAP_DAYS},
        "input_sha256": input_sha256,
        "daily_rows": int(len(ts)),
        "rv30_defined_days": int(np.sum(~np.isnan(rv))),
    }
    for W in (270, 180):
        m = window_scores(rv, W)
        if len(m) == 0:
            continue
        starts = np.arange(len(m)) + first
        ends = starts + W - 1
        lv = np.where(~np.isnan(m) & (m <= LV_MAX) & (ends <= cutoff_day))[0]
        hv = np.where(~np.isnan(m) & (m >= HV_MIN) & (ends <= cutoff_day))[0]
        a = b = None
        if len(lv):
            ia = lv[np.argmax(ends[lv])]
            a = (int(starts[ia]), int(ends[ia]), float(m[ia]))
            for ib in hv[np.argsort(-ends[hv])]:
                if _gap_days(a[0], a[1], int(starts[ib]), int(ends[ib])) >= MIN_GAP_DAYS:
                    b = (int(starts[ib]), int(ends[ib]), float(m[ib]))
                    break
        result["candidates_W%d" % W] = {"lv_windows": int(len(lv)), "hv_windows": int(len(hv))}
        if a is not None and b is not None:
            result["W"] = W
            result["status"] = "OK"
            for key, w in (("A", a), ("B", b)):
                result[key] = {
                    "start": day_to_iso(w[0]),
                    "end": day_to_iso(w[1]),
                    "days": W,
                    "median_rv30": round(w[2], 6),
                }
            result["hash_sha256"] = json_hash({k: v for k, v in result.items() if k != "hash_sha256"})
            return result
    result["W"] = None
    result["status"] = "BLOCKED"
    result["note"] = "Kein A/B-Paar mit W=270 oder 180 (Spec §3): keine Historien-Discovery; Fallback = Forward-Daten ab 2026-07-01"
    result["hash_sha256"] = json_hash({k: v for k, v in result.items() if k != "hash_sha256"})
    return result


def window_bounds_utc(regime, key):
    """[t0, t1) in Unix-Sekunden fuer Regime A oder B."""
    w = regime[key]
    t0 = iso_to_day(w["start"]) * 86400
    t1 = (iso_to_day(w["end"]) + 1) * 86400
    return t0, t1
