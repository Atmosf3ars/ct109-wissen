# freeze_gs_v1.py - Freeze-Manifest GOLD-SILBER (HINWEIS-Klasse) und Registerzeile (hashgekettet an TESTREGISTER.jsonl)
# Aufruf (Repo-Wurzel): python3 code/tools/freeze_gs_v1.py [--write] [--append]
#   ohne Optionen: Vorschau; --write: schreibt register/FREEZE_MANIFEST_GS.txt; --append: haengt die Registerzeile an (NUR nach GO).
import sys, os, json, hashlib
ROOT = os.getcwd()
SPECS = ["RUNDE3D_SPEC_v1_GS_FREEZEKANDIDAT.md"]
CODE = ["code/tools/gs_test_v1.py", "code/tools/count_gs_v1.py"]
DATA = ["register/MANIFEST_GS_DATA_SHA256.txt"]
PARAMS = ["klasse HINWEIS kein alpha_konto; alpha_konto bleibt 7/20 (D37)",
          "GS-C und GS-R wochenweise, kosten=6bp je Woche, beta=OLS 52 Wochen, signal=sign(Spread Vorwoche)",
          "fenster 2016-01-04 .. 2026-06-30 (hartes Ende ab 2026-07-01 gesperrt)",
          "bootstrap blocklaenge=4 ziehungen=10000 seed=20261025 einseitig p<=0.05; placebos zeitversatz=2000 quantil=0.975"]
def sha(b): return hashlib.sha256(b).hexdigest()
def norm(p):
    b = open(os.path.join(ROOT, p), "rb").read()
    return b.replace(b"\r\n", b"\n") if p.endswith((".md", ".txt")) else b
def manifest():
    lines = ["CT109-FREEZE-GS-v1"]
    for g, fs in (("spec", SPECS), ("code", CODE), ("data", DATA)):
        for f in fs: lines.append("%s %s %s" % (g, f, sha(norm(f))))
    for p in PARAMS: lines.append("param " + p)
    return ("\n".join(lines) + "\n").encode("utf-8")
if __name__ == "__main__":
    m = manifest(); fh = sha(m); print(m.decode("utf-8")); print("FREEZE_HASH", fh)
    reg = os.path.join(ROOT, "register/TESTREGISTER.jsonl")
    last = [json.loads(l) for l in open(reg, encoding="utf-8") if l.strip()][-1]
    row = dict(idx=12, test="GS GOLD-SILBER wochenweise (GS-C und GS-R), HINWEIS-Klasse", markt="aktien-etf", kind="frozen",
               status="FROZEN-HINWEIS (kein alpha)", alpha_i=None, freeze_hash=fh, result_hash=None, quelle="RUNDE3D_SPEC_v1", prev=last["entry_hash"])
    body = json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    row["entry_hash"] = sha((row["prev"] + "\n" + body).encode("utf-8"))
    print("Registerzeile idx 12 entry_hash", row["entry_hash"], "prev", row["prev"][:16])
    if "--write" in sys.argv: open(os.path.join(ROOT, "register/FREEZE_MANIFEST_GS.txt"), "wb").write(m); print("Manifest geschrieben")
    if "--append" in sys.argv:
        with open(reg, "a", encoding="utf-8") as f: f.write(json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")
        print("Registerzeile angehaengt")
