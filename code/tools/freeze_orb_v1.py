# freeze_orb_v1.py - Freeze-Manifest ORB (HINWEIS-Klasse) und Registerzeile (hashgekettet an TESTREGISTER.jsonl)
# Aufruf (Repo-Wurzel): python3 code/tools/freeze_orb_v1.py [--write] [--append]   (--append NUR nach GO)
import sys, os, json, hashlib
ROOT = os.getcwd()
SPECS = ["RUNDE3F_SPEC_v1_ORB_FREEZEKANDIDAT.md"]
CODE = ["code/tools/orb_test_v1.py", "code/tools/orb_select_v2.py", "code/tools/alpaca_intraday_v1.py", "code/tools/alpaca_day5_v1.py", "code/tools/alpaca_daily_v1.py",
        "code/tools/orb_dev_sim_v1.py", "code/tools/orb_dev_sim_v2.py", "code/tools/orb_select_v1.py", "code/tools/orb_first5_count_v1.py", "code/tools/orb_count_v2.py",
        "code/tools/alpaca_universe_v1.py", "code/tools/form4_symbols_v1.py"]
DATA = ["register/results/orb_dev_sim_v1_out.txt", "register/results/orb_dev_sim_v2_out.txt", "register/results/orb_first5_out.txt", "register/results/orb_count_v2b_out.txt"]
PARAMS = ["klasse HINWEIS kein alpha_konto; alpha_konto bleibt 7/20 (D37)",
          "regel top20 je tag nach RV5 (erste kerze / mittel 14 vortage, >=10), signal 09:30 kerzenrichtung, einstieg open naechste bar, stop gegenende, ziel 10R, schluss letzte bar",
          "kosten provision 0.70 USD je round-trip ticket 1500 USD, slippage 5bp je seite primaer, 0 und 10 berichtet",
          "fenster test 2020-01-02 .. 2026-06-30, hartes ende ab 2026-07-01 gesperrt, halften A 2020-2022 B 2023-2026H1",
          "bootstrap tagesbloecke L=5 zirkulaer ziehungen=10000 seed=20261026 zadj=m/(1.3*SE)>=1.645; n>=20000; richtungswert>0 zadj>=1.645; beide halften netto>0",
          "kategorien HINWEIS-POSITIV | NICHT NACHWEISBAR | INSUFFICIENT, kein BESTAETIGT"]
def sha(b): return hashlib.sha256(b).hexdigest()
def norm(p):
    b = open(os.path.join(ROOT, p), "rb").read()
    return b.replace(b"\r\n", b"\n") if p.endswith((".md", ".txt")) else b
def manifest():
    lines = ["CT109-FREEZE-ORB-v1"]
    for g, fs in (("spec", SPECS), ("code", CODE), ("data", DATA)):
        for f in fs: lines.append("%s %s %s" % (g, f, sha(norm(f))))
    for p in PARAMS: lines.append("param " + p)
    return ("\n".join(lines) + "\n").encode("utf-8")
if __name__ == "__main__":
    m = manifest(); fh = sha(m); print(m.decode("utf-8")); print("FREEZE_HASH", fh)
    reg = os.path.join(ROOT, "register/TESTREGISTER.jsonl")
    last = [json.loads(l) for l in open(reg, encoding="utf-8") if l.strip()][-1]
    row = dict(idx=last["idx"] + 1, test="ORB Stocks-in-Play Top-20 RV5 US-Aktien, HINWEIS-Klasse", markt="aktien", kind="frozen",
               status="FROZEN-HINWEIS (kein alpha)", alpha_i=None, freeze_hash=fh, result_hash=None, quelle="RUNDE3F_SPEC_v1", prev=last["entry_hash"])
    body = json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    row["entry_hash"] = sha((row["prev"] + "\n" + body).encode("utf-8"))
    print("Registerzeile idx %d entry_hash %s prev %s" % (row["idx"], row["entry_hash"], row["prev"][:16]))
    if "--write" in sys.argv: open(os.path.join(ROOT, "register/FREEZE_MANIFEST_ORB.txt"), "wb").write(m); print("Manifest geschrieben")
    if "--append" in sys.argv:
        with open(reg, "a", encoding="utf-8") as f: f.write(json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")
        print("Registerzeile angehaengt")
