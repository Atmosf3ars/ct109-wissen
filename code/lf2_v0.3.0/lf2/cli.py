"""lf2 Kommandozeile: universe | fetch | qcount | gate | freeze | backtest."""
import argparse
import json
import os
import sys

from . import __version__
from . import fetch as F
from . import universe as U
from .util import sha256_bytes, sha256_file, code_hash, canon_json, write_once

SPEC_SHA256 = "09b6ca179575ead1604b6e87f014d55ef3b91a36b9bb5386f80bf5d021ec6c56"


def cmd_universe(a):
    out = os.path.abspath(a.out)
    if os.path.exists(os.path.join(out, "universe.json")):
        print("ABGELEHNT: universe.json existiert bereits (einmalig)")
        return 4
    os.makedirs(out, exist_ok=True)
    raw = U.fetch_html()
    with open(os.path.join(out, "wiki_sp500.html"), "wb") as f:
        f.write(raw)
    raw_syms = U.parse_constituents(raw.decode("utf-8", "replace"))
    uni, rep = U.build_universe(raw_syms)
    uni_all = uni + ["SPY"]
    doc = {"tool": "lf2.universe", "lf2_version": __version__, "code_hash": code_hash(), "spec_sha256": SPEC_SHA256,
           "source_html_sha256": sha256_bytes(raw), "report": rep, "symbols": uni_all}
    path = os.path.join(out, "universe.json")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(canon_json(doc) + "\n")
    print(json.dumps({"n_symbols_with_SPY": len(uni_all), "raw": rep["raw"], "bad_format": len(rep["bad_format"]),
                      "duplicates": rep["duplicates"], "cut_off": len(rep["cut_off"]),
                      "source_html_sha256": doc["source_html_sha256"], "universe_json_sha256": sha256_file(path)},
                     indent=1))
    return 0


def cmd_fetch(a):
    with open(a.universe, encoding="utf-8") as f:
        uni = json.load(f)
    if uni.get("spec_sha256") != SPEC_SHA256:
        print("ABGELEHNT: Universum gehoert zu einer anderen Spec")
        return 4
    token = os.environ.get("TIINGO_TOKEN", "")
    try:
        man = F.fetch_all(uni["symbols"], a.out, token, min_gap_s=a.gap)
    except F.FetchAbort as e:
        print("ABBRUCH: %s" % e)
        return 5
    doc = F.finalize_manifest(man, sha256_file(a.universe), SPEC_SHA256)
    mpath = os.path.join(a.out, "manifest.json")
    with open(mpath, "w", encoding="utf-8", newline="\n") as f:
        f.write(canon_json(doc) + "\n")
    print(json.dumps({"summary": F.manifest_summary(man), "manifest_hash": doc["manifest_hash"],
                      "manifest_sha256": sha256_file(mpath)}, indent=1))
    return 0


def _write_json_once(path, doc):
    if not write_once(path, json.dumps(doc, sort_keys=True, indent=1) + "\n"):
        print("ABGELEHNT: %s existiert bereits (einmalig)" % path)
        return False
    return True


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _check_manifest_file(a):
    uni_path, man_path = os.path.join(a.data, "universe.json"), os.path.join(a.data, "manifest.json")
    if not (os.path.exists(uni_path) and os.path.exists(man_path)):
        print("ABGELEHNT: universe.json oder manifest.json fehlt (Download nicht abgeschlossen?)")
        return None
    uni, man = _load(uni_path), _load(man_path)
    if man.get("universe_hash") != sha256_file(uni_path) or man.get("spec_hash") != SPEC_SHA256:
        print("ABGELEHNT: Manifest gehoert nicht zu diesem Universum/dieser Spec")
        return None
    return uni, man, uni_path, man_path


def cmd_qcount(a):
    from . import protocol as P
    r = _check_manifest_file(a)
    if r is None:
        return 4
    uni, man, _, _ = r
    bad = P.data_manifest_check(os.path.join(a.data, "prices"), man, uni["symbols"])
    if bad:
        print("ABGELEHNT: C6: Daten weichen vom Manifest ab: %s" % bad[:5])
        return 4
    rep = P.qcount(os.path.join(a.data, "prices"), uni, man)
    rep["code_hash"] = code_hash()
    print(json.dumps(rep, indent=1, sort_keys=True))
    out = os.path.join(a.data, "qcount_S.json")
    if not write_once(out, json.dumps(rep, sort_keys=True, indent=1) + "\n"):
        print("(qcount_S.json existiert bereits und bleibt unveraendert)")
    return 0


def cmd_gate(a):
    from . import protocol as P
    r = _check_manifest_file(a)
    if r is None:
        return 4
    uni, man, uni_path, _ = r
    if not os.path.exists(os.path.join(a.data, "qcount_S.json")):
        print("ABGELEHNT: erst `qcount` ausfuehren (Spec R8 Schritt 4 vor Schritt 5)")
        return 4
    bad = P.data_manifest_check(os.path.join(a.data, "prices"), man, uni["symbols"])
    if bad:
        print("ABGELEHNT: C6: Daten weichen vom Manifest ab: %s" % bad[:5])
        return 4
    doc = P.gate_s(os.path.join(a.data, "prices"), uni, man, sha256_file(uni_path))
    out = os.path.join(a.data, "gate_result_S.json")
    if not _write_json_once(out, doc):
        return 4
    print(json.dumps({"admissible": doc["admissible"], "cells": doc["cells"], "result_hash": doc["result_hash"], "file_sha256": sha256_file(out)}, indent=1, sort_keys=True))
    return 0


def _check_specs(spec_dir):
    from . import protocol as P
    want = {"RUNDE2_SPEC_v1.md": P.SPEC_SHA256, "GATE_SPEC_v1.md": P.GATE_SPEC_SHA256, "BAU_SPEC_S1S3_v2.md": P.BAU_SPEC_V2_SHA256}
    for name, h in want.items():
        path = os.path.join(spec_dir, name)
        if not os.path.exists(path) or P._norm_spec_hash(path) != h:
            print("ABGELEHNT: Spec fehlt oder Hash abweichend: %s" % name)
            return False
    return True


def cmd_freeze(a):
    from . import protocol as P
    r = _check_manifest_file(a)
    if r is None or not _check_specs(a.specs):
        return 4
    uni, man, uni_path, man_path = r
    if not os.path.exists(os.path.join(a.data, "gate_result_S.json")):
        print("ABGELEHNT: erst `gate` ausfuehren (Spec R8 Schritt 5 vor Schritt 6)")
        return 4
    gate = _load(os.path.join(a.data, "gate_result_S.json"))
    try:
        payload, fh = P.make_freeze(uni_path, man_path, gate, os.path.join(a.data, "prices"))
    except P.FreezeError as e:
        print("ABGELEHNT: %s" % e)
        return 4
    doc = {"payload": payload, "freeze_hash": fh}
    out = os.path.join(a.data, "freeze.json")
    if not _write_json_once(out, doc):
        return 4
    print(json.dumps({"FREEZE_HASH": fh, "code_hash": payload["code_hash"], "manifest_hash": payload["manifest_hash"], "gate_classes": payload["gate_classes"],
                      "freeze_file_sha256": sha256_file(out)}, indent=1, sort_keys=True))
    return 0


def cmd_backtest(a):
    from . import protocol as P
    r = _check_manifest_file(a)
    if r is None:
        return 4
    _, _, uni_path, man_path = r
    fz = _load(os.path.join(a.data, "freeze.json"))
    prev = None
    if a.stage == "confirm":
        pp = os.path.join(a.data, "out", "result_discovery_A.json")
        if not os.path.exists(pp):
            print("ABGELEHNT: Stufe D fehlt")
            return 4
        prev = _load(pp)
    try:
        doc = P.run_stage(a.stage, fz, uni_path, man_path, os.path.join(a.data, "prices"), os.path.join(a.data, "out"), prev, retry=a.retry)
    except P.StageError as e:
        print("ABGELEHNT: %s" % e)
        return 4
    show = {"stage": doc["stage"], "result_hash": doc["result_hash"], "freeze_hash": doc["freeze_hash"], "results": doc["results"]}
    if "decision" in doc:
        show["decision"] = doc["decision"]
    print(json.dumps(show, indent=1, sort_keys=True))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="lf2")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("universe"); s.add_argument("--out", required=True); s.set_defaults(f=cmd_universe)
    s = sub.add_parser("fetch"); s.add_argument("--universe", required=True); s.add_argument("--out", required=True)
    s.add_argument("--gap", type=float, default=F.MIN_GAP_S); s.set_defaults(f=cmd_fetch)
    for name, fn in (("qcount", cmd_qcount), ("gate", cmd_gate)):
        s = sub.add_parser(name); s.add_argument("--data", required=True); s.set_defaults(f=fn)
    s = sub.add_parser("freeze"); s.add_argument("--data", required=True); s.add_argument("--specs", required=True); s.set_defaults(f=cmd_freeze)
    s = sub.add_parser("backtest"); s.add_argument("--data", required=True); s.add_argument("--stage", required=True, choices=["discovery_A", "confirm"])
    s.add_argument("--retry", action="store_true", help="nur nach technischem Fehler (Sperre status failed/running); wird in der Sperre protokolliert")
    s.set_defaults(f=cmd_backtest)
    s = sub.add_parser("selfcheck"); s.set_defaults(f=lambda a: print(json.dumps({"lf2_version": __version__, "code_hash": code_hash()}, indent=1)) or 0)
    a = p.parse_args(argv)
    return a.f(a)


if __name__ == "__main__":
    sys.exit(main())
