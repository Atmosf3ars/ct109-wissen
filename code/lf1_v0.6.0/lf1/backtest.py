"""lf1.backtest: Freeze, Einmal-Lauf und Entscheidungsregeln C1-C5 (BAU_SPEC_S1S3_v1 S2.4-S2.6).

Reine Rechnung auf bereits geladenen Gittern (Arrays). Kein Netzwerk, keine Broker-Module.
Ein Lauf braucht den Freeze-Hash der Liste; ein zweiter Lauf mit gleichem Hash wird verweigert
(Ausnahme: technischer Fehler bei identischem Code). Ergebnisse tragen einen Ergebnis-Hash.

Zeit: Signale nutzen nur Daten <= Entscheidungsbar; die Fenster (s, e) begrenzen nur die Trades
(Ein- und Ausstieg liegen im Fenster); Vorlauf vor s darf fuer Lookback benutzt werden (Vergangenheit).
"""
import datetime as dt
import json
import math
import os
from statistics import NormalDist

import numpy as np

from . import core
from .gate import ALPHA_PRIME, ASSETS, BETA, C0_BP, COST_FACTOR, FUND_BP_PER_8H, HORIZONS_H, c_gate
from .util import SEED, SPEC_SHA256, code_hash, json_hash

MAX_HYP = 8
MAX_W_HYP = 2
NBOOT_P = 5000
NPLACEBO = 1000
CONC_TOP = 5
CONC_MAX = 0.5
STRESS_COST = 1.5
Q_FDR = 0.05
EPOCH_SPLIT_UTC = "2021-01-01"   # Spec v2 V2.2: E1 = Start bis 2020-12-31, E2 = ab 2021-01-01
E1_COST_FACTOR = 2.0             # Annahme A14 (nicht gemessen, konservativ)
EPOCH_MISSING_MAX = 0.05         # A16
EPOCH_GAP_MAX_H = 24             # A16
MAX_LOOKBACK = 336          # Bars Vorlauf vor dem Fenster; Regelparameter duerfen nicht weiter zurueckgreifen

RULES = {
    "BREAKOUT": {"L": int, "side": str},
    "TS_MOM": {"L": int, "side": str},
    "SHOCK_FADE": {"w": int, "k": float, "N": int},
}
SIDES = ("long", "short", "both")


class FreezeError(Exception):
    pass


# ----------------------------------------------------------------------------- Hypothesen

def validate_hypothesis(h):
    """Prueft Form und Wertebereich einer Hypothese. Wirft FreezeError."""
    for key in ("id", "rule", "params", "asset", "H"):
        if key not in h:
            raise FreezeError("Hypothese ohne Feld %r" % key)
    if set(h) != {"id", "rule", "params", "asset", "H"}:
        raise FreezeError("Hypothese %s hat unzulaessige Zusatzfelder" % h.get("id"))
    if h["rule"] not in RULES:
        raise FreezeError("unbekannter Regeltyp %r" % h["rule"])
    spec = RULES[h["rule"]]
    p = h["params"]
    if set(p) != set(spec):
        raise FreezeError("Parameter von %s muessen genau %s sein" % (h["id"], sorted(spec)))
    for k, typ in spec.items():
        v = p[k]
        if typ is float:
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0:
                raise FreezeError("%s.%s muss eine positive Zahl sein" % (h["id"], k))
        elif typ is int:
            if isinstance(v, bool) or not isinstance(v, int) or v < 1:
                raise FreezeError("%s.%s muss eine ganze Zahl >= 1 sein" % (h["id"], k))
        else:
            if v not in SIDES:
                raise FreezeError("%s.side muss in %s liegen" % (h["id"], SIDES))
    if h["rule"] == "SHOCK_FADE" and p["N"] < 2:
        raise FreezeError("SHOCK_FADE.N muss >= 2 sein")
    look = p["N"] + p["w"] if h["rule"] == "SHOCK_FADE" else p["L"]
    if look > MAX_LOOKBACK:
        raise FreezeError("%s: Rueckblick %d Bars > %d" % (h["id"], look, MAX_LOOKBACK))
    if h["asset"] not in ASSETS:
        raise FreezeError("Asset %r ausserhalb des Gate-Universums" % h["asset"])
    if h["H"] not in HORIZONS_H:
        raise FreezeError("Horizont %r ausserhalb der Gate-Horizonte" % h["H"])
    return True


def gate_cell(gate_result, asset, H):
    for c in gate_result["cells"]:
        if c["asset"] == asset and c["h_hours"] == H:
            return c
    raise FreezeError("Gate-Ergebnis hat keine Zelle (%s, %s)" % (asset, H))


def validate_list(hyps, gate_result):
    """Liste <= 8, eindeutige IDs, jede Hypothese nur in zulaessiger Zelle, Klasse-W-Hypothesen <= 2 (Gate-Spec §6)."""
    if not 1 <= len(hyps) <= MAX_HYP:
        raise FreezeError("Anzahl Hypothesen muss 1..%d sein" % MAX_HYP)
    ids = [h["id"] for h in hyps]
    if len(set(ids)) != len(ids):
        raise FreezeError("Hypothesen-IDs nicht eindeutig")
    n_w = 0
    for h in hyps:
        validate_hypothesis(h)
        cell = gate_cell(gate_result, h["asset"], h["H"])
        if cell["class"] not in ("P", "W") or not cell.get("evaluable", False):
            raise FreezeError("Zelle (%s, %s h) ist gesperrt (Klasse %s)" % (h["asset"], h["H"], cell["class"]))
        if cell["class"] == "W":
            n_w += 1
    if n_w > MAX_W_HYP:
        raise FreezeError("Mehr als %d Hypothesen in Klasse-W-Zellen" % MAX_W_HYP)
    return {"n": len(hyps), "n_class_W": n_w}


def cost_for(asset, mult=1.0):
    return core.gate_consistent_cost(C0_BP[asset], mult=mult)


def make_freeze(hyps, gate_result, regime_hash, bau_spec_sha256, windows_desc, data_manifest, pkg_dir=None):
    """Baut die Freeze-Nutzlast (S2.4/S2.6) und ihren Hash. Schreibt MDE und max. Trade-Zahl je Hypothese mit."""
    info = validate_list(hyps, gate_result)
    per_hyp = []
    for h in hyps:
        cell = gate_cell(gate_result, h["asset"], h["H"])
        per_hyp.append({
            "id": h["id"], "gate_class": cell["class"],
            "mde_net_bp_full_exposure": cell["mde_net_bp_full_exposure"],
            "max_trades_in_gate_window": int(cell["n_eff"]),
            "c_gate_bp": c_gate(h["asset"], h["H"]),
        })
    payload = {
        "hypotheses": hyps,
        "per_hypothesis_protocol": per_hyp,
        "cost_model": {"c0_bp": C0_BP, "factor": COST_FACTOR, "funding_bp_per_8h": FUND_BP_PER_8H},
        "regime_hash": regime_hash,
        "gate_result_hash": gate_result["result_hash"],
        "seeds": {"base": SEED},
        "code_hash": code_hash(pkg_dir),
        "data_manifest": data_manifest,
        "spec_hashes": {"gate_spec": SPEC_SHA256, "bau_spec": bau_spec_sha256},
        "windows": windows_desc,
        "protocol": {
            "nboot_p": NBOOT_P, "nplacebo": NPLACEBO, "q_fdr": Q_FDR, "conc_top": CONC_TOP, "conc_max": CONC_MAX,
            "stress_cost": STRESS_COST, "latency_stress_bars": 1,
            "epoch_split_utc": EPOCH_SPLIT_UTC, "e1_cost_factor": E1_COST_FACTOR,
            "epoch_missing_max": EPOCH_MISSING_MAX, "epoch_gap_max_h": EPOCH_GAP_MAX_H,
        },
        "limits": info,
    }
    return payload, json_hash(payload)


# ----------------------------------------------------------------------------- Handel

def build_signals(h, grid):
    p = h["params"]
    if h["rule"] == "BREAKOUT":
        return core.signals_breakout(grid["h"], grid["l"], grid["c"], p["L"], p["side"])
    if h["rule"] == "TS_MOM":
        return core.signals_ts_mom(grid["c"], p["L"], p["side"])
    return core.signals_shock_fade(grid["c"], p["w"], float(p["k"]), p["N"])


def trades_for(h, grid, windows, cost, latency_bars=0, sig=None):
    """Trades der Hypothese; je Fenster unabhaengig (kein Trade ueber Fenstergrenzen). Indizes global."""
    if sig is None:
        sig = build_signals(h, grid)
    out = []
    for s, e in windows:
        t = core.simulate(grid["o"][s:e], sig[s:e], h["H"], cost, latency_bars, 1.0)
        if len(t):
            t = t.copy()
            t["i_dec"] += s
            t["i_entry"] += s
            t["i_exit"] += s
            out.append(t)
    return np.concatenate(out) if out else np.zeros(0, dtype=core.TRADE_DTYPE)


# ----------------------------------------------------------------------------- Statistik

def epoch_cost_factor(n, t0_ts, step_s=3600):
    """Kostenfaktor je Gitterindex (Einstiegsbar): E1 -> E1_COST_FACTOR, ab Epochengrenze 1.0."""
    split = split_index(t0_ts, n, step_s)
    f = np.ones(n)
    f[:split] = E1_COST_FACTOR
    return f


def split_index(t0_ts, n, step_s=3600):
    import datetime as _dt
    y, m, d = (int(x) for x in EPOCH_SPLIT_UTC.split("-"))
    ts = int(_dt.datetime(y, m, d, tzinfo=_dt.timezone.utc).timestamp())
    return int(min(max((ts - t0_ts) // step_s, 0), n))


def adjust_epoch_costs(trades, cost, H, cf):
    """Zieht den Zusatz (Faktor-1)*Kosten der Epoche vom Netto ab (Faktor bezieht sich auf die Einstiegsbar)."""
    if len(trades) == 0 or cf is None:
        return trades
    t = trades.copy()
    extra = (cf[t["i_entry"].astype(np.int64)] - 1.0) * cost.cost_bp(H)
    t["cost_bp"] = t["cost_bp"] + extra
    t["net_bp"] = t["net_bp"] - extra
    return t


def epoch_quality(present, windows, split):
    """Q-Pflicht V2.2 je Epoche (nur Zaehler). present: bool je Gitterbar. Epoche ungueltig bei Fehlend > 5 % oder Luecke > 24 h."""
    out = {}
    for name, (a, b) in (("E1", (None, split)), ("E2", (split, None))):
        lo = min(s_ for s_, _e in windows)
        hi = max(e_ for _s, e_ in windows)
        s_i = max(lo, a if a is not None else lo)
        e_i = min(hi, b if b is not None else hi)
        if e_i <= s_i:
            out[name] = {"expected_bars": 0, "present_bars": 0, "missing_pct": None, "max_gap_h": None, "valid": False, "reason": "leer"}
            continue
        idx = np.flatnonzero(present[s_i:e_i])
        if len(idx) == 0:
            out[name] = {"expected_bars": int(e_i - s_i), "present_bars": 0, "missing_pct": 100.0, "max_gap_h": None, "valid": False, "reason": "keine Daten"}
            continue
        first, last = int(idx[0]) + s_i, int(idx[-1]) + s_i
        exp = last - first + 1
        pres = int(present[first:last + 1].sum())
        gaps = np.diff(np.flatnonzero(present[first:last + 1]))
        mg = int(gaps.max() - 1) if len(gaps) else 0
        miss = 100.0 * (exp - pres) / exp
        ok = (miss <= 100 * EPOCH_MISSING_MAX) and (mg <= EPOCH_GAP_MAX_H)
        out[name] = {"first_idx": first, "last_idx": last, "expected_bars": int(exp), "present_bars": pres,
                     "missing_pct": round(miss, 4), "max_gap_h": mg, "valid": bool(ok),
                     "reason": None if ok else "Fehlend>%d%% oder Luecke>%dh" % (100 * EPOCH_MISSING_MAX, EPOCH_GAP_MAX_H)}
    return out


def n_min(sigma_bp, delta_bp):
    z = NormalDist().inv_cdf
    s = z(1 - ALPHA_PRIME) + z(1 - BETA)
    return int(math.ceil((s * sigma_bp / delta_bp) ** 2))


def mde_bp(sigma_bp, n):
    z = NormalDist().inv_cdf
    return (z(1 - ALPHA_PRIME) + z(1 - BETA)) * sigma_bp / math.sqrt(n)


def block_len(H, trades, windows):
    """max(2, ceil(6*H / mittlerer Abstand der Einstiege in Bars)); Abstaende nur zwischen Trades im selben Fenster."""
    if len(trades) < 2:
        return 2
    starts = np.array(sorted(s for s, _e in windows), dtype=np.int64)
    ent = trades["i_entry"].astype(np.int64)
    wid = np.searchsorted(starts, ent, side="right") - 1
    d = np.diff(ent)
    same = wid[1:] == wid[:-1]
    d = d[same]
    spacing = float(np.mean(d)) if len(d) else float(H)
    return max(2, int(math.ceil(6.0 * H / max(spacing, 1.0))))


def _boot_means(x, b, nboot, rng, batch=500):
    n = len(x)
    b = max(1, min(b, n))
    nb = int(math.ceil(n / b))
    out = np.empty(nboot)
    ar = np.arange(b)
    done = 0
    while done < nboot:
        m = min(batch, nboot - done)
        starts = rng.integers(0, n - b + 1, size=(m, nb))
        idx = (starts[:, :, None] + ar[None, None, :]).reshape(m, nb * b)[:, :n]
        out[done:done + m] = x[idx].mean(axis=1)
        done += m
    return out


def block_bootstrap(net, block, nboot, rng):
    """Einseitiger p-Wert fuer H0: E[net] <= 0 (zentrierte Bootstrap-Verteilung) und untere 95-%-Grenze der Expectancy."""
    x = np.asarray(net, dtype=float)
    n = len(x)
    if n < 2:
        return {"p": 1.0, "lcb95": None, "mean": float(x.mean()) if n else None}
    mean = float(x.mean())
    null = _boot_means(x - mean, block, nboot, rng)
    p = float((np.sum(null >= mean) + 1) / (nboot + 1))
    alt = _boot_means(x, block, nboot, rng)
    return {"p": p, "lcb95": float(np.quantile(alt, 0.05)), "mean": mean}


def bh_fdr(pvals, q=Q_FDR):
    """Benjamini-Hochberg-Step-up. Gibt Liste bool (Ablehnung von H0) in Eingabereihenfolge zurueck."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: (pvals[i], i))
    kmax = 0
    for rank, i in enumerate(order, start=1):
        if pvals[i] <= rank / m * q:
            kmax = rank
    rej = [False] * m
    for rank, i in enumerate(order, start=1):
        if rank <= kmax:
            rej[i] = True
    return rej


def bonferroni(pvals, alpha=0.05):
    m = len(pvals)
    return [p <= alpha / m for p in pvals]


def top_share(net, k=CONC_TOP):
    """Anteil der k besten Trades an der Netto-Summe; None bei Summe <= 0."""
    x = np.sort(np.asarray(net, dtype=float))[::-1]
    tot = float(x.sum())
    if tot <= 0 or len(x) == 0:
        return None
    return float(x[:k].sum() / tot)


def placebo_means(h, grid, windows, trades, cost, latency_bars, nsim, rng, cost_factor=None):
    """Zufallseinstiegs-Zwillinge: gleiche H, gleiche Trade-Zahl, gleiche Richtungsverteilung, gleiche Fenster.

    Kandidaten: alle Entscheidungsbars mit gueltigem Ein-/Ausstieg im Fenster. Zwillinge duerfen sich
    ueberlappen (der Mittelwert wird dadurch nicht verzerrt); die Richtungen sind eine Zufallsumordnung
    der echten Trades.
    """
    n = len(trades)
    if n == 0:
        return None
    o = grid["o"]
    H = h["H"]
    ent, ext = [], []
    for s, e in windows:
        i = np.arange(s, e)
        ee = i + 1 + latency_bars
        xx = ee + H
        ok = xx < e
        i, ee, xx = i[ok], ee[ok], xx[ok]
        good = np.isfinite(o[ee]) & np.isfinite(o[xx]) & (o[ee] > 0) & (o[xx] > 0)
        ent.append(ee[good])
        ext.append(xx[good])
    ent = np.concatenate(ent) if ent else np.zeros(0, dtype=np.int64)
    ext = np.concatenate(ext) if ext else np.zeros(0, dtype=np.int64)
    m = len(ent)
    if m < n:
        return None
    ret = (o[ext] / o[ent] - 1.0) * 1e4
    cb = cost.cost_bp(H) * (np.ones(m) if cost_factor is None else np.asarray(cost_factor, dtype=float)[ent])
    sides = trades["side"].astype(np.float64)
    means = np.empty(nsim)
    for k in range(nsim):
        pick = rng.choice(m, size=n, replace=False)
        sd = rng.permutation(sides)
        means[k] = float(np.mean(sd * ret[pick]) - np.mean(cb[pick]))
    return means


# ----------------------------------------------------------------------------- Auswertung

def _rng(freeze_hash, idx, stream):
    return np.random.default_rng([int(freeze_hash[:16], 16), int(idx), int(stream)])


def evaluate_hypothesis(h, idx, grid, windows, freeze_hash, nboot=NBOOT_P, nplacebo=NPLACEBO, cost_factor=None, split_idx=None):
    """Berechnet Kennzahlen und die Einzelkriterien C1, C3, C4, C5 sowie p-Wert/LCB fuer C2."""
    asset = h["asset"]
    cost = cost_for(asset)
    sig = build_signals(h, grid)
    tr = adjust_epoch_costs(trades_for(h, grid, windows, cost, 0, sig), cost, h["H"], cost_factor)
    n = len(tr)
    res = {"id": h["id"], "n_trades": n}
    if n == 0:
        res.update({"net_mean_bp": None, "c1_power": False, "c1_reason": "keine Trades", "p": 1.0, "lcb95_bp": None,
                    "c3_placebo": False, "c4_stress": False, "c5_conc": False})
        return res
    net = tr["net_bp"].astype(float)
    gross = tr["gross_bp"].astype(float)
    sigma = float(np.sqrt(np.mean(gross ** 2)))
    delta = c_gate(asset, h["H"])
    nm = n_min(sigma, delta)
    res.update({
        "net_mean_bp": float(net.mean()), "gross_mean_bp": float(gross.mean()),
        "sigma_trade_bp": sigma, "delta_min_bp": delta, "n_min": nm,
        "mde_bp_at_n": mde_bp(sigma, n),
        "c1_power": bool(n >= nm),
        "n_long": int((tr["side"] > 0).sum()), "n_short": int((tr["side"] < 0).sum()),
    })
    bl = block_len(h["H"], tr, windows)
    bb = block_bootstrap(net, bl, nboot, _rng(freeze_hash, idx, 1))
    res.update({"block_len_trades": bl, "p": bb["p"], "lcb95_bp": bb["lcb95"]})
    # C3 Placebo
    pm = placebo_means(h, grid, windows, tr, cost, 0, nplacebo, _rng(freeze_hash, idx, 2), cost_factor)
    if pm is None:
        res.update({"c3_placebo": False, "placebo_q95_bp": None})
    else:
        q95 = float(np.quantile(pm, 0.95))
        res.update({"placebo_q95_bp": q95, "placebo_mean_bp": float(pm.mean()), "c3_placebo": bool(net.mean() > q95)})
    # C4 Stress: Einstieg +1 Bar und Kosten x1.5
    t_lat = adjust_epoch_costs(trades_for(h, grid, windows, cost, 1, sig), cost, h["H"], cost_factor)
    c15 = cost_for(asset, STRESS_COST)
    t_cost = adjust_epoch_costs(trades_for(h, grid, windows, c15, 0, sig), c15, h["H"], cost_factor)
    res["stress_latency_net_bp"] = float(t_lat["net_bp"].mean()) if len(t_lat) else None
    res["stress_cost_net_bp"] = float(t_cost["net_bp"].mean()) if len(t_cost) else None
    res["c4_stress"] = bool(len(t_lat) and len(t_cost) and res["stress_latency_net_bp"] > 0 and res["stress_cost_net_bp"] > 0)
    # C5 Konzentration
    ts = top_share(net)
    res["top5_share"] = ts
    res["c5_conc"] = bool(ts is not None and ts <= CONC_MAX)
    if split_idx is not None:
        m2 = tr["i_entry"] >= split_idx
        res["e2_n"] = int(m2.sum())
        res["e2_net_mean_bp"] = float(net[m2].mean()) if m2.any() else None
        res["c7a_epoch"] = bool(m2.any() and res["e2_net_mean_bp"] > 0)
    return res


def decide(results, hyps_ids):
    """C2 (BH-FDR ueber die ganze Liste + Bonferroni-Gegenprobe) und Gesamtentscheidung. Aendert results in place."""
    by_id = {r["id"]: r for r in results}
    ps = [by_id[i]["p"] for i in hyps_ids]
    bh = bh_fdr(ps, Q_FDR)
    bf = bonferroni(ps, 0.05)
    cands = []
    for i, (hid, rej, bfr) in enumerate(zip(hyps_ids, bh, bf)):
        r = by_id[hid]
        r["bh_reject"] = bool(rej)
        r["bonferroni_reject"] = bool(bfr)
        r["c2_signif"] = bool(rej and r.get("lcb95_bp") is not None and r["lcb95_bp"] > 0)
        r["passes_all"] = bool(r.get("c1_power") and r["c2_signif"] and r.get("c3_placebo")
                               and r.get("c4_stress") and r.get("c5_conc"))
        if r["passes_all"]:
            cands.append((hid, i, r["lcb95_bp"]))
    if not cands:
        return None
    cands.sort(key=lambda t: (-t[2], t[1]))
    return cands[0][0]


CATEGORIES = ("BESTAETIGT", "POSITIV-UNTERPOWERT", "NULLBEFUND")


def decide_confirm(results, hyps_ids, a_net_means):
    """Spec v2 V2.3: BH-FDR ueber die Liste (m = Anzahl Hypothesen), C7a/C7b, Kategorien. Aendert results in place.

    a_net_means: Hypothese -> Netto-Mittel aus Stufe D (oder None). Gibt Liste der Hypothesen mit BESTAETIGT zurueck."""
    by_id = {r["id"]: r for r in results}
    ps = [by_id[i]["p"] for i in hyps_ids]
    bh = bh_fdr(ps, Q_FDR)
    bf = bonferroni(ps, 0.05)
    confirmed = []
    for hid, rej, bfr in zip(hyps_ids, bh, bf):
        r = by_id[hid]
        r["bh_reject"] = bool(rej)
        r["bonferroni_reject"] = bool(bfr)
        r["c2_signif"] = bool(rej and r.get("lcb95_bp") is not None and r["lcb95_bp"] > 0)
        a = a_net_means.get(hid)
        r["a_net_mean_bp"] = a
        r["c7b_regime_a"] = bool(a is not None and a > 0)
        r["c7a_epoch"] = bool(r.get("c7a_epoch", False))
        core = bool(r["c2_signif"] and r.get("c3_placebo") and r.get("c4_stress") and r.get("c5_conc")
                    and r["c7a_epoch"] and r["c7b_regime_a"])
        r["core_ok_without_c1"] = core
        if core and r.get("c1_power"):
            r["category"] = "BESTAETIGT"
            confirmed.append(hid)
        elif core:
            r["category"] = "POSITIV-UNTERPOWERT"
        else:
            r["category"] = "NULLBEFUND"
    return confirmed


# ----------------------------------------------------------------------------- Lauf

def _now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)


def _acquire(path, freeze_hash, code_h):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            lk = json.load(f)
        if lk.get("status") == "error" and lk.get("freeze_hash") == freeze_hash and lk.get("code_hash") == code_h:
            lk["status"] = "started"
            lk["attempts"] = int(lk.get("attempts", 1)) + 1
            lk["restarted_utc"] = _now()
            _write_json(path, lk)
            return
        raise FreezeError("Lauf ist einmalig: Sperre vorhanden (status=%s). Wiederholung nur nach technischem Fehler "
                          "mit identischem Freeze- und Code-Hash." % lk.get("status"))
    _write_json(path, {"status": "started", "freeze_hash": freeze_hash, "code_hash": code_h,
                       "started_utc": _now(), "attempts": 1})


def run_stage(stage, payload, freeze_hash, grids, windows, out_dir, pkg_dir=None, extras=None):
    """Fuehrt eine Stufe aus (z. B. 'discovery_A' oder 'confirm'). grids: Asset -> {o,h,l,c}; windows: Asset -> [(s,e)]."""
    if json_hash(payload) != freeze_hash:
        raise FreezeError("Freeze-Hash passt nicht zur Nutzlast (Liste oder Parameter geaendert)")
    ch = code_hash(pkg_dir)
    if payload.get("code_hash") != ch:
        raise FreezeError("Code-Hash weicht vom Freeze ab (C6): kein Lauf")
    hyps = payload["hypotheses"]
    for h in hyps:
        validate_hypothesis(h)
    if len(hyps) > MAX_HYP:
        raise FreezeError("zu viele Hypothesen")
    os.makedirs(out_dir, exist_ok=True)
    mode = "B" if stage == "confirm" else ("D" if stage.startswith("discovery") else "generic")
    a_means, d_hash = {}, None
    if mode == "B":
        if not extras or "cost_factor" not in extras or "split_idx" not in extras:
            raise FreezeError("Stufe confirm braucht Epochen-Angaben (Kostenfaktor, Epochengrenze)")
        dpath = os.path.join(out_dir, "bt_result_discovery_A.json")
        if not os.path.exists(dpath):
            raise FreezeError("Stufe confirm verlangt zuerst Stufe D (bt_result_discovery_A.json fehlt)")
        with open(dpath, encoding="utf-8") as f:
            dres = json.load(f)
        if dres.get("freeze_hash") != freeze_hash or json_hash({k: v for k, v in dres.items() if k not in ("run_utc", "result_hash")}) != dres.get("result_hash"):
            raise FreezeError("Ergebnis der Stufe D passt nicht zum Freeze oder wurde veraendert")
        a_means = {r["id"]: r.get("net_mean_bp") for r in dres["results"]}
        d_hash = dres["result_hash"]
    lock = os.path.join(out_dir, "bt_lock_%s.json" % stage)
    _acquire(lock, freeze_hash, ch)
    try:
        results = []
        for idx, h in enumerate(hyps):
            kw = {}
            if mode == "B":
                kw = {"cost_factor": extras["cost_factor"][h["asset"]], "split_idx": extras["split_idx"][h["asset"]]}
            results.append(evaluate_hypothesis(h, idx, grids[h["asset"]], windows[h["asset"]], freeze_hash, **kw))
        ids = [h["id"] for h in hyps]
        cand = decide(results, ids) if mode != "B" else None
        confirmed = decide_confirm(results, ids, a_means) if mode == "B" else None
        if mode == "B":
            verdict = "BESTAETIGT" if confirmed else ("POSITIV-UNTERPOWERT" if any(r["category"] == "POSITIV-UNTERPOWERT" for r in results) else "NULLBEFUND")
        elif mode == "D":
            verdict = "BESCHREIBEND"
            cand = None
        else:
            verdict = "KANDIDAT" if cand else "NULLBEFUND"
        result = {
            "tool": "lf1.backtest", "stage": stage, "freeze_hash": freeze_hash, "code_hash": ch,
            "results": results, "candidate": cand, "confirmed": confirmed, "stage_d_result_hash": d_hash,
            "epoch_quality": (extras or {}).get("epoch_quality"), "window_e": (extras or {}).get("window_e"),
            "verdict": verdict,
            "c6_process": {"code_hash_matches_freeze": True,
                           "extern_pruefen": ["Testsuite gruen", "Mutationsliste >= 15", "kein Eingriff nach dem Freeze"]},
            "run_utc": _now(),
        }
        result["result_hash"] = json_hash({k: v for k, v in result.items() if k != "run_utc"})
        _write_json(os.path.join(out_dir, "bt_result_%s.json" % stage), result)
        with open(lock, encoding="utf-8") as f:
            lk = json.load(f)
        lk.update({"status": "done", "result_hash": result["result_hash"], "finished_utc": _now()})
        _write_json(lock, lk)
        return result
    except Exception as e:
        with open(lock, encoding="utf-8") as f:
            lk = json.load(f)
        lk.update({"status": "error", "error_class": type(e).__name__, "error_utc": _now()})
        _write_json(lock, lk)
        raise
