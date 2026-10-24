"""Synthetische Daten fuer Tests (kein reales Marktdatum)."""
import io
import zipfile

import numpy as np


def hourly_walk(n_hours, sigma_bp_per_hour, seed, start_ts, p0=100.0, drop_frac=0.0, drift_bp=0.0):
    """Stuendliche Bars mit Zufallspfad. open_t = p[t], close_t = p[t+1]. drop_frac = Anteil fehlender Bars."""
    rng = np.random.default_rng(seed)
    lr = rng.normal(drift_bp, sigma_bp_per_hour, n_hours) * 1e-4
    p = p0 * np.exp(np.concatenate(([0.0], np.cumsum(lr))))
    o, c = p[:-1], p[1:]
    h = np.maximum(o, c) * 1.0001
    l = np.minimum(o, c) * 0.9999
    v = 1.0 + rng.random(n_hours)
    ts = start_ts + 3600 * np.arange(n_hours)
    keep = rng.random(n_hours) >= drop_frac
    return ts[keep], o[keep], h[keep], l[keep], c[keep], v[keep]


def to_csv(ts, o, h, l, c, v, trades=3):
    buf = io.StringIO()
    for i in range(len(ts)):
        buf.write("%d,%.8f,%.8f,%.8f,%.8f,%.8f,%d\n" % (ts[i], o[i], h[i], l[i], c[i], v[i], trades))
    return buf.getvalue().encode("ascii")


def daily_from_vol(daily_sigma_list, start_day, seed, p0=100.0):
    """Tagesschlusskurse; daily_sigma_list = Liste von (Anzahl Tage, jaehrliche Vol)."""
    rng = np.random.default_rng(seed)
    lrs = []
    for n, ann in daily_sigma_list:
        lrs.append(rng.normal(0.0, ann / np.sqrt(365.0), n))
    lr = np.concatenate(lrs)
    close = p0 * np.exp(np.cumsum(lr))
    days = start_day + np.arange(len(close))
    return days * 86400, close


def make_zip(path, members, prefix="Kraken_OHLCVT/"):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in members.items():
            z.writestr(prefix + name, data)
