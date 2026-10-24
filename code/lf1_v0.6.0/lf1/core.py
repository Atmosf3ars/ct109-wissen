"""lf1_core: Signalregeln, Kosten- und Fill-Modell. Reine Funktionen, ein Code fuer Backtest und Runner.

Zeitregel: Entscheidung nur zum Bar-Close i mit Daten <= i. Einstieg zum OPEN von Bar i+1(+Latenz),
Ausstieg zum OPEN von Bar i+1+latency+H. Fehlende Bars (NaN) liefern kein Signal und keinen Trade;
nichts wird aufgefuellt oder interpoliert. Eine offene Position je Regel, keine Ueberlappung.
Kein Netzwerk, keine Broker-/Order-Module.
"""
from dataclasses import dataclass

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

TRADE_DTYPE = np.dtype([
    ("i_dec", "i8"), ("i_entry", "i8"), ("i_exit", "i8"), ("side", "i1"),
    ("entry", "f8"), ("exit", "f8"), ("gross_bp", "f8"), ("cost_bp", "f8"), ("net_bp", "f8"),
])


@dataclass(frozen=True)
class CostModel:
    """Roundtrip-Kosten in bp (Gebuehren + Spread + Slippage) plus Funding je 8 h Haltedauer."""
    roundtrip_bp: float
    funding_bp_per_8h: float = 0.0
    mult: float = 1.0   # Stresstest: 1.5 = alle Kosten +50 % (Roundtrip und Funding)

    def cost_bp(self, hold_hours):
        return self.mult * (self.roundtrip_bp + self.funding_bp_per_8h * hold_hours / 8.0)


def gate_consistent_cost(c0_bp, mult=1.0):
    """Kostenmodell wie GATE_SPEC_v1 §5: 1.25 * c0 + 1.0 bp je 8 h (konservativ, Annahmen A2/A4)."""
    return CostModel(roundtrip_bp=1.25 * c0_bp, funding_bp_per_8h=1.0, mult=mult)


def signals_breakout(h, l, c, L, side="long"):
    """+1, wenn Close_i > max(High[i-L..i-1]); -1, wenn Close_i < min(Low[i-L..i-1]) (falls side erlaubt)."""
    n = len(c)
    sig = np.zeros(n, dtype=np.int8)
    if L < 1 or n <= L:
        return sig
    mx = np.max(sliding_window_view(h, L), axis=1)[: n - L]
    mn = np.min(sliding_window_view(l, L), axis=1)[: n - L]
    with np.errstate(invalid="ignore"):
        if side in ("long", "both"):
            sig[L:][c[L:] > mx] = 1
        if side in ("short", "both"):
            sig[L:][c[L:] < mn] = -1
    return sig


def signals_ts_mom(c, L, side="both"):
    """sign(ln C_i - ln C_{i-L}); side 'long'/'short' schneidet die andere Richtung ab."""
    n = len(c)
    sig = np.zeros(n, dtype=np.int8)
    if L < 1 or n <= L:
        return sig
    with np.errstate(invalid="ignore", divide="ignore"):
        d = np.log(c[L:]) - np.log(c[:-L])
    s = np.where(np.isnan(d), 0, np.sign(d)).astype(np.int8)
    if side == "long":
        s = np.where(s > 0, s, 0).astype(np.int8)
    elif side == "short":
        s = np.where(s < 0, s, 0).astype(np.int8)
    sig[L:] = s
    return sig


def signals_shock_fade(c, w, k, N):
    """Gegenrichtung zu Bewegungen mit |ln C_i - ln C_{i-w}| > k * sigma1 * sqrt(w).

    sigma1 = Std (ddof=1) der 1-Bar-Log-Renditen der N Bars VOR Bar i (i-N..i-1), nur Vergangenheit.
    """
    n = len(c)
    sig = np.zeros(n, dtype=np.int8)
    if w < 1 or N < 2 or n <= max(w, N):
        return sig
    with np.errstate(invalid="ignore", divide="ignore"):
        r1 = np.concatenate(([np.nan], np.log(c[1:]) - np.log(c[:-1])))
        sd = np.std(sliding_window_view(r1, N), axis=1, ddof=1)[: n - N]   # Fenster j deckt r1[j..j+N-1]
        move = np.log(c[w:]) - np.log(c[:-w])
    i0 = max(w, N)
    idx = np.arange(i0, n)
    thr = k * sd[idx - N] * np.sqrt(w)
    m = move[idx - w]
    with np.errstate(invalid="ignore"):
        hit = np.abs(m) > thr
    sig[idx[hit]] = (-np.sign(m[hit])).astype(np.int8)
    return sig


def simulate(o, sig, H, cost, latency_bars=0, step_hours=1.0):
    """Handelt Signale: Einstieg Open[i+1+lat], Ausstieg Open[i+1+lat+H]. Gibt TRADE_DTYPE-Array zurueck.

    Naechste Entscheidung fruehestens bei Index i+H (dann faellt Einstieg mit dem Ausstieg
    der Vorposition zusammen): keine Ueberlappung, keine Doppelzaehlung.
    Luecke (NaN) bei Ein- oder Ausstieg: kein Trade (Position wird nicht eroeffnet).
    """
    n = len(o)
    rows = []
    nxt = 0
    for i in range(n):
        if i < nxt:
            continue
        s = int(sig[i])
        if s == 0:
            continue
        e = i + 1 + latency_bars
        x = e + H
        if x >= n:
            continue
        pe, px = o[e], o[x]
        if not (np.isfinite(pe) and np.isfinite(px)) or pe <= 0 or px <= 0:
            continue
        gross = s * (px / pe - 1.0) * 1e4
        cb = cost.cost_bp(H * step_hours)
        rows.append((i, e, x, s, pe, px, gross, cb, gross - cb))
        nxt = i + H
    return np.array(rows, dtype=TRADE_DTYPE)


def expectancy_bp(trades):
    """Mittlere Netto-Rendite je Trade in bp (nie Trefferquote)."""
    if len(trades) == 0:
        return None
    return float(np.mean(trades["net_bp"]))
