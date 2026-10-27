# register_result_orb_v1.py - Ergebniszeile ORB (Index 16 -> 17) in TESTREGISTER.jsonl; --append NUR nach zweitem GO.
import sys, os, json, hashlib
ROOT = os.getcwd()
def sha(b): return hashlib.sha256(b).hexdigest()
res = open(os.path.join(ROOT, "register/results/orb_final.txt"), "rb").read()
reg = os.path.join(ROOT, "register/TESTREGISTER.jsonl")
last = [json.loads(l) for l in open(reg, encoding="utf-8") if l.strip()][-1]
assert last["idx"] == 16 and last["kind"] == "frozen", "unerwarteter Registerstand"
row = dict(idx=17, test="ERGEBNIS ORB (Index 16)", markt="aktien", kind="result", alpha_i=None, freeze_hash=last["freeze_hash"], result_hash=sha(res),
           status="NICHT NACHWEISBAR (HINWEIS-Klasse; Netto-R s=5 -0.0969, z_adj -6.89; Richtungswert +0.0035 R, z_adj +0.25; Kriterien 2-4 nein)",
           quelle="orb_final.txt; 1631 Tage 2020-01-02..2026-06-30; n=32065 Trades; Datenmanifest e621660b9e8851d8555fc8dd3757f8ffdda63e050fbf08d90ca7c153210e9f7e (157 Dateien); 27.10.2026 ca. 22:15 Berlin",
           prev=last["entry_hash"])
body = json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
row["entry_hash"] = sha((row["prev"] + "\n" + body).encode("utf-8"))
print("result_hash", row["result_hash"]); print("Registerzeile idx 17 entry_hash", row["entry_hash"], "prev", row["prev"][:16])
if "--append" in sys.argv:
    with open(reg, "a", encoding="utf-8") as f: f.write(json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")
    print("Registerzeile angehaengt")
