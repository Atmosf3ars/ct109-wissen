# freeze_carry_v1.py - Freeze-Manifest CARRY-HOLD (HINWEIS-Klasse) und Registerzeile (hashgekettet an TESTREGISTER.jsonl)
# Aufruf (Repo-Wurzel): python3 code/tools/freeze_carry_v1.py [--write] [--append]
#   ohne Optionen: Vorschau; --write: schreibt register/FREEZE_MANIFEST_CARRY.txt; --append: haengt die Registerzeile an (NUR nach GO).
import sys, os, json, hashlib
ROOT = os.getcwd()
SPECS = ["RUNDE3E_SPEC_v1_CARRYHOLD_FREEZEKANDIDAT.md"]
CODE = ["code/tools/carry_test_v1.py", "code/tools/carry_null_v1.py", "code/tools/carry_acf_v1.py", "code/tools/carry_train_v1.py", "code/tools/basis_probe_v1.py"]
DATA = ["register/MANIFEST_CARRY_DATA_SHA256.txt"]
PARAMS = ["klasse HINWEIS kein alpha_konto; alpha_konto bleibt 7/20 (D37)",
          "regel F7=mittel Tagesfunding d-7..d-1 annualisiert, einstieg F7>10%, ausstieg F7<3%, BTCUSDT+ETHUSDT je 50%, spot long perp short",
          "kosten basis 90bp je phase (2x40 spot maker + 2x5 perp), stress 170bp, kollateralreibung 0.5bp je woche in position",
          "fenster test 2024-01-01 .. 2026-06-28 (130 wochen), hartes ende ab 2026-07-01 gesperrt",
          "bootstrap blocklaenge=8 ziehungen=10000 seed=20261025 zadj=m/(1.5*SE)>=1.645; zustand RV30 BTC hoch/niedrig beide>0 je >=10 wochen; stress>0",
          "placebo zufallsplaene=2000 nur berichtet"]
def sha(b): return hashlib.sha256(b).hexdigest()
def norm(p):
    b = open(os.path.join(ROOT, p), "rb").read()
    return b.replace(b"\r\n", b"\n") if p.endswith((".md", ".txt")) else b
def manifest():
    lines = ["CT109-FREEZE-CARRY-v1"]
    for g, fs in (("spec", SPECS), ("code", CODE), ("data", DATA)):
        for f in fs: lines.append("%s %s %s" % (g, f, sha(norm(f))))
    for p in PARAMS: lines.append("param " + p)
    return ("\n".join(lines) + "\n").encode("utf-8")
if __name__ == "__main__":
    m = manifest(); fh = sha(m); print(m.decode("utf-8")); print("FREEZE_HASH", fh)
    reg = os.path.join(ROOT, "register/TESTREGISTER.jsonl")
    last = [json.loads(l) for l in open(reg, encoding="utf-8") if l.strip()][-1]
    row = dict(idx=last["idx"] + 1, test="CARRY-HOLD Binance-Proxy BTC+ETH, HINWEIS-Klasse", markt="krypto", kind="frozen",
               status="FROZEN-HINWEIS (kein alpha)", alpha_i=None, freeze_hash=fh, result_hash=None, quelle="RUNDE3E_SPEC_v1", prev=last["entry_hash"])
    body = json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    row["entry_hash"] = sha((row["prev"] + "\n" + body).encode("utf-8"))
    print("Registerzeile idx %d entry_hash %s prev %s" % (row["idx"], row["entry_hash"], row["prev"][:16]))
    if "--write" in sys.argv: open(os.path.join(ROOT, "register/FREEZE_MANIFEST_CARRY.txt"), "wb").write(m); print("Manifest geschrieben")
    if "--append" in sys.argv:
        with open(reg, "a", encoding="utf-8") as f: f.write(json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")
        print("Registerzeile angehaengt")
