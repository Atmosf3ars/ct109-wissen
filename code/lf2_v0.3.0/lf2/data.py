"""Laden der Tiingo-Tagesdaten in ein gemeinsames Raster (Kalender = SPY). Nur Standardbibliothek + numpy."""
import csv
import os

import numpy as np

COLS = ("close", "volume", "adjclose", "adjopen")


def date_int(s):
    return int(s[:4]) * 10000 + int(s[5:7]) * 100 + int(s[8:10])


def read_csv(path):
    """Gibt Dict Spalte -> np.array und Datumsarray (int YYYYMMDD) zurueck."""
    with open(path, newline="", encoding="utf-8") as f:
        rd = csv.reader(f)
        head = [h.strip().lower() for h in next(rd)]
        idx = {c: head.index(c) for c in ("date",) + COLS}
        dates, cols = [], {c: [] for c in COLS}
        for row in rd:
            if not row:
                continue
            dates.append(date_int(row[idx["date"]]))
            for c in COLS:
                v = row[idx[c]]
                cols[c].append(float(v) if v != "" else float("nan"))
    return np.array(dates, dtype=np.int64), {c: np.array(v, dtype=float) for c, v in cols.items()}


def load_panel(price_dir, symbols, calendar_symbol="SPY", end_date=20260630):
    """Panel (T,N) fuer die Aktien (ohne Kalendersymbol). Kalender = Handelstage von SPY bis end_date.
    Gibt dict(dates, symbols, O, C, CL, V, dropped_rows) zurueck. Symbole ohne Datei werden uebersprungen (und gezaehlt)."""
    cal_dates, cal = read_csv(os.path.join(price_dir, calendar_symbol + ".csv"))
    keep = cal_dates <= end_date
    dates = cal_dates[keep]
    pos = {int(d): i for i, d in enumerate(dates)}
    syms = [s for s in symbols if s != calendar_symbol and os.path.exists(os.path.join(price_dir, s + ".csv"))]
    T, N = len(dates), len(syms)
    O = np.full((T, N), np.nan); C = np.full((T, N), np.nan); CL = np.full((T, N), np.nan); V = np.full((T, N), np.nan)
    dropped = 0
    for j, s in enumerate(syms):
        d, cols = read_csv(os.path.join(price_dir, s + ".csv"))
        for k in range(len(d)):
            i = pos.get(int(d[k]))
            if i is None:
                dropped += 1
                continue
            O[i, j] = cols["adjopen"][k]; C[i, j] = cols["adjclose"][k]; CL[i, j] = cols["close"][k]; V[i, j] = cols["volume"][k]
    for a in (O, C, CL, V):
        a[~np.isfinite(a)] = np.nan
    O[O <= 0] = np.nan; C[C <= 0] = np.nan; CL[CL <= 0] = np.nan
    return {"dates": dates, "symbols": syms, "O": O, "C": C, "CL": CL, "V": V, "dropped_rows": dropped,
            "spy_close": cal["adjclose"][keep]}


def window_bounds(dates, start, end):
    """(ws, we) Indizes (inklusive) der ersten/letzten Handelstage innerhalb [start, end] (YYYYMMDD)."""
    idx = np.where((dates >= start) & (dates <= end))[0]
    if len(idx) == 0:
        raise ValueError("Fenster leer")
    return int(idx[0]), int(idx[-1])
