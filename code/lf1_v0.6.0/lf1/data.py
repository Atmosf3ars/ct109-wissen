"""Loader fuer Kraken-OHLCVT (CSV ohne Kopfzeile: timestamp,open,high,low,close,volume,trades).

Wichtig (Kraken-Seite, L1): Intervalle ohne Handel FEHLEN in den Dateien. Der Loader fuellt
nie auf, interpoliert nie. Fehlende Bars bleiben fehlend (NaN im Gitter).
Liest direkt aus dem ZIP (kein Entpacken noetig) oder aus einem Verzeichnis.
Fehlermeldungen enthalten nie Dateiinhalte.
"""
import io
import os
import re
import zipfile
from dataclasses import dataclass

import numpy as np

from .util import sha256_bytes

ALIASES = {
    "BTC": ("XBTUSD", "BTCUSD"),
    "ETH": ("ETHUSD",),
    "SOL": ("SOLUSD",),
    "DOGE": ("XDGUSD", "DOGEUSD"),
    "XRP": ("XRPUSD",),
}


class DataError(Exception):
    pass


@dataclass
class Bars:
    asset: str
    interval_min: int
    member: str
    sha256: str
    nbytes: int
    ts: np.ndarray   # int64, Unix-Sekunden (Bar-Beginn, UTC)
    o: np.ndarray
    h: np.ndarray
    l: np.ndarray
    c: np.ndarray
    v: np.ndarray
    n: np.ndarray    # Trades (0 wenn Spalte fehlt)


class Source:
    """ZIP-Datei oder Verzeichnis."""

    def __init__(self, path):
        self.path = path
        self._zip = None
        if os.path.isdir(path):
            self.kind = "dir"
        elif zipfile.is_zipfile(path):
            self.kind = "zip"
            self._zip = zipfile.ZipFile(path)
        else:
            raise DataError("Quelle ist weder Verzeichnis noch ZIP: %s" % path)

    def names(self):
        if self.kind == "zip":
            if self._zip is None:
                raise DataError("Quelle ist geschlossen")
            return [i.filename for i in self._zip.infolist() if not i.is_dir()]
        out = []
        for root, _d, files in os.walk(self.path):
            for f in files:
                out.append(os.path.relpath(os.path.join(root, f), self.path))
        return out

    def read(self, name):
        if self.kind == "zip":
            if self._zip is None:
                raise DataError("Quelle ist geschlossen")
            return self._zip.read(name)
        with open(os.path.join(self.path, name), "rb") as f:
            return f.read()

    def close(self):
        if self._zip is not None:
            self._zip.close()
            self._zip = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


def find_member(names, pair, interval_min):
    pat = re.compile(r"(?:^|[\\/])%s_%d\.csv$" % (re.escape(pair), int(interval_min)), re.I)
    return sorted(n for n in names if pat.search(n))


def parse_ohlcvt(raw):
    """Parst CSV-Bytes. Wirft DataError ohne Inhalte zu zitieren."""
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError:
        raise DataError("Datei ist nicht ASCII")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        raise DataError("Datei ist leer")
    first = lines[0].split(",")[0].strip()
    try:
        float(first)
    except ValueError:
        lines = lines[1:]  # Kopfzeile (erwartet: keine)
    try:
        arr = np.loadtxt(io.StringIO("\n".join(lines)), delimiter=",", ndmin=2, dtype=np.float64)
    except ValueError:
        raise DataError("CSV nicht parsebar (unregelmaessige Spalten oder Nichtzahlen)")
    if arr.shape[1] < 6:
        raise DataError("weniger als 6 Spalten")
    if not np.all(np.isfinite(arr[:, 0])):
        raise DataError("nichtendliche Zeitstempel")
    if arr[:, 0].max() > 1e11:
        raise DataError("Zeitstempel nicht in Sekunden")
    ts = arr[:, 0].astype(np.int64)
    n = arr[:, 6].astype(np.int64) if arr.shape[1] >= 7 else np.zeros(len(ts), dtype=np.int64)
    return ts, arr[:, 1], arr[:, 2], arr[:, 3], arr[:, 4], arr[:, 5], n


def load_bars(src, asset, interval_min):
    """Laedt eine Serie. asset in {BTC, ETH, SOL}. Genau ein Treffer erwartet."""
    if asset not in ALIASES:
        raise DataError("unbekanntes Asset: %s" % asset)
    names = src.names()
    hits = []
    for pair in ALIASES[asset]:
        hits += [(pair, m) for m in find_member(names, pair, interval_min)]
    if len(hits) == 0:
        raise DataError("keine Datei fuer %s %d min gefunden" % (asset, interval_min))
    if len(hits) > 1:
        raise DataError("mehrdeutig: %d Dateien fuer %s %d min" % (len(hits), asset, interval_min))
    _pair, member = hits[0]
    raw = src.read(member)
    ts, o, h, l, c, v, n = parse_ohlcvt(raw)
    return Bars(asset, int(interval_min), member, sha256_bytes(raw), len(raw), ts, o, h, l, c, v, n)


def to_grid(bars, t0, t1, step_s=3600):
    """Regelmaessiges Gitter [t0, t1) mit Schritt step_s. Fehlende Bars = NaN.

    Gibt (o, h, l, c, v, present) zurueck. Bars ausserhalb [t0,t1) oder neben dem Gitter werden
    ignoriert (Anzahl ueber check_window sichtbar). Bei Duplikaten gewinnt der letzte Eintrag.
    """
    if (t1 - t0) % step_s != 0:
        raise DataError("Fenstergrenzen nicht auf Gitter")
    n = (t1 - t0) // step_s
    out = {k: np.full(n, np.nan) for k in "ohlcv"}
    sel = (bars.ts >= t0) & (bars.ts < t1) & (((bars.ts - t0) % step_s) == 0)
    idx = ((bars.ts[sel] - t0) // step_s).astype(np.int64)
    for k in "ohlcv":
        out[k][idx] = getattr(bars, k)[sel]
    present = ~np.isnan(out["o"])
    return out["o"], out["h"], out["l"], out["c"], out["v"], present
