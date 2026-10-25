# freeze_r3_v1.py - baut das Freeze-Manifest der Welle 3 (K4, K4P, K6) und das Register-Entwurf (hashgekettet)
# Aufruf (im Repo-Wurzelordner):  python3 code/tools/freeze_r3_v1.py [--write]
# Ohne --write: nur Vorschau (Ausgabe). Mit --write: schreibt register/FREEZE_MANIFEST_R3.txt und register/TESTREGISTER_ENTWURF.jsonl.
# Das Manifest hat ein festes Textformat; FREEZE_HASH = SHA256 der Manifest-Bytes (UTF-8, LF). Texte werden vor dem Hashen
# LF-normalisiert (CRLF -> LF), Code und Daten byteweise. Unabhaengige Nachrechnung: tools/verify_freeze_r3.sh (sha256sum, openssl, node).
import sys, os, hashlib, json

ROOT = os.getcwd()
SPECS = ["RUNDE3A_SPEC_v1_FREEZEKANDIDAT.md", "RUNDE3B_SPEC_v1_FREEZEKANDIDAT.md"]
CODE = ["code/tools/k4_test_v1.py", "code/tools/k6_test_v1.py", "code/tools/count_events_v2.py", "code/tools/count_events_v3.py",
        "code/tools/count_events_v4.py", "code/tools/count_cs_v1.py", "code/tools/agg_trades_v1.py"]
DATA = ["register/MANIFEST_AGG_SHA256.txt", "register/K4P_POOL_LIQFILTER_20261025.txt", "register/K6_POOL_LIQFILTER_20261025.txt"]
PARAMS = [
    "alpha_konto N_max=20 FWER=0.05 alpha_i=0.0025 einseitig (D37); bisher verbraucht 4, mit diesem Freeze 7",
    "K4 register_index=5 alpha_i=0.0025 w=1 pairs=XBT,ETH",
    "K4P register_index=6 alpha_i=0.0025 w=1 pairs=32 (register/K4P_POOL_LIQFILTER_20261025.txt)",
    "K6 register_index=7 alpha_i=0.0025 w=1 geteilt C/R je 0.00125 pairs=34 (register/K6_POOL_LIQFILTER_20261025.txt)",
    "fenster 2019-01-01 .. 2026-06-30 (hartes Ende ab 2026-07-01 gesperrt)",
    "bootstrap blocklaenge=4 ziehungen=10000 seed=20261025; placebos zeitversatz=2000 volgematcht=500 quantil=0.975",
]

def norm(path):
    b = open(os.path.join(ROOT, path), "rb").read()
    if path.endswith((".md", ".txt")):
        b = b.replace(b"\r\n", b"\n")
    return b

def sha(b): return hashlib.sha256(b).hexdigest()

def manifest():
    lines = ["CT109-FREEZE-R3-v1"]
    for grp, files in (("spec", SPECS), ("code", CODE), ("data", DATA)):
        for f in files:
            lines.append("%s %s %s" % (grp, f, sha(norm(f))))
    for p in PARAMS: lines.append("param " + p)
    return ("\n".join(lines) + "\n").encode("utf-8")

# Altlast-Zeilen 1-4 (Quelle 01_STATUS, Hashes dort belegt) + Wellen-Zeilen 5-7 (FREEZE_HASH eintragen)
ALT = [
    dict(idx=1, test="lf1 H1 TS_MOM (BTC 24h)", markt="krypto", kind="altlast", status="NULLBEFUND", alpha_i=None,
         freeze_hash="9314688276da73ee1ab726d7f029247aaa90504a048ebb74cbf25dfcca48359c",
         result_hash="9d24018ab1f6c49fc40a762ab18d9734cd5117cb37c1899c867af10761f1f3f6", quelle="01 Stufe B 23.10.2026"),
    dict(idx=2, test="lf1 H2 SHOCK_FADE (BTC 24h)", markt="krypto", kind="altlast", status="NULLBEFUND", alpha_i=None,
         freeze_hash="9314688276da73ee1ab726d7f029247aaa90504a048ebb74cbf25dfcca48359c",
         result_hash="9d24018ab1f6c49fc40a762ab18d9734cd5117cb37c1899c867af10761f1f3f6", quelle="01 Stufe B 23.10.2026"),
    dict(idx=3, test="lf2 R-H1 STR(5), H=5 (US-Aktien Tages-Querschnitt)", markt="aktien", kind="altlast", status="NICHT NACHWEISBAR (unterpowert)", alpha_i=None,
         freeze_hash="77a6eb4405351c22e15b3e98a6d47cb9191c82a0e043c97c707fa55d7a120a51",
         result_hash="8796b17f9ca44f4e905d9ac70db1ed0b0610c5263286b78e96ca4c60846e4246", quelle="01 Stufe B 24.10.2026"),
    dict(idx=4, test="lf2 R-H2 MOM (US-Aktien Tages-Querschnitt)", markt="aktien", kind="altlast", status="NICHT NACHWEISBAR (unterpowert)", alpha_i=None,
         freeze_hash="77a6eb4405351c22e15b3e98a6d47cb9191c82a0e043c97c707fa55d7a120a51",
         result_hash="8796b17f9ca44f4e905d9ac70db1ed0b0610c5263286b78e96ca4c60846e4246", quelle="01 Stufe B 24.10.2026"),
]
def wave(freeze_hash):
    mk = lambda idx, test, a: dict(idx=idx, test=test, markt="krypto", kind="frozen", status="FROZEN", alpha_i=a,
                                   freeze_hash=freeze_hash, result_hash=None, quelle="RUNDE3A/3B Freeze-Kandidat")
    return [mk(5, "K4 AFTERSHOCK-LONG (XBT,ETH)", 0.0025), mk(6, "K4P AFTERSHOCK-LONG-ALTS (32 Paare)", 0.0025),
            mk(7, "K6 FLOW (34 Paare; C und R je 0.00125)", 0.0025)]

def chain(rows):
    prev = "0" * 64; out = []
    for r in rows:
        r = dict(r); r["prev"] = prev
        body = json.dumps(r, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        r["entry_hash"] = sha((prev + "\n" + body).encode("utf-8"))
        prev = r["entry_hash"]; out.append(r)
    return out

if __name__ == "__main__":
    m = manifest(); fh = sha(m)
    print(m.decode("utf-8")); print("FREEZE_HASH", fh)
    rows = chain(ALT + wave(fh))
    for r in rows: print(r["idx"], r["entry_hash"][:16], r["status"], r["test"])
    if "--write" in sys.argv:
        open(os.path.join(ROOT, "register/FREEZE_MANIFEST_R3.txt"), "wb").write(m)
        with open(os.path.join(ROOT, "register/TESTREGISTER_ENTWURF.jsonl"), "w", encoding="utf-8") as f:
            for r in rows: f.write(json.dumps(r, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")
        print("geschrieben")
