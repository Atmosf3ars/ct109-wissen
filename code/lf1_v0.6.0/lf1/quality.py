"""Datenqualitaet nach GATE_SPEC_v1 §7. Nur Q-Metriken, keine Signal-/Richtungsstatistik.

Auslegung (vor dem Datenblick festgelegt, siehe BAU_SPEC_S1S3_v1 §1.4):
- Lueckenlaenge = Anzahl fehlender Stundenbars in Folge (diff/3600 - 1); Fehler bei > 6.
- Kraken laesst Intervalle ohne Handel weg; "Bars ohne Volumen" ist deshalb meist 0
  (leere Metrik), die Fehlend-Quote und Luecken tragen die Pruefung.
- |1h-Rendite| > 30 % wird als Pruefliste gemeldet (max. 20 Zeitstempel), nie entfernt.
"""
import datetime as dt

import numpy as np

MISSING_MAX_PCT = 1.0
GAP_MAX_H = 6
NOVOL_MAX_PCT = 5.0
BIGMOVE = 0.30


def iso(ts):
    return dt.datetime.fromtimestamp(int(ts), dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def check_file(bars):
    ts = bars.ts
    d = np.diff(ts) if len(ts) > 1 else np.array([], dtype=np.int64)
    bad_ohlc = int(
        np.sum((bars.h < np.maximum(bars.o, bars.c)) | (bars.l > np.minimum(bars.o, bars.c)) | (bars.c <= 0))
    )
    return {
        "asset": bars.asset,
        "interval_min": bars.interval_min,
        "member": bars.member,
        "sha256": bars.sha256,
        "bytes": bars.nbytes,
        "rows": int(len(ts)),
        "first_ts": iso(ts[0]) if len(ts) else None,
        "last_ts": iso(ts[-1]) if len(ts) else None,
        "strictly_increasing": bool(np.all(d > 0)),
        "duplicate_ts": int(np.sum(d == 0)),
        "off_grid_rows": int(np.sum(ts % (bars.interval_min * 60) != 0)),
        "nonfinite_rows": int(np.sum(~np.isfinite(bars.o + bars.h + bars.l + bars.c + bars.v))),
        "ohlc_inconsistent_rows": bad_ohlc,
    }


def check_window(bars60, t0, t1):
    """Spec §7 je Asset im Fenster [t0, t1) (60-min-Bars)."""
    ts = bars60.ts
    sel = (ts >= t0) & (ts < t1)
    w_ts = ts[sel]
    w_c = bars60.c[sel]
    w_v = bars60.v[sel]
    expected = (t1 - t0) // 3600
    uniq = np.unique(w_ts)
    dups = int(len(w_ts) - len(uniq))
    nondec = int(np.sum(np.diff(w_ts) < 0)) if len(w_ts) > 1 else 0
    on_grid = uniq[((uniq - t0) % 3600) == 0]
    present = int(len(on_grid))
    missing_pct = 100.0 * (expected - present) / expected if expected > 0 else 100.0
    if present > 0:
        edges = np.concatenate(([t0 - 3600], on_grid, [t1]))
        max_gap = int(np.max(np.diff(edges) // 3600 - 1))
    else:
        max_gap = int(expected)
    novol = float(100.0 * np.mean(w_v <= 0)) if len(w_v) else 100.0
    # |1h-Rendite| > 30 %: nur aufeinanderfolgende Stundenbars (Differenz genau 3600 s)
    big_ts = []
    if len(w_ts) > 1 and nondec == 0:
        consec = np.diff(w_ts) == 3600
        with np.errstate(divide="ignore", invalid="ignore"):
            ret = np.abs(w_c[1:] / w_c[:-1] - 1.0)
        big = consec & (ret > BIGMOVE)
        big_ts = [iso(x) for x in w_ts[1:][big][:20]]
        big_n = int(np.sum(big))
    else:
        big_n = 0
    reasons = []
    if expected <= 0 or present == 0:
        reasons.append("keine Bars im Fenster")
    if missing_pct > MISSING_MAX_PCT:
        reasons.append("fehlende Bars %.2f %% > %.1f %%" % (missing_pct, MISSING_MAX_PCT))
    if max_gap > GAP_MAX_H:
        reasons.append("Luecke %d h > %d h" % (max_gap, GAP_MAX_H))
    if dups > 0:
        reasons.append("doppelte Zeitstempel: %d" % dups)
    if nondec > 0:
        reasons.append("nicht aufsteigend: %d" % nondec)
    if novol > NOVOL_MAX_PCT:
        reasons.append("Bars ohne Volumen %.2f %% > %.1f %%" % (novol, NOVOL_MAX_PCT))
    return {
        "asset": bars60.asset,
        "expected_bars": int(expected),
        "present_bars": present,
        "missing_pct": round(missing_pct, 4),
        "max_gap_hours": max_gap,
        "duplicate_ts": dups,
        "non_monotonic": nondec,
        "no_volume_pct": round(novol, 4),
        "big_move_count": big_n,
        "big_move_review_list": big_ts,
        "series_first_ts": iso(ts[0]) if len(ts) else None,
        "passes": len(reasons) == 0,
        "reasons": reasons,
    }
