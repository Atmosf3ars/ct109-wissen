"""Hashes, kanonisches JSON, Spec-Pruefung, Code-Hash."""
import hashlib
import json
import os

SPEC_SHA256 = "acaed785b2a0e7b5e7fa2f74565e6d1b5250e1ef793a3d5c768d6771d59d5be7"
SEED = 20261022


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(path, chunk=1 << 22):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def canon_json(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def json_hash(obj):
    return sha256_bytes(canon_json(obj).encode("utf-8"))


def check_spec(path):
    """GATE_SPEC_v1.md muss den eingefrorenen Hash haben.

    Akzeptiert wird der Hash der Rohdatei oder der Hash mit LF-Zeilenenden
    (Windows/Git kann CRLF erzeugen). Gibt immer beide Hashes zurueck.
    """
    with open(path, "rb") as f:
        raw = f.read()
    h_raw = sha256_bytes(raw)
    h_lf = sha256_bytes(raw.replace(b"\r\n", b"\n"))
    ok = SPEC_SHA256 in (h_raw, h_lf)
    return {
        "expected": SPEC_SHA256,
        "sha256_raw": h_raw,
        "sha256_lf_normalized": h_lf,
        "ok": ok,
        "matched": "raw" if h_raw == SPEC_SHA256 else ("lf_normalized" if h_lf == SPEC_SHA256 else None),
    }


def code_hash(pkg_dir=None):
    """SHA-256 ueber alle .py-Dateien des Pakets (Name + LF-normalisierter Inhalt)."""
    if pkg_dir is None:
        pkg_dir = os.path.dirname(os.path.abspath(__file__))
    h = hashlib.sha256()
    for name in sorted(os.listdir(pkg_dir)):
        if name.endswith(".py"):
            with open(os.path.join(pkg_dir, name), "rb") as f:
                body = f.read().replace(b"\r\n", b"\n")
            h.update(name.encode("utf-8") + b"\0" + body + b"\0")
    return h.hexdigest()
