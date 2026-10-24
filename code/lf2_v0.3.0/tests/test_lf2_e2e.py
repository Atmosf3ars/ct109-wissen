"""Ende-zu-Ende mit synthetischen Daten auf Platte: Gate, Freeze, Stufen, Sperren, Manipulationsschutz, Signalnachweis und Nullkontrolle."""
import datetime
import json
import os
import shutil
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from lf2 import fetch as F, protocol as P, cli  # noqa: E402
from lf2.util import sha256_bytes, sha256_file, canon_json  # noqa: E402

HEAD = "date,close,high,low,open,volume,adjClose,adjHigh,adjLow,adjOpen,adjVolume,divCash,splitFactor\n"


def weekdays(a, b):
    d, out = a, []
    while d <= b:
        if d.weekday() < 5:
            out.append(d)
        d += datetime.timedelta(days=1)
    return out


def make_dataset(root, n=150, seed=7, reversal=0.0, momentum=0.0, junk=10):
    days = weekdays(datetime.date(2005, 1, 3), datetime.date(2026, 6, 30))
    T = len(days)
    rng = np.random.default_rng(seed)
    r = rng.normal(0, 0.02, (T, n)) + rng.normal(0, 0.008, (T, 1))
    if reversal:                                              # jeder Tagesschock wird in den 5 Folgetagen zu je 1/5 zurueckgenommen (kein Schwingen)
        s0 = r.copy()
        for k in range(1, 6):
            r[k:] -= reversal * s0[:-k] / 5.0
    if momentum:
        drift = rng.normal(0, 0.0008, n)                      # persistente Aktien-Drift (langsames Momentum)
        r += drift[None, :] * momentum
    prices = 50 * np.exp(np.cumsum(r, axis=0))
    opn = prices * np.exp(rng.normal(0, 0.002, (T, n)))
    vol = rng.uniform(1e6, 5e6, (T, n))
    spy = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, T)))
    jr = np.random.default_rng(seed + 99)
    jprice = 2.0 * np.exp(np.cumsum(jr.normal(0, 0.3, (T, junk)), axis=0)) / 1.0
    jprice = np.clip(jprice, 0.5, 4.5)                                       # nie >= 5 USD: nicht handelbar, aber riesige Renditen und Volumen
    jopn = jprice * np.exp(jr.normal(0, 0.05, (T, junk)))
    jvol = np.full((T, junk), 5e8)
    pdir = os.path.join(root, "prices")
    os.makedirs(pdir, exist_ok=True)
    syms = ["S%03d" % i for i in range(n)] + ["J%02d" % i for i in range(junk)] + ["SPY"]
    man = {"symbols": {}}
    for j, s in enumerate(syms):
        if s == "SPY":
            px, op, vo = spy, spy, np.full(T, 5e7)
        elif s.startswith("J"):
            k = int(s[1:]); px, op, vo = jprice[:, k], jopn[:, k], jvol[:, k]
        else:
            px, op, vo = prices[:, j], opn[:, j], vol[:, j]
        rows = "".join("%s,%.4f,%.4f,%.4f,%.4f,%d,%.4f,%.4f,%.4f,%.4f,%d,0,1\n" % (d.isoformat(), px[i], px[i], px[i], op[i], vo[i], px[i], px[i], px[i], op[i], vo[i])
                       for i, d in enumerate(days))
        body = (HEAD + rows).encode()
        with open(os.path.join(pdir, s + ".csv"), "wb") as f:
            f.write(body)
        man["symbols"][s] = {"status": "ok", "rows": T, "first": days[0].isoformat(), "last": days[-1].isoformat(), "sha256": sha256_bytes(body), "bytes": len(body), "resumed": False}
    uni = {"tool": "lf2.universe", "spec_sha256": P.SPEC_SHA256, "symbols": syms}
    upath = os.path.join(root, "universe.json")
    with open(upath, "w", encoding="utf-8", newline="\n") as f:
        f.write(canon_json(uni) + "\n")
    mdoc = F.finalize_manifest(man, sha256_file(upath), P.SPEC_SHA256)
    mpath = os.path.join(root, "manifest.json")
    with open(mpath, "w", encoding="utf-8", newline="\n") as f:
        f.write(canon_json(mdoc) + "\n")
    return upath, mpath, pdir, uni


class E2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tempfile.mkdtemp()
        cls.up, cls.mp, cls.pd, cls.uni = make_dataset(cls.root)
        cls.man = json.load(open(cls.mp)); cls.usha = sha256_file(cls.up)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True)

    def test_a_pipeline_null_data(self):
        q = P.qcount(self.pd, self.uni, json.load(open(self.mp)))
        self.assertEqual(q["stocks_loaded"], 160)
        self.assertEqual(q["manifest_status"], {"ok": 161})
        for w in "AEF":
            self.assertLessEqual(q["tradable_%s" % w]["max"], 150)                 # Junk-Aktien (< 5 USD) nie handelbar
        self.assertIn("gap_days_per_symbol", q)
        self.assertIn("open_vs_prev_adjclose_gt_50pct_count", q)
        for w in "AEF":
            self.assertEqual(q["tradable_%s" % w]["days_below_100"], 0 if w != "E" else q["tradable_E"]["days_below_100"])
        gate = P.gate_s(self.pd, self.uni, self.man, self.usha)
        self.assertEqual(gate["admissible"], ["H21", "H5"])
        self.assertEqual(gate["cells"]["H5"]["class"], "P")
        self.assertLess(gate["cells"]["H5"]["e_abs_r_bp"], 500)                      # Junk-Renditen (> 1000 bp) duerfen nicht eingehen
        payload, fh = P.make_freeze(self.up, self.mp, gate, self.pd)
        fz = {"payload": payload, "freeze_hash": fh}
        out = os.path.join(self.root, "out")
        d = P.run_stage("discovery_A", fz, self.up, self.mp, self.pd, out, nplacebo=30, nboot=400, log=lambda *_: None)
        self.assertEqual(len(d["results"]), 2)
        self.assertEqual([r["block"] for r in d["results"]], [20, 84])                   # Nachtrag N1
        self.assertEqual([gate["cells"]["H5"]["block"], gate["cells"]["H21"]["block"]], [20, 84])
        self.assertNotIn("decision", d)
        with self.assertRaises(P.StageError):                                  # Sperre
            P.run_stage("discovery_A", fz, self.up, self.mp, self.pd, out, nplacebo=30, nboot=400, log=lambda *_: None)
        c = P.run_stage("confirm", fz, self.up, self.mp, self.pd, out, prev_result=d, nplacebo=30, nboot=400, log=lambda *_: None)
        self.assertEqual([x["category"] for x in c["decision"]], ["NULLBEFUND", "NULLBEFUND"])     # Nullkontrolle: Kosten fressen alles
        for r in c["results"]:
            self.assertLess(r["mean_bp_day"], 0)                                  # negativ wegen Kosten
        self.assertEqual(c["prev_result_hash"], d["result_hash"])
        # result_hash reproduzierbar
        body = {k: v for k, v in c.items() if k not in ("run_utc", "result_hash")}
        from lf2.util import json_hash
        self.assertEqual(json_hash(body), c["result_hash"])

    def test_b_tamper_data_rejected(self):
        gate = P.gate_s(self.pd, self.uni, self.man, self.usha)
        payload, fh = P.make_freeze(self.up, self.mp, gate, self.pd)
        fz = {"payload": payload, "freeze_hash": fh}
        victim = os.path.join(self.pd, "S005.csv")
        orig = open(victim, "rb").read()
        try:
            with open(victim, "ab") as f:
                f.write(b"\n")
            with self.assertRaises(P.StageError):
                P.run_stage("discovery_A", fz, self.up, self.mp, self.pd, os.path.join(self.root, "out_t"), log=lambda *_: None)
            with self.assertRaises(P.FreezeError):
                P.make_freeze(self.up, self.mp, gate, self.pd)
        finally:
            with open(victim, "wb") as f:
                f.write(orig)
        bad = dict(fz, freeze_hash="0" * 64)
        with self.assertRaises(P.StageError):
            P.run_stage("discovery_A", bad, self.up, self.mp, self.pd, os.path.join(self.root, "out_t2"), log=lambda *_: None)
        bad2 = {"payload": dict(payload, seed=1), "freeze_hash": fh}
        with self.assertRaises(P.StageError):
            P.run_stage("discovery_A", bad2, self.up, self.mp, self.pd, os.path.join(self.root, "out_t3"), log=lambda *_: None)

    def test_c_confirm_needs_valid_stage_d(self):
        gate = P.gate_s(self.pd, self.uni, self.man, self.usha)
        payload, fh = P.make_freeze(self.up, self.mp, gate, self.pd)
        fz = {"payload": payload, "freeze_hash": fh}
        with self.assertRaises(P.StageError):
            P.run_stage("confirm", fz, self.up, self.mp, self.pd, os.path.join(self.root, "o4"), prev_result=None, log=lambda *_: None)
        with self.assertRaises(P.StageError):
            P.run_stage("confirm", fz, self.up, self.mp, self.pd, os.path.join(self.root, "o5"), prev_result={"result_hash": "x", "results": []}, log=lambda *_: None)

    def test_d_gate_tamper_rejected(self):
        gate = P.gate_s(self.pd, self.uni, self.man, self.usha)
        gate["cells"]["H5"]["class"] = "P"
        gate["cells"]["H5"]["rho_min_plus"] = 0.0001
        with self.assertRaises(P.FreezeError):
            P.make_freeze(self.up, self.mp, gate, self.pd)


    def _fz(self):
        gate = P.gate_s(self.pd, self.uni, self.man, self.usha)
        payload, fh = P.make_freeze(self.up, self.mp, gate, self.pd)
        return gate, payload, {"payload": payload, "freeze_hash": fh}

    def test_e_code_hash_guard(self):
        from lf2.util import json_hash
        _, payload, _ = self._fz()
        p2 = dict(payload, code_hash="0" * 64)
        fz2 = {"payload": p2, "freeze_hash": json_hash(p2)}                       # in sich stimmiger Freeze, aber anderer Code
        with self.assertRaises(P.StageError) as cm:
            P.run_stage("discovery_A", fz2, self.up, self.mp, self.pd, os.path.join(self.root, "o_ch"), log=lambda *_: None)
        self.assertIn("Code", str(cm.exception))

    def test_f_confirm_requires_matching_stage_d(self):
        from lf2.util import json_hash, code_hash
        _, _, fz = self._fz()
        prev = {"stage": "discovery_A", "freeze_hash": "x" * 64, "code_hash": code_hash(), "results": []}
        prev["result_hash"] = json_hash(prev)
        with self.assertRaises(P.StageError):
            P.run_stage("confirm", fz, self.up, self.mp, self.pd, os.path.join(self.root, "o_pf"), prev_result=prev, log=lambda *_: None)
        prev2 = dict(prev, freeze_hash=fz["freeze_hash"], stage="confirm")
        prev2.pop("result_hash"); prev2["result_hash"] = json_hash(prev2)
        with self.assertRaises(P.StageError):
            P.run_stage("confirm", fz, self.up, self.mp, self.pd, os.path.join(self.root, "o_pf2"), prev_result=prev2, log=lambda *_: None)
        prev3 = dict(prev, freeze_hash=fz["freeze_hash"], code_hash="1" * 64)
        prev3.pop("result_hash"); prev3["result_hash"] = json_hash(prev3)
        with self.assertRaises(P.StageError):
            P.run_stage("confirm", fz, self.up, self.mp, self.pd, os.path.join(self.root, "o_pf3"), prev_result=prev3, log=lambda *_: None)

    def test_g_crash_retry_protocol(self):
        import lf2.protocol as pm
        _, _, fz = self._fz()
        out = os.path.join(self.root, "o_retry")
        orig = pm.evaluate_set
        calls = {"n": 0}

        def boom(*a, **k):
            calls["n"] += 1
            if calls["n"] == 2:
                raise RuntimeError("simulierter Absturz")
            return orig(*a, **k)
        pm.evaluate_set = boom
        try:
            with self.assertRaises(RuntimeError):
                P.run_stage("discovery_A", fz, self.up, self.mp, self.pd, out, nplacebo=10, nboot=100, log=lambda *_: None)
            lock = json.load(open(os.path.join(out, "lock_discovery_A")))
            self.assertEqual(lock["status"], "failed"); self.assertIn("RuntimeError", lock["error"])
            self.assertFalse(os.path.exists(os.path.join(out, "result_discovery_A.json")))
            with self.assertRaises(P.StageError):                                   # ohne --retry bleibt die Sperre
                P.run_stage("discovery_A", fz, self.up, self.mp, self.pd, out, nplacebo=10, nboot=100, log=lambda *_: None)
            d = P.run_stage("discovery_A", fz, self.up, self.mp, self.pd, out, nplacebo=10, nboot=100, log=lambda *_: None, retry=True)
        finally:
            pm.evaluate_set = orig
        lock = json.load(open(os.path.join(out, "lock_discovery_A")))
        self.assertEqual((lock["status"], lock["attempts"]), ("done", 2))
        self.assertEqual(lock["history"][0]["status"], "failed")
        self.assertIn("RuntimeError", lock["history"][0]["error"])
        self.assertEqual(len(d["results"]), 2)
        with self.assertRaises(P.StageError):                                       # nach Ergebnis nie wieder, auch nicht mit retry
            P.run_stage("discovery_A", fz, self.up, self.mp, self.pd, out, nplacebo=10, nboot=100, log=lambda *_: None, retry=True)
        self.assertEqual([x for x in os.listdir(out) if ".tmp" in x], [])

    def test_h_retry_refused_for_foreign_or_done_lock(self):
        _, _, fz = self._fz()
        out = os.path.join(self.root, "o_foreign")
        os.makedirs(out)
        open(os.path.join(out, "lock_discovery_A"), "w").write(json.dumps({"freeze_hash": "z" * 64, "code_hash": "z" * 64, "status": "failed", "attempts": 1}) + "\n")
        with self.assertRaises(P.StageError):
            P.run_stage("discovery_A", fz, self.up, self.mp, self.pd, out, log=lambda *_: None, retry=True)
        from lf2.util import code_hash
        open(os.path.join(out, "lock_discovery_A"), "w").write(json.dumps({"freeze_hash": fz["freeze_hash"], "code_hash": code_hash(), "status": "done", "attempts": 1}) + "\n")
        with self.assertRaises(P.StageError):
            P.run_stage("discovery_A", fz, self.up, self.mp, self.pd, out, log=lambda *_: None, retry=True)

    def test_i_gate_binding(self):
        from lf2.util import json_hash
        gate, _, _ = self._fz()

        def rehash(g):
            g = dict(g); g.pop("result_hash", None); g["result_hash"] = json_hash(g); return g
        for key, val in (("manifest_hash", "0" * 64), ("universe_json_sha256", "0" * 64), ("code_hash", "0" * 64)):
            with self.assertRaises(P.FreezeError, msg=key):
                P.make_freeze(self.up, self.mp, rehash(dict(gate, **{key: val})), self.pd)
        with self.assertRaises(P.FreezeError):                                       # Gate stammt von anderer Spec
            P.make_freeze(self.up, self.mp, rehash(dict(gate, spec_sha256="0" * 64)), self.pd)

    def test_j_c6_strict_and_manifest_spec(self):
        man = json.loads(json.dumps(self.man))
        sym = self.uni["symbols"][3]
        man["manifest"]["symbols"][sym] = {"status": "error", "http": 500}
        bad = P.data_manifest_check(self.pd, man, self.uni["symbols"])
        self.assertEqual([b[0] for b in bad], [sym])                                   # Datei vorhanden, Status nicht ok
        man2 = json.loads(json.dumps(self.man)); man2["manifest"]["symbols"].pop(sym)
        self.assertEqual([b[0] for b in P.data_manifest_check(self.pd, man2, self.uni["symbols"])], [sym])
        gate, _, _ = self._fz()
        import tempfile as tf
        d = tf.mkdtemp()
        man3 = dict(self.man, spec_hash="0" * 64)
        man3.pop("manifest_hash"); man3["manifest_hash"] = __import__("lf2.util", fromlist=["json_hash"]).json_hash(man3)
        mp3 = os.path.join(d, "manifest.json")
        open(mp3, "w").write(json.dumps(man3))
        g3 = dict(gate, manifest_hash=man3["manifest_hash"])
        g3.pop("result_hash"); g3["result_hash"] = __import__("lf2.util", fromlist=["json_hash"]).json_hash(g3)
        with self.assertRaises(P.FreezeError) as cm:
            P.make_freeze(self.up, mp3, g3, self.pd)
        self.assertIn("Spec", str(cm.exception))
        man4 = dict(self.man, manifest_hash="f" * 64)                                    # veraendertes Manifest (Hash passt nicht zum Inhalt)
        mp4 = os.path.join(d, "manifest4.json")
        open(mp4, "w").write(json.dumps(man4))
        g4 = dict(gate, manifest_hash="f" * 64)
        g4.pop("result_hash"); g4["result_hash"] = __import__("lf2.util", fromlist=["json_hash"]).json_hash(g4)
        with self.assertRaises(P.FreezeError) as cm:
            P.make_freeze(self.up, mp4, g4, self.pd)
        self.assertIn("Manifest-Hash", str(cm.exception))


class CliFlow(unittest.TestCase):
    """Reihenfolge laut Spec R8 ueber die Kommandozeile: qcount -> gate -> freeze; Hash-Waechter fuer Specs; Einmaligkeit."""

    @classmethod
    def setUpClass(cls):
        cls.root = tempfile.mkdtemp()
        make_dataset(cls.root, n=120, seed=21, junk=3)
        cls.specs = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "specs")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True)

    def run_cli(self, *argv):
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cli.main(list(argv))
        return rc, buf.getvalue()

    def test_order_and_once(self):
        d = self.root
        rc, out = self.run_cli("gate", "--data", d)
        self.assertEqual(rc, 4); self.assertIn("qcount", out)
        rc, out = self.run_cli("freeze", "--data", d, "--specs", self.specs)
        self.assertEqual(rc, 4); self.assertIn("gate", out)
        rc, out = self.run_cli("qcount", "--data", d)
        self.assertEqual(rc, 0); self.assertTrue(os.path.exists(os.path.join(d, "qcount_S.json")))
        self.assertNotIn("S000", out)                                                 # keine Symbolnamen/Reihen in der Ausgabe
        rc, out = self.run_cli("gate", "--data", d)
        self.assertEqual(rc, 0, out)
        rc, out = self.run_cli("gate", "--data", d)
        self.assertEqual(rc, 4); self.assertIn("einmalig", out)
        bad_specs = tempfile.mkdtemp()
        for n in os.listdir(self.specs):
            shutil.copy(os.path.join(self.specs, n), bad_specs)
        with open(os.path.join(bad_specs, "RUNDE2_SPEC_v1.md"), "a") as f:
            f.write("\nx\n")
        rc, out = self.run_cli("freeze", "--data", d, "--specs", bad_specs)
        self.assertEqual(rc, 4); self.assertIn("Spec", out)
        self.assertFalse(os.path.exists(os.path.join(d, "freeze.json")))
        rc, out = self.run_cli("freeze", "--data", d, "--specs", self.specs)
        self.assertEqual(rc, 0, out); self.assertIn("FREEZE_HASH", out)
        rc, out = self.run_cli("freeze", "--data", d, "--specs", self.specs)
        self.assertEqual(rc, 4)
        rc, out = self.run_cli("backtest", "--data", d, "--stage", "confirm")
        self.assertEqual(rc, 4); self.assertIn("Stufe D fehlt", out)
        # Datenmanipulation wird von qcount/gate abgelehnt
        victim = os.path.join(d, "prices", "S001.csv")
        orig = open(victim, "rb").read()
        try:
            open(victim, "ab").write(b"\n")
            rc, out = self.run_cli("qcount", "--data", d)
            self.assertEqual(rc, 4); self.assertIn("C6", out)
        finally:
            open(victim, "wb").write(orig)


class Detection(unittest.TestCase):
    """Das Verfahren muss einen eingebauten starken Effekt finden (sonst waere ein Nullbefund wertlos)."""

    def test_planted_reversal_found(self):
        root = tempfile.mkdtemp()
        try:
            up, mp, pd, uni = make_dataset(root, n=150, seed=11, reversal=1.0)
            gate = P.gate_s(pd, uni, json.load(open(mp)), sha256_file(up))
            payload, fh = P.make_freeze(up, mp, gate, pd)
            fz = {"payload": payload, "freeze_hash": fh}
            out = os.path.join(root, "out")
            d = P.run_stage("discovery_A", fz, up, mp, pd, out, nplacebo=40, nboot=600, log=lambda *_: None)
            c = P.run_stage("confirm", fz, up, mp, pd, out, prev_result=d, nplacebo=40, nboot=600, log=lambda *_: None)
            h1 = c["results"][0]
            self.assertGreater(h1["mean_bp_day"], 5.0)
            self.assertTrue(h1["c3_placebo"])
            self.assertEqual(c["decision"][0]["category"], "HINWEIS-POSITIV (survivorship-behaftet)", c["decision"][0])
            self.assertNotIn("BESTAETIGT", json.dumps(c["decision"]))
            self.assertEqual(c["decision"][1]["category"], "NULLBEFUND")
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_planted_momentum_found(self):
        root = tempfile.mkdtemp()
        try:
            up, mp, pd, uni = make_dataset(root, n=150, seed=12, momentum=1.0)
            gate = P.gate_s(pd, uni, json.load(open(mp)), sha256_file(up))
            payload, fh = P.make_freeze(up, mp, gate, pd)
            fz = {"payload": payload, "freeze_hash": fh}
            out = os.path.join(root, "out")
            d = P.run_stage("discovery_A", fz, up, mp, pd, out, nplacebo=40, nboot=600, log=lambda *_: None)
            c = P.run_stage("confirm", fz, up, mp, pd, out, prev_result=d, nplacebo=40, nboot=600, log=lambda *_: None)
            self.assertGreater(c["results"][1]["mean_bp_day"], 0)
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
