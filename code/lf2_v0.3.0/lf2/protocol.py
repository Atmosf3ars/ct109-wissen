"""Protokoll (RUNDE2_SPEC_v1 R2-R8): Q-Zaehler, Gate S, Freeze, Stufen D und B. Ausgabe nur Aggregate."""
import json
import os

import numpy as np

from . import core, stats
from .data import load_panel, window_bounds
from .util import code_hash, json_hash, sha256_bytes, sha256_file, write_once

SPEC_SHA256 = "09b6ca179575ead1604b6e87f014d55ef3b91a36b9bb5386f80bf5d021ec6c56"       # RUNDE2_SPEC_v1.md (LF-normalisiert)
GATE_SPEC_SHA256 = "acaed785b2a0e7b5e7fa2f74565e6d1b5250e1ef793a3d5c768d6771d59d5be7"
BAU_SPEC_V2_SHA256 = "34d6add4f7c4dbbf0dbcab5311c29f3981382d0885da32d8e8c11354c720e068"

WINDOWS = {"A": (20120103, 20191231), "E": (20050103, 20111230), "F": (20200102, 20260630)}
HYPOTHESES = [
    {"id": "R-H1", "rule": "STR", "params": {"L": 5}, "H": 5, "category": "Mean-Reversion"},
    {"id": "R-H2", "rule": "MOM", "params": {"far": 252, "skip": 21}, "H": 21, "category": "Momentum"},
]
C_GATE_BP = 1.25 * 7.0
GATE_P, GATE_W = 0.05, 0.10
STRESS_COST = 1.5
NPLACEBO = 1000
CONC_TOP = 10
CONC_TOP_MAX = 0.25
CONC_YEAR_MAX = 0.40
STAGE_CODE = {"discovery_A": 1, "confirm": 2}


def _norm_spec_hash(path):
    with open(path, "rb") as f:
        raw = f.read()
    return sha256_bytes(raw.replace(b"\r\n", b"\n"))


def hyp_score(hyp, C):
    if hyp["rule"] == "STR":
        return core.score_str(C, hyp["params"]["L"])
    if hyp["rule"] == "MOM":
        return core.score_mom(C, hyp["params"]["far"], hyp["params"]["skip"])
    raise ValueError("unbekannte Regel")


class Context:
    """Rechenkontext: Panel, Handelbarkeit, Kosten; Scores und Renditen werden je Bedarf berechnet und gemerkt."""

    def __init__(self, panel):
        self.p = panel
        self.dates = panel["dates"]
        self.trad, self.med = core.tradable(panel["CL"], panel["V"])
        self.cost = core.cost_matrix(self.trad, self.med)
        self._score, self._ret = {}, {}
        self.bounds = {k: window_bounds(self.dates, a, b) for k, (a, b) in WINDOWS.items()}

    def score(self, hyp):
        if hyp["id"] not in self._score:
            self._score[hyp["id"]] = hyp_score(hyp, self.p["C"])
        return self._score[hyp["id"]]

    def ret(self, H, delay=0):
        key = (H, delay)
        if key not in self._ret:
            self._ret[key] = core.forward_returns(self.p["O"], H, delay)
        return self._ret[key]


def series_for(ctx, hyp, wins, delay=0, cost_mult=1.0, score=None):
    """Tagesserien je Fenster. Gibt Liste von (x_idx, werte, t_idx, coh) je Fenster zurueck."""
    H = hyp["H"]
    sc = ctx.score(hyp) if score is None else score
    coh = core.cohorts(sc, ctx.trad, ctx.ret(H, delay), ctx.cost, H)
    out = []
    for w in wins:
        ws, we = ctx.bounds[w]
        x, v, t = core.cohort_series(coh, H, ws, we, delay, cost_mult)
        out.append((x, v, t))
    return out, coh


PLACEBO_Q = 0.95


def placebo_threshold(pl):
    """Schwelle fuer C3/C3b: 95-%-Quantil der Placebo-Mittel."""
    return float(np.quantile(pl, PLACEBO_Q)) if len(pl) else None


def _placebo(ctx, hyp, wins, ndraw, seed, mode):
    H = hyp["H"]
    ret = ctx.ret(H, 0)
    lo = max(0, min(ctx.bounds[w][0] for w in wins) - 1)
    hi = max(ctx.bounds[w][1] for w in wins) + 1
    sl = slice(lo, hi + 1)
    trad, cost, ret_s = ctx.trad[sl], ctx.cost[sl], ret[sl]
    real = ctx.score(hyp)[sl] if mode == "cols" else None
    rng = np.random.default_rng(seed)
    means = np.empty(ndraw)
    for i in range(ndraw):
        if mode == "days":
            sc = rng.random(trad.shape)                              # je Tag unabhaengige Zufallsordnung (Spec R6 C3)
        else:
            sc = real[:, rng.permutation(real.shape[1])]            # echte Score-Pfade, Aktienzuordnung zufaellig (zeitlich persistent; Nachtrag N2)
        coh = core.cohorts(sc, trad, ret_s, cost, H)
        vals = []
        for w in wins:
            ws, we = ctx.bounds[w]
            x, v, t = core.cohort_series(coh, H, ws - lo, we - lo, 0, 1.0)
            vals.append(v)
        means[i] = float(np.mean(np.concatenate(vals))) if vals and sum(len(v) for v in vals) else np.nan
    return means


def placebo_means(ctx, hyp, wins, ndraw, seed):
    """Placebo C3 (Spec R6): je Tag werden die Scores innerhalb des Tages zufaellig permutiert, alles andere gleich."""
    return _placebo(ctx, hyp, wins, ndraw, seed, "days")


def placebo_means_cols(ctx, hyp, wins, ndraw, seed):
    """Placebo C3b (Nachtrag N2, zusaetzlich zu C3): die echten Score-Zeitreihen werden den Aktien zufaellig neu zugeordnet. Behaelt Persistenz
    und Querschnittsstruktur der Scores, zerstoert nur den Bezug zu den Renditen; ist (anders als C3) fuer persistente Scores kalibriert."""
    return _placebo(ctx, hyp, wins, ndraw, seed, "cols")


def stress_means(ctx, hyp, wins):
    """C4a (Kosten und Leihe x STRESS_COST) und C4b (1 Tag Verzug): Netto-Mittel in bp/Tag."""
    sc, _ = series_for(ctx, hyp, wins, cost_mult=STRESS_COST)
    sl, _ = series_for(ctx, hyp, wins, delay=1)
    return (float(np.mean(np.concatenate([v for _, v, _ in sc]))), float(np.mean(np.concatenate([v for _, v, _ in sl]))))


def concentration(ctx, hyp, wins, coh, net_series):
    """C5: Anteil der 10 groessten Namensbeitraege am Bruttogewinn und groesster Jahresanteil am Gesamtnetto."""
    H = hyp["H"]
    ret = ctx.ret(H, 0)
    T, N = ret.shape
    contrib = np.zeros(N)
    mL, mS = coh["_mL"], coh["_mS"]
    v = np.isfinite(ret)
    cL = (mL & v).sum(axis=1)
    cS = (mS & v).sum(axis=1)
    for w in wins:
        ws, we = ctx.bounds[w]
        t = np.arange(T)
        sel = coh["ok"] & (t + 1 >= ws) & (t + 1 + H <= we)
        wL = np.where(mL & v, 1.0, 0.0) / np.maximum(cL, 1)[:, None]
        wS = np.where(mS & v, 1.0, 0.0) / np.maximum(cS, 1)[:, None]
        r = np.where(v, ret, 0.0)
        contrib += (0.5 * (wL - wS) * r * 1e4 / H)[sel].sum(axis=0)
    total = float(contrib.sum())
    top = float(np.sort(contrib)[::-1][:CONC_TOP].sum())
    top_share = (top / total) if total > 0 else None
    # Jahresanteile (Austrittsjahr) am Gesamtnetto
    years = {}
    for x, vals, _ in net_series:
        for xi, val in zip(x, vals):
            y = int(ctx.dates[xi]) // 10000
            years[y] = years.get(y, 0.0) + float(val)
    tot_net = sum(years.values())
    year_share = (max(years.values()) / tot_net) if (years and tot_net > 0) else None
    return {"gross_total_bp_day_sum": total, "top10_share": top_share, "max_year_share": year_share,
            "total_net_sum": tot_net,
            "c5_names": bool(top_share is not None and top_share <= CONC_TOP_MAX),
            "c5_year": bool(year_share is None or year_share <= CONC_YEAR_MAX)}


def evaluate_set(ctx, hyp, wins, stage, hyp_index, ndraw_boot=stats.NBOOT, nplacebo=NPLACEBO):
    """Alle Kennzahlen einer Hypothese auf der Fenstermenge `wins`."""
    base, coh = series_for(ctx, hyp, wins)
    H = hyp["H"]
    segs = [v for _, v, _ in base]
    summ = stats.summarize(segs, block=stats.block_for(H), ndraw=ndraw_boot)
    per_win = {w: {"n_days": int(len(v)), "mean_bp_day": (float(np.mean(v)) if len(v) else None)} for w, (_, v, _) in zip(wins, base)}
    seed0 = stats.SEED + 1000 * hyp_index + 10 * STAGE_CODE[stage]
    pl = placebo_means(ctx, hyp, wins, nplacebo, seed0)
    pl = pl[np.isfinite(pl)]
    q95 = placebo_threshold(pl)
    plc = placebo_means_cols(ctx, hyp, wins, nplacebo, seed0 + 1)
    plc = plc[np.isfinite(plc)]
    q95c = placebo_threshold(plc)
    m_cost, m_lat = stress_means(ctx, hyp, wins)
    conc = concentration(ctx, hyp, wins, coh, base)
    T = len(coh["ok"])
    t = np.arange(T)
    inwin = np.zeros(T, bool)
    for w in wins:
        ws, we = ctx.bounds[w]
        inwin |= (t + 1 >= ws) & (t + 1 + H <= we)
    used = inwin & coh["ok"]
    legs = float(coh["legs_total"][used].sum())
    res = {"id": hyp["id"], "windows": wins, "per_window": per_win, **summ,
           "gross_mean_bp_day": float(np.mean(np.concatenate([(coh["gross_bp"][tt] / H) for _, _, tt in base]))),
           "placebo_mean_bp_day": float(np.mean(pl)) if len(pl) else None, "placebo_q95_bp_day": q95,
           "placebo_cols_mean_bp_day": float(np.mean(plc)) if len(plc) else None, "placebo_cols_q95_bp_day": q95c,
           "stress_cost_net_bp_day": m_cost, "stress_latency_net_bp_day": m_lat,
           "n_cohort_days_no_signal": int((inwin & ~coh["ok"]).sum()), "n_cohort_days_used": int(used.sum()),
           "mean_n_elig": float(np.mean(coh["n_elig"][used])) if used.any() else None,
           "dropped_leg_share": (float(coh["dropped_legs"][used].sum()) / legs) if legs > 0 else None,
           "c3_placebo": bool(q95 is not None and summ["mean_bp_day"] > q95),
           "c3b_placebo_cols": bool(q95c is not None and summ["mean_bp_day"] > q95c),
           "c4_stress": bool(m_cost > 0 and m_lat > 0),
           **conc}
    return res


def decide_stage_b(res_b, res_a_d):
    """Entscheidungsregeln R6/R7 fuer beide Hypothesen (BH ueber m = 2). res_b/res_a_d: Listen in gleicher Reihenfolge."""
    if [r["id"] for r in res_b] != [a["id"] for a in res_a_d]:
        raise ValueError("Hypothesen-IDs von Stufe D und B stimmen nicht ueberein")
    pv = [r["p"] for r in res_b]
    bh = stats.bh_reject(pv, stats.Q_FDR)
    out = []
    for r, a, rej in zip(res_b, res_a_d, bh):
        bonf = bool(r["p"] <= 0.05 / len(res_b))
        c2 = bool(r["mean_bp_day"] > 0 and r["lcb95_bp_day"] > 0 and rej)
        c7a = bool(r["per_window"]["E"]["mean_bp_day"] is not None and r["per_window"]["E"]["mean_bp_day"] > 0
                   and r["per_window"]["F"]["mean_bp_day"] is not None and r["per_window"]["F"]["mean_bp_day"] > 0)
        c7b = bool(a["mean_bp_day"] > 0)
        c5 = bool(r["c5_names"] and r["c5_year"])
        core_ok = bool(c2 and r["c3_placebo"] and r["c3b_placebo_cols"] and r["c4_stress"] and c5 and c7a and c7b)
        cat = "HINWEIS-POSITIV (survivorship-behaftet)" if core_ok else "NULLBEFUND"      # R7: nie BESTAETIGT
        out.append({"id": r["id"], "bh_reject": bool(rej), "bonferroni_reject": bonf, "c1_power": r["c1_power"], "c2_signif": c2,
                    "c3_placebo": r["c3_placebo"], "c3b_placebo_cols": r["c3b_placebo_cols"], "c4_stress": r["c4_stress"], "c5_conc": c5, "c7a_epoch": c7a,
                    "c7b_regime_a": c7b, "core_ok_without_c1": core_ok,
                    "category": cat, "would_be_bestaetigt_if_survivorship_free": bool(core_ok and r["c1_power"])})
    return out


# ------------------------------------------------------------------ Q-Zaehler und Gate

def qcount(panel_dir, universe, manifest_doc):
    """Nur Zaehler (Spec R8 Schritt 4)."""
    syms = universe["symbols"]
    man = manifest_doc["manifest"]["symbols"]
    st = {}
    for s in syms:
        st[man.get(s, {"status": "fehlt"})["status"]] = st.get(man.get(s, {"status": "fehlt"})["status"], 0) + 1
    panel = load_panel(panel_dir, syms)
    ctx = Context(panel)
    N = len(panel["symbols"])
    first = [int(np.argmax(np.isfinite(panel["O"][:, j]))) for j in range(N)]
    last = [int(len(panel["dates"]) - 1 - np.argmax(np.isfinite(panel["O"][::-1, j]))) for j in range(N)]
    delisted_like = sum(1 for l in last if int(panel["dates"][l]) < 20260601)
    rep = {"symbols_in_universe": len(syms), "manifest_status": st, "stocks_loaded": N, "calendar_days": int(len(panel["dates"])),
           "calendar_first": int(panel["dates"][0]), "calendar_last": int(panel["dates"][-1]), "dropped_rows_not_in_calendar": int(panel["dropped_rows"]),
           "stocks_last_date_before_20260601": int(delisted_like),
           "stocks_with_history_from_start": int(sum(1 for f in first if int(panel["dates"][f]) <= 20050110)),
           "nan_share_open": float(np.mean(~np.isfinite(panel["O"])))}
    # Tage und Luecken je Symbol (nur Verteilungen, keine Einzelreihen)
    O = panel["O"]
    days = np.isfinite(O).sum(axis=0)
    span = np.array([max(1, l - f + 1) for f, l in zip(first, last)])
    gaps = span - days                                              # Kalendertage zwischen erstem und letztem Preis ohne Open
    rep["days_per_symbol"] = {"min": int(days.min()), "median": float(np.median(days)), "max": int(days.max())}
    rep["gap_days_per_symbol"] = {"symbols_with_gaps": int((gaps > 0).sum()), "total_gap_days": int(gaps.sum()), "max": int(gaps.max())}
    with np.errstate(all="ignore"):
        jump = np.abs(O[1:] / np.where(np.isfinite(panel["C"][:-1]), panel["C"][:-1], np.nan) - 1.0)
    rep["open_vs_prev_adjclose_gt_50pct_count"] = int(np.nansum(jump > 0.5))      # nur gezaehlt, nichts gefiltert (Bad-Tick-Hinweis)
    rep["open_vs_prev_adjclose_gt_25pct_count"] = int(np.nansum(jump > 0.25))
    for w, (ws, we) in ctx.bounds.items():
        ne = ctx.trad[ws:we + 1].sum(axis=1)
        rep["tradable_%s" % w] = {"days": int(we - ws + 1), "min": int(ne.min()), "median": int(np.median(ne)), "max": int(ne.max()),
                                  "days_below_%d" % core.MIN_ELIG: int((ne < core.MIN_ELIG).sum())}
    # SPY-Regime (beschreibend, R3): Median RV30 je Fenster
    spy = panel["spy_close"]
    lr = np.diff(np.log(spy), prepend=np.nan)
    rv = np.full(len(spy), np.nan)
    for t in range(30, len(spy)):
        seg = lr[t - 29:t + 1]
        if np.all(np.isfinite(seg)):
            rv[t] = np.sqrt(365) * np.std(seg, ddof=1)
    rep["spy_rv30_median"] = {w: float(np.nanmedian(rv[ws:we + 1])) for w, (ws, we) in ctx.bounds.items()}
    return rep


def classify_rho(rho):
    """Gate-Klassen (R2): P wenn rho <= 0,05; W wenn <= 0,10; sonst X."""
    return "P" if rho <= GATE_P else ("W" if rho <= GATE_W else "X")


def gate_cell(daily, H):
    """LCB95 des mittleren |r_H| (Blockbootstrap, Blocklaenge nach N1) und Klasse."""
    boots, _, _ = stats.boot_mean([daily], stats.block_for(H), stats.NBOOT_GATE, stats.SEED)
    lcb = float(np.quantile(boots, 0.05))
    rho = C_GATE_BP / lcb if lcb > 0 else float("inf")
    return {"block": stats.block_for(H), "lcb95_bp": lcb, "rho_min_plus": float(rho), "class": classify_rho(rho)}


def gate_s(panel_dir, universe, manifest_doc=None, universe_sha=None):
    """Gate S (R2): nur Betraege. rho_min+ = c_gate / LCB95(E|r_H|) im Fenster A, fuer H = 5 und 21."""
    panel = load_panel(panel_dir, universe["symbols"])
    ctx = Context(panel)
    ws, we = ctx.bounds["A"]
    res = {}
    for H in (5, 21):
        ret = ctx.ret(H, 0)
        t = np.arange(ret.shape[0])
        sel = (t + 1 >= ws) & (t + 1 + H <= we)
        a = np.abs(ret) * 1e4
        m = ctx.trad & np.isfinite(a)
        m = m & sel[:, None]
        cnt = m.sum(axis=1)
        s = np.where(m, a, 0.0).sum(axis=1)
        daily = (s[cnt > 0] / cnt[cnt > 0])
        cell = gate_cell(daily, H)
        res["H%d" % H] = dict(cell, H=H, n_days=int(len(daily)), n_obs=int(m.sum()),
                              e_abs_r_bp=float(np.sum(np.where(m, a, 0.0)) / max(1, m.sum())), c_gate_bp=C_GATE_BP)
    doc = {"tool": "lf2.gate", "code_hash": code_hash(), "spec_sha256": SPEC_SHA256, "window": "A", "cells": res,
           "manifest_hash": (manifest_doc or {}).get("manifest_hash"), "universe_json_sha256": universe_sha,
           "admissible": sorted(k for k, v in res.items() if v["class"] in ("P", "W"))}
    doc["result_hash"] = json_hash({k: v for k, v in doc.items() if k != "result_hash"})
    return doc


# ------------------------------------------------------------------ Freeze

class FreezeError(Exception):
    pass


def data_manifest_check(price_dir, manifest_doc, symbols):
    """C6: Status 'ok' <=> Datei vorhanden mit dem im Manifest genannten SHA-256. Jede vorhandene Datei eines Universum-Symbols ohne Status 'ok'
    ist ein Befund (der Lader wuerde sie sonst lesen)."""
    bad = []
    for s in symbols:
        m = manifest_doc["manifest"]["symbols"].get(s)
        p = os.path.join(price_dir, s + ".csv")
        if m is None:
            bad.append((s, "nicht im Manifest"))
        elif m["status"] == "ok":
            if not os.path.exists(p) or sha256_file(p) != m["sha256"]:
                bad.append((s, "Hash"))
        elif os.path.exists(p):
            bad.append((s, "Datei trotz Status %s" % m["status"]))
    return bad


def make_freeze(universe_path, manifest_path, gate_doc, price_dir):
    with open(universe_path, encoding="utf-8") as f:
        uni = json.load(f)
    with open(manifest_path, encoding="utf-8") as f:
        man = json.load(f)
    if gate_doc.get("spec_sha256") != SPEC_SHA256 or gate_doc.get("result_hash") != json_hash({k: v for k, v in gate_doc.items() if k != "result_hash"}):
        raise FreezeError("Gate-Ergebnis passt nicht zur Spec oder ist veraendert")
    if gate_doc.get("code_hash") != code_hash():
        raise FreezeError("Gate-Ergebnis stammt von anderem Code")
    if gate_doc.get("manifest_hash") != man.get("manifest_hash") or gate_doc.get("universe_json_sha256") != sha256_file(universe_path):
        raise FreezeError("Gate-Ergebnis gehoert zu anderen Daten")
    cells = gate_doc["cells"]
    bad_cells = [h["id"] for h in HYPOTHESES if cells.get("H%d" % h["H"], {}).get("class") not in ("P", "W")]
    if bad_cells:
        raise FreezeError("Zelle nicht zulaessig fuer: %s" % ",".join(bad_cells))
    n_w = sum(1 for h in HYPOTHESES if cells["H%d" % h["H"]]["class"] == "W")
    if n_w > 2 or len(HYPOTHESES) > 2:
        raise FreezeError("zu viele Hypothesen fuer die Zellklassen")
    bad = data_manifest_check(price_dir, man, uni["symbols"])
    if bad:
        raise FreezeError("Datenabweichung: %s" % bad[:5])
    if man.get("spec_hash") != SPEC_SHA256:
        raise FreezeError("Manifest gehoert zu anderer Spec")
    if man.get("manifest_hash") != json_hash({k: v for k, v in man.items() if k != "manifest_hash"}):
        raise FreezeError("Manifest-Hash stimmt nicht (Manifest veraendert)")
    if man.get("universe_hash") != sha256_file(universe_path):
        raise FreezeError("Manifest gehoert zu anderem Universum")
    payload = {"hypotheses": HYPOTHESES, "windows": WINDOWS, "spec_hashes": {"runde2": SPEC_SHA256, "gate_spec": GATE_SPEC_SHA256, "bau_spec_v2": BAU_SPEC_V2_SHA256},
               "universe_json_sha256": sha256_file(universe_path), "manifest_hash": man["manifest_hash"], "manifest_file_sha256": sha256_file(manifest_path),
               "gate_result_hash": gate_doc["result_hash"], "gate_classes": {k: v["class"] for k, v in cells.items()},
               "code_hash": code_hash(),
               "protocol": {"min_dv": core.MIN_DV, "min_px": core.MIN_PX, "min_hist": core.MIN_HIST, "dv_win": core.DV_WIN, "dv_min_valid": core.DV_MIN_VALID,
                            "min_elig": core.MIN_ELIG, "cost_classes": [[a if a != float("inf") else "inf", b] for a, b in core.COST_CLASSES],
                            "cost_pad": core.COST_PAD, "borrow_bp_per_day": core.BORROW_BP_PER_DAY, "stress_cost": STRESS_COST,
                            "block": stats.BLOCK, "block_rule": "max(block, 4*H) (Nachtrag N1)", "placebo_q": PLACEBO_Q, "placebo_cols": "C3b (Nachtrag N2)", "nboot": stats.NBOOT, "nplacebo": NPLACEBO, "seed": stats.SEED, "delta_min": stats.DELTA_MIN,
                            "z_sum": stats.Z_SUM, "q_fdr": stats.Q_FDR, "conc_top": CONC_TOP, "conc_top_max": CONC_TOP_MAX, "conc_year_max": CONC_YEAR_MAX},
               "limits": {"n": len(HYPOTHESES), "n_class_W": n_w}}
    return payload, json_hash(payload)


# ------------------------------------------------------------------ Stufen

class StageError(Exception):
    pass


def verify_freeze(freeze_doc):
    if freeze_doc.get("freeze_hash") != json_hash(freeze_doc["payload"]):
        raise StageError("freeze_hash stimmt nicht")
    if freeze_doc["payload"]["code_hash"] != code_hash():
        raise StageError("Code weicht vom Freeze ab")
    return freeze_doc["payload"]


def run_stage(stage, freeze_doc, universe_path, manifest_path, price_dir, out_dir, prev_result=None, nplacebo=NPLACEBO, nboot=stats.NBOOT, log=print, retry=False):
    """Einmalige Stufe. Verweigert bei vorhandener Sperre oder abweichenden Eingaben. Ergebnis = Aggregate + result_hash."""
    payload = verify_freeze(freeze_doc)
    if payload["universe_json_sha256"] != sha256_file(universe_path) or payload["manifest_file_sha256"] != sha256_file(manifest_path):
        raise StageError("Universum/Manifest weichen vom Freeze ab")
    with open(universe_path, encoding="utf-8") as f:
        uni = json.load(f)
    with open(manifest_path, encoding="utf-8") as f:
        man = json.load(f)
    bad = data_manifest_check(price_dir, man, uni["symbols"])
    if bad:
        raise StageError("C6: Daten weichen vom Manifest ab: %s" % bad[:5])
    if stage not in STAGE_CODE:
        raise StageError("unbekannte Stufe")
    os.makedirs(out_dir, exist_ok=True)
    lock = os.path.join(out_dir, "lock_%s" % stage)
    res_path = os.path.join(out_dir, "result_%s.json" % stage)
    if os.path.exists(res_path):
        raise StageError("Stufe %s hat bereits ein Ergebnis" % stage)
    if stage == "confirm":
        if prev_result is None or prev_result.get("result_hash") != json_hash({k: v for k, v in prev_result.items() if k not in ("run_utc", "result_hash")}):
            raise StageError("Ergebnis der Stufe D fehlt oder ist veraendert")
        if prev_result.get("freeze_hash") != freeze_doc["freeze_hash"] or prev_result.get("stage") != "discovery_A" or prev_result.get("code_hash") != code_hash():
            raise StageError("Stufe D gehoert zu anderem Freeze, anderer Stufe oder anderem Code")
    state = {"freeze_hash": freeze_doc["freeze_hash"], "code_hash": code_hash(), "status": "running", "attempts": 1, "history": []}
    if not write_once(lock, json.dumps(state, sort_keys=True) + "\n"):
        if not retry:
            raise StageError("Stufe %s wurde bereits gestartet (Sperre vorhanden); nur bei technischem Fehler mit --retry wiederholbar, Sperre bleibt protokolliert" % stage)
        with open(lock, encoding="utf-8") as f:
            old = json.load(f)
        if old.get("freeze_hash") != state["freeze_hash"] or old.get("code_hash") != state["code_hash"]:
            raise StageError("Sperre gehoert zu anderem Freeze/Code")
        if old.get("status") not in ("failed", "running"):
            raise StageError("Sperre hat Status %s: keine Wiederholung" % old.get("status"))
        state = dict(old, status="running", attempts=int(old.get("attempts", 1)) + 1, history=list(old.get("history", [])) + [{"status": old.get("status"), "error": old.get("error")}])
        _rewrite_lock(lock, state)
    try:
        return _run_stage_body(stage, freeze_doc, payload, uni, price_dir, res_path, prev_result, nplacebo, nboot, log, lock, state)
    except BaseException as e:
        state = dict(state, status="failed", error="%s: %s" % (type(e).__name__, str(e)[:200]))
        _rewrite_lock(lock, state)
        raise


def _rewrite_lock(lock, state):
    tmp = lock + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(state, sort_keys=True) + "\n")
    os.replace(tmp, lock)


def _run_stage_body(stage, freeze_doc, payload, uni, price_dir, res_path, prev_result, nplacebo, nboot, log, lock, state):
    log("lade Daten ...")
    panel = load_panel(price_dir, uni["symbols"])
    ctx = Context(panel)
    wins = ["A"] if stage == "discovery_A" else ["E", "F"]
    results = []
    for i, hyp in enumerate(HYPOTHESES):
        log("rechne %s ..." % hyp["id"])
        results.append(evaluate_set(ctx, hyp, wins, stage, i, ndraw_boot=nboot, nplacebo=nplacebo))
    doc = {"tool": "lf2.backtest", "stage": stage, "freeze_hash": freeze_doc["freeze_hash"], "code_hash": code_hash(),
           "manifest_hash": payload["manifest_hash"], "stocks_loaded": len(panel["symbols"]), "results": results}
    if stage == "confirm":
        doc["prev_result_hash"] = prev_result["result_hash"]
        a_res = prev_result["results"]
        doc["decision"] = decide_stage_b(results, a_res)
    else:
        doc["note"] = "beschreibend (Stufe D): keine Kategorie"
    doc["result_hash"] = json_hash(doc)
    doc["run_utc"] = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if not write_once(res_path, json.dumps(doc, sort_keys=True, indent=1) + "\n"):
        raise StageError("Ergebnisdatei existiert bereits")
    _rewrite_lock(lock, dict(state, status="done"))
    return doc
