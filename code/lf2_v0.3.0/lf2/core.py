"""Kern (RUNDE2_SPEC_v1 R1-R6): Handelbarkeit, Scores, Kohorten, Kosten. Reines numpy, vollstaendig vektorisiert.

Konventionen: Index t = Signaltag (Information <= t); Entry = adjOpen[t+1+delay]; Exit = adjOpen[t+1+delay+H].
Fehlende Preise = NaN (nichts wird aufgefuellt). Es gibt keine Zeitabfrage und keinen Zufall ausser ueber uebergebene RNGs.
"""
import numpy as np

# Spec-Konstanten (R1, R5, R6) -- Aenderung = neue Spec-Version
MIN_DV = 20e6          # Median(close*volume) der letzten 60 Tage >= 20 Mio USD
MIN_PX = 5.0           # close >= 5 USD
MIN_HIST = 260         # mindestens 260 gueltige Handelstage Historie
DV_WIN = 60
DV_MIN_VALID = 50      # Implementierungsdetail: mindestens 50 von 60 Tagen mit Daten (sonst nicht handelbar)
MIN_ELIG = 100         # weniger handelbare Aktien -> kein Signal an dem Tag
COST_CLASSES = ((100, 4.0), (300, 7.0), (float("inf"), 12.0))   # (Rang <=, Rundreise bp)
COST_PAD = 1.25
BORROW_BP_PER_DAY = 1.0


def rolling_median_dv(dv, win=DV_WIN, min_valid=DV_MIN_VALID, chunk=400):
    """Median der letzten `win` Tage (inkl. t) von dv; NaN wenn weniger als min_valid gueltige Tage. Chunked (Speicher)."""
    T, N = dv.shape
    out = np.full((T, N), np.nan)
    if T < win:
        return out
    from numpy.lib.stride_tricks import sliding_window_view
    for s in range(0, T - win + 1, chunk):
        e = min(T - win + 1, s + chunk)
        seg = dv[s:e + win - 1]
        w = sliding_window_view(seg, win, axis=0)                 # (e-s, N, win)
        valid = np.isfinite(w).sum(axis=2)
        with np.errstate(all="ignore"):
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                med = np.nanmedian(w, axis=2)
        med[valid < min_valid] = np.nan
        out[s + win - 1:e + win - 1] = med
    return out


def tradable(close_raw, volume):
    """(mask, med_dv): handelbar an Tag t nur mit Information <= t (R1)."""
    dv = close_raw * volume
    med = rolling_median_dv(dv)
    hist = np.cumsum(np.isfinite(close_raw), axis=0)
    ok = np.isfinite(med) & (med >= MIN_DV) & np.isfinite(close_raw) & (close_raw >= MIN_PX) & (hist >= MIN_HIST)
    return ok, med


def ranks_ascending(key):
    """Rang je Zeile (0 = kleinster Schluessel); NaN-Schluessel bekommen die hoechsten Raenge. Stabil (Spaltenreihenfolge bricht Gleichstand)."""
    k = np.where(np.isfinite(key), key, np.inf)
    order = np.argsort(k, axis=1, kind="stable")
    rank = np.empty_like(order)
    rows = np.arange(k.shape[0])[:, None]
    rank[rows, order] = np.arange(k.shape[1])[None, :]
    return rank


def cost_matrix(trad_mask, med_dv):
    """Rundreise-Kosten je Aktie und Tag nach Rang im 60-Tage-Median-Dollarvolumen unter den handelbaren Aktien (R5), inkl. Faktor 1,25.
    Rang 1..100: 4 bp, 101..300: 7 bp, ab 301: 12 bp (vor Faktor)."""
    key = np.where(trad_mask, -med_dv, np.nan)                   # groesster Dollarvolumen = kleinster Schluessel
    rk = ranks_ascending(key)                                    # 0-basiert
    cost = np.full(med_dv.shape, np.nan)
    prev = 0
    for lim, bp in COST_CLASSES:
        m = (rk >= prev) & (rk < lim)
        cost[m & trad_mask] = bp * COST_PAD
        prev = lim
    return cost


def score_str(adj_close, L=5):
    """Mean-Reversion: Verlierer der letzten L Tage haben den hoechsten Score (R-H1)."""
    s = np.full(adj_close.shape, np.nan)
    with np.errstate(all="ignore"):
        s[L:] = -np.log(adj_close[L:] / adj_close[:-L])
    return s


def score_mom(adj_close, far=252, skip=21):
    """Momentum 12-1: ln(C[t-skip]/C[t-far]) (R-H2)."""
    s = np.full(adj_close.shape, np.nan)
    with np.errstate(all="ignore"):
        s[far:] = np.log(adj_close[far - skip:-skip] / adj_close[:-far]) if skip > 0 else np.log(adj_close[far:] / adj_close[:-far])
    return s


def forward_returns(adj_open, H, delay=0):
    """RET[t,i] = O[t+1+delay+H] / O[t+1+delay] - 1 (einfache Rendite); NaN wenn ein Preis fehlt oder ausserhalb."""
    T, N = adj_open.shape
    ret = np.full((T, N), np.nan)
    a = 1 + delay
    b = a + H
    if b < T:
        with np.errstate(all="ignore"):
            ret[:T - b] = adj_open[b:] / adj_open[a:T - H] - 1.0
    ret[~np.isfinite(ret)] = np.nan
    return ret


def cohorts(score, elig, ret, cost, H):
    """Eine Kohorte je Signaltag. Gibt Dict von Arrays der Laenge T zurueck (NaN = kein Signal/ungueltig).

    Long = k hoechste Scores, Short = k niedrigste (k = n//5, n = handelbare Aktien mit gueltigem Score). Gleichgewichtet.
    Aktien ohne gueltige Rendite (fehlender Entry/Exit) fallen aus dem Bein (werden gezaehlt, nicht ersetzt).
    gross_bp = 0.5*(R_long - R_short)*1e4; cost_bp = 0.5*(Kosten_long + Kosten_short) (mittlere Rundreise je Aktie);
    borrow_bp = 0.5*H*BORROW_BP_PER_DAY; net_bp = gross - cost - borrow (je Kohorte, bezogen auf Bruttokapital).
    """
    T, N = score.shape
    e = elig & np.isfinite(score)
    n = e.sum(axis=1)
    k = n // 5
    rk = ranks_ascending(np.where(e, score, np.nan))
    mL = e & (rk >= (n - k)[:, None]) & (k[:, None] > 0)
    mS = e & (rk < k[:, None])
    v = np.isfinite(ret)
    out = {}
    cnt = {}
    mean_ret = {}
    mean_cost = {}
    for name, m in (("L", mL), ("S", mS)):
        mv = m & v
        c = mv.sum(axis=1)
        with np.errstate(all="ignore"):
            mean_ret[name] = np.where(mv, ret, 0.0).sum(axis=1) / c
            mean_cost[name] = np.where(mv, np.where(np.isfinite(cost), cost, 0.0), 0.0).sum(axis=1) / c
        cnt[name] = c
    ok = (n >= MIN_ELIG) & (cnt["L"] > 0) & (cnt["S"] > 0)
    gross = 0.5 * (mean_ret["L"] - mean_ret["S"]) * 1e4
    cst = 0.5 * (mean_cost["L"] + mean_cost["S"])
    borrow = 0.5 * H * BORROW_BP_PER_DAY
    net = gross - cst - borrow
    for key, arr in (("gross_bp", gross), ("cost_bp", cst), ("net_bp", net)):
        out[key] = np.where(ok, arr, np.nan)
    out["dropped_legs"] = (mL.sum(axis=1) - cnt["L"]) + (mS.sum(axis=1) - cnt["S"])       # Namen ohne Entry-/Exit-Preis (nicht ersetzt)
    out["legs_total"] = mL.sum(axis=1) + mS.sum(axis=1)
    out["n_elig"] = n
    out["n_long"] = cnt["L"]
    out["n_short"] = cnt["S"]
    out["k"] = k
    out["ok"] = ok
    out["borrow_bp"] = borrow
    out["_mL"], out["_mS"] = mL, mS
    return out


def cohort_series(coh, H, ws, we, delay=0, cost_mult=1.0):
    """Tagesserie des Buchs: Kohorte mit Signaltag t, Entry e=t+1+delay >= ws, Exit x=e+H <= we; datiert auf x; Wert = net/H (bp je Tag).
    cost_mult skaliert Handelskosten und Leihe (Stress, verschaerfend). Gibt (x_idx, value, t_idx) zurueck."""
    T = len(coh["net_bp"])
    t = np.arange(T)
    e = t + 1 + delay
    x = e + H
    valid = coh["ok"] & (e >= ws) & (x <= we)
    gross = coh["gross_bp"]
    net = gross - cost_mult * (coh["cost_bp"] + coh["borrow_bp"])
    valid &= np.isfinite(net)
    return x[valid], net[valid] / H, t[valid]
