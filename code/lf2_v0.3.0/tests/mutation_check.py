"""Mutationstest: jede Aenderung einer entscheidenden Zeile muss mindestens einen Test brechen (schnelle Tests: core + misc)."""
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

MUT = [
    ("core.py", "MIN_DV = 20e6", "MIN_DV = 2e6"),
    ("core.py", "MIN_PX = 5.0", "MIN_PX = 1.0"),
    ("core.py", "MIN_HIST = 260", "MIN_HIST = 100"),
    ("core.py", "DV_MIN_VALID = 50", "DV_MIN_VALID = 30"),
    ("core.py", "MIN_ELIG = 100", "MIN_ELIG = 50"),
    ("core.py", "COST_PAD = 1.25", "COST_PAD = 1.0"),
    ("core.py", "((100, 4.0), (300, 7.0)", "((100, 5.0), (300, 7.0)"),
    ("core.py", "((100, 4.0), (300, 7.0)", "((120, 4.0), (300, 7.0)"),
    ("core.py", "s[L:] = -np.log(", "s[L:] = np.log("),
    ("core.py", "np.log(adj_close[far - skip:-skip]", "np.log(adj_close[far:]"),
    ("core.py", "a = 1 + delay", "a = delay"),
    ("core.py", "k = n // 5", "k = n // 4"),
    ("core.py", "mS = e & (rk < k[:, None])", "mS = e & (rk <= k[:, None])"),
    ("core.py", "borrow = 0.5 * H * BORROW_BP_PER_DAY", "borrow = H * BORROW_BP_PER_DAY"),
    ("core.py", "net = gross - cst - borrow", "net = gross - cst"),
    ("core.py", "gross = 0.5 * (mean_ret[\"L\"] - mean_ret[\"S\"]) * 1e4", "gross = (mean_ret[\"L\"] - mean_ret[\"S\"]) * 1e4"),
    ("core.py", "x = e + H", "x = e"),
    ("core.py", "valid = coh[\"ok\"] & (e >= ws) & (x <= we)", "valid = coh[\"ok\"] & (e >= ws)"),
    ("core.py", "& (close_raw >= MIN_PX)", ""),
    ("core.py", "k = np.where(np.isfinite(key), key, np.inf)", "k = np.where(np.isfinite(key), key, -np.inf)"),
    ("core.py", "net = gross - cost_mult * (coh[\"cost_bp\"] + coh[\"borrow_bp\"])", "net = gross - cost_mult * coh[\"cost_bp\"] - coh[\"borrow_bp\"]"),
    ("core.py", "out[\"dropped_legs\"] = (mL.sum(axis=1) - cnt[\"L\"]) + (mS.sum(axis=1) - cnt[\"S\"])", "out[\"dropped_legs\"] = (mL.sum(axis=1) - cnt[\"L\"])"),
    ("stats.py", "Z_SUM = 3.3393", "Z_SUM = 1.96"),
    ("stats.py", "p = float(np.mean((boots - obs) >= obs))", "p = float(np.mean((boots - obs) >= 0))"),
    ("stats.py", "pvals[i] <= rank / m * q", "pvals[i] <= q"),
    ("stats.py", "lcb = float(np.quantile(boots, 0.05))", "lcb = float(np.quantile(boots, 0.5))"),
    ("stats.py", "bms.append((cs[block:] - cs[:-block]) / block)", "bms.append((cs[block:] - cs[:-block]) / (block + 1))"),
    ("protocol.py", "c7b = bool(a[\"mean_bp_day\"] > 0)", "c7b = True"),
    ("protocol.py", "r[\"c3_placebo\"] and r[\"c3b_placebo_cols\"] and r[\"c4_stress\"]", "r[\"c3_placebo\"] and r[\"c3b_placebo_cols\"]"),
    ("protocol.py", "r[\"c3_placebo\"] and r[\"c3b_placebo_cols\"] and r[\"c4_stress\"]", "r[\"c3b_placebo_cols\"] and r[\"c4_stress\"]"),
    ("protocol.py", "r[\"c3_placebo\"] and r[\"c3b_placebo_cols\"] and r[\"c4_stress\"]", "r[\"c3_placebo\"] and r[\"c4_stress\"]"),
    ("protocol.py", "\"HINWEIS-POSITIV (survivorship-behaftet)\" if core_ok else \"NULLBEFUND\"", "\"BESTAETIGT\" if core_ok else \"NULLBEFUND\""),
    ("protocol.py", "c2 = bool(r[\"mean_bp_day\"] > 0 and r[\"lcb95_bp_day\"] > 0 and rej)", "c2 = bool(r[\"mean_bp_day\"] > 0 and rej)"),
    ("protocol.py", "STRESS_COST = 1.5", "STRESS_COST = 1.2"),
    ("protocol.py", "CONC_TOP_MAX = 0.25", "CONC_TOP_MAX = 0.5"),
    ("protocol.py", "c5_names\": bool(top_share is not None and top_share <= CONC_TOP_MAX)", "c5_names\": bool(top_share is None or top_share <= CONC_TOP_MAX)"),
    ("protocol.py", "return \"P\" if rho <= GATE_P else (\"W\" if rho <= GATE_W else \"X\")", "return \"P\" if rho < GATE_P else (\"W\" if rho < GATE_W else \"X\")"),
    ("stats.py", "return max(BLOCK, 4 * int(H))", "return BLOCK"),
    ("protocol.py", "stats.summarize(segs, block=stats.block_for(H), ndraw=ndraw_boot)", "stats.summarize(segs, ndraw=ndraw_boot)"),
    ("protocol.py", "stats.boot_mean([daily], stats.block_for(H), stats.NBOOT_GATE, stats.SEED)", "stats.boot_mean([daily], stats.BLOCK, stats.NBOOT_GATE, stats.SEED)"),
    ("protocol.py", "rho = C_GATE_BP / lcb if lcb > 0", "rho = C_GATE_BP / (lcb * 2) if lcb > 0"),
    ("protocol.py", "if freeze_doc[\"payload\"][\"code_hash\"] != code_hash():", "if False:"),
    ("protocol.py", "prev_result.get(\"freeze_hash\") != freeze_doc[\"freeze_hash\"] or", "False or"),
    ("protocol.py", "prev_result.get(\"stage\") != \"discovery_A\" or", "False or"),
    ("protocol.py", "prev_result.get(\"code_hash\") != code_hash()", "False"),
    ("protocol.py", "float(np.quantile(pl, PLACEBO_Q))", "float(np.quantile(pl, 0.5))"),
    ("protocol.py", "sc, _ = series_for(ctx, hyp, wins, cost_mult=STRESS_COST)", "sc, _ = series_for(ctx, hyp, wins, cost_mult=1.0)"),
    ("protocol.py", "sl, _ = series_for(ctx, hyp, wins, delay=1)", "sl, _ = series_for(ctx, hyp, wins, delay=0)"),
    ("protocol.py", "core.cohort_series(coh, H, ws - lo, we - lo, 0, 1.0)", "core.cohort_series(coh, H, ws, we, 0, 1.0)"),
    ("protocol.py", "m = ctx.trad & np.isfinite(a)", "m = np.isfinite(a)"),
    ("protocol.py", "if man.get(\"spec_hash\") != SPEC_SHA256:", "if False:"),
    ("protocol.py", "if man.get(\"manifest_hash\") != json_hash({k: v for k, v in man.items() if k != \"manifest_hash\"}):", "if False:"),
    ("protocol.py", "sel = coh[\"ok\"] & (t + 1 >= ws) & (t + 1 + H <= we)", "sel = coh[\"ok\"] & (t + 1 >= ws)"),
    ("util.py", "body = f.read().replace(b\"\\r\\n\", b\"\\n\")", "body = f.read()"),
    ("protocol.py", "top = float(np.sort(contrib)[::-1][:CONC_TOP].sum())", "top = float(np.sort(contrib)[::-1][:CONC_TOP].sum()) / 2"),
    ("protocol.py", "if not write_once(lock, json.dumps(state, sort_keys=True) + \"\\n\"):", "if False:"),
    ("protocol.py", "if old.get(\"status\") not in (\"failed\", \"running\"):", "if False:"),
    ("protocol.py", "sc = real[:, rng.permutation(real.shape[1])]", "sc = real"),
    ("protocol.py", "gate_doc.get(\"manifest_hash\") != man.get(\"manifest_hash\") or", "False or"),
    ("protocol.py", "if gate_doc.get(\"code_hash\") != code_hash():", "if False:"),
    ("protocol.py", "elif os.path.exists(p):", "elif False:"),
    ("protocol.py", "if [r[\"id\"] for r in res_b] != [a[\"id\"] for a in res_a_d]:", "if False:"),
    ("protocol.py", "if os.path.exists(res_path):\n        raise StageError(\"Stufe %s hat bereits ein Ergebnis\" % stage)", "if False:\n        raise StageError(\"x\")"),
    ("cli.py", "if not os.path.exists(os.path.join(a.data, \"qcount_S.json\")):", "if False:"),
    ("cli.py", "if not os.path.exists(os.path.join(a.data, \"gate_result_S.json\")):", "if False:"),
    ("cli.py", "or not _check_specs(a.specs)", "or False"),
    ("protocol.py", "sc = rng.random(trad.shape)", "sc = np.tile(np.arange(trad.shape[1], dtype=float), (trad.shape[0], 1))"),
    ("protocol.py", "if freeze_doc.get(\"freeze_hash\") != json_hash(freeze_doc[\"payload\"]):", "if False:"),
]
FAST = ["tests.test_lf2_core", "tests.test_lf2_misc"]
PLACEBO_FAST = {("protocol.py", "keys = rng.random(trad.shape)")}
SLOW = ["tests.test_lf2_e2e"]


def main():
    survived = []
    only = [int(x) for x in os.environ.get("MUT_ONLY", "").split(",") if x]
    for i, (fn, old, new) in enumerate(MUT, 1):
        if only and i not in only:
            continue
        tmp = tempfile.mkdtemp()
        shutil.copytree(os.path.join(ROOT, "lf2"), os.path.join(tmp, "lf2"), ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(os.path.join(ROOT, "tests"), os.path.join(tmp, "tests"), ignore=shutil.ignore_patterns("__pycache__"))
        p = os.path.join(tmp, "lf2", fn)
        src = open(p, encoding="utf-8").read()
        if src.count(old) < 1:
            print("MUTATION %d: Muster nicht gefunden: %s" % (i, old)); survived.append((i, "kein Treffer")); continue
        open(p, "w", encoding="utf-8").write(src.replace(old, new, 1))
        r = subprocess.run([sys.executable, "-W", "ignore", "-m", "unittest"] + FAST, cwd=tmp, capture_output=True, text=True)
        killed = r.returncode != 0
        how = "schnell"
        if not killed:
            r = subprocess.run([sys.executable, "-W", "ignore", "-m", "unittest"] + SLOW, cwd=tmp, capture_output=True, text=True)
            killed = r.returncode != 0
            how = "e2e"
        print("MUTATION %2d %-12s %s (%s) -> %s" % (i, fn, "getoetet" if killed else "UEBERLEBT", how, old[:60]), flush=True)
        if not killed:
            survived.append((i, old))
        shutil.rmtree(tmp, ignore_errors=True)
    print("Mutationen: %d, getoetet: %d, ueberlebt: %d" % (len(MUT), len(MUT) - len(survived), len(survived)))
    return 1 if survived else 0


if __name__ == "__main__":
    sys.exit(main())
