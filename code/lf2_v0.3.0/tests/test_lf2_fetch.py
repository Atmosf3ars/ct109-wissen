import io
import json
import os
import sys
import tempfile
import unittest
import urllib.error

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from lf2 import fetch as F, universe as U, cli  # noqa: E402

HEAD = "date,close,high,low,open,volume,adjClose,adjHigh,adjLow,adjOpen,adjVolume,divCash,splitFactor\n"


def csv_body(dates):
    return (HEAD + "".join("%s,10,11,9,10,1000,10,11,9,10,1000,0,1\n" % d for d in dates)).encode()


WIKI = """<html><body><table class="wikitable" id="other"><tr><td>NOPE</td></tr></table>
<table class="wikitable sortable" id="constituents"><tbody>
<tr><th>Symbol</th><th>Security</th></tr>
<tr><td><a href="x">MMM</a></td><td>3M</td></tr>
<tr><td><a href="x">BRK.B</a>
</td><td>Berkshire</td></tr>
<tr><td><a href="x">AAPL</a></td><td><table><tr><td>INNER</td></tr></table></td></tr>
</tbody></table><table id="after"><tr><td>LATER</td></tr></table></body></html>"""


class Universe(unittest.TestCase):
    def test_parse_only_constituents_first_column(self):
        self.assertEqual(U.parse_constituents(WIKI), ["MMM", "BRK.B", "AAPL"])

    def test_tiingo_symbol(self):
        self.assertEqual(U.to_tiingo("BRK.B"), "BRK-B")

    def test_build_sorted_unique_cut(self):
        raw = ["MSFT", "AAPL", "AAPL", "bad sym", "BRK.B"] + ["Z%d" % i for i in range(600)]
        uni, rep = U.build_universe(raw, max_stocks=4)
        self.assertEqual(uni, sorted(uni))
        self.assertEqual(len(uni), 4)
        self.assertEqual(rep["duplicates"], 1)
        self.assertEqual(rep["bad_format"], ["bad sym"])
        self.assertTrue(rep["cut_off"])
        self.assertEqual(rep["used"], 4)

    def test_default_cap_is_495(self):
        self.assertEqual(U.MAX_STOCKS, 495)
        raw = ["A%s" % chr(65 + i % 26) + chr(65 + (i // 26) % 26) for i in range(700)]
        uni, rep = U.build_universe(raw)
        self.assertLessEqual(len(uni), 495)

    def test_cut_is_alphabetical_not_by_anything_else(self):
        uni, rep = U.build_universe(["ZZZ", "AAA", "MMM"], max_stocks=2)
        self.assertEqual(uni, ["AAA", "MMM"])


class Validate(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(F.validate_csv(csv_body(["2005-01-03", "2005-01-04"])), (2, "2005-01-03", "2005-01-04"))

    def test_bad_cases(self):
        for body in (b"", b"date,open\n2005-01-03,1\n", HEAD.encode(), csv_body(["2005-01-04", "2005-01-03"]),
                     csv_body(["2005-01-03", "2005-01-03"]), (HEAD + "xx,1,1,1,1,1,1,1,1,1,1,0,1\n").encode()):
            with self.assertRaises(ValueError):
                F.validate_csv(body)


class Fetch(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.t = [0.0]
        self.sleeps = []

    def now(self):
        return self.t[0]

    def sleep(self, s):
        self.sleeps.append(s)
        self.t[0] += s

    def run_fetch(self, syms, request, gap=75.0, **kw):
        return F.fetch_all(syms, self.d, "SECRETTOKEN", request=request, sleep=self.sleep, now=self.now,
                           min_gap_s=gap, log=lambda m: None, **kw)

    def test_ok_not_found_error_and_files(self):
        def req(sym, tok):
            if sym == "NF":
                raise urllib.error.HTTPError("u", 404, "nf", {}, None)
            if sym == "BAD":
                return b"garbage"
            return csv_body(["2005-01-03"])
        m = self.run_fetch(["AAA", "NF", "BAD"], req)
        self.assertEqual({k: v["status"] for k, v in m["symbols"].items()}, {"AAA": "ok", "NF": "not_found", "BAD": "error"})
        self.assertTrue(os.path.exists(os.path.join(self.d, "AAA.csv")))
        self.assertFalse(os.path.exists(os.path.join(self.d, "NF.csv")))
        self.assertFalse(os.path.exists(os.path.join(self.d, "BAD.csv")))
        self.assertFalse([f for f in os.listdir(self.d) if f.endswith(".tmp")])

    def test_throttle_gap_between_requests(self):
        calls = []
        def req(sym, tok):
            calls.append(self.now())
            return csv_body(["2005-01-03"])
        self.run_fetch(["A", "B", "C"], req)
        self.assertEqual([round(b - a) for a, b in zip(calls, calls[1:])], [75, 75])

    def test_resume_skips_valid_and_refetches_broken(self):
        open(os.path.join(self.d, "A.csv"), "wb").write(csv_body(["2005-01-03"]))
        open(os.path.join(self.d, "B.csv"), "wb").write(b"kaputt")
        asked = []
        def req(sym, tok):
            asked.append(sym)
            return csv_body(["2005-01-03", "2005-01-04"])
        m = self.run_fetch(["A", "B"], req)
        self.assertEqual(asked, ["B"])
        self.assertTrue(m["symbols"]["A"]["resumed"])
        self.assertFalse(m["symbols"]["B"]["resumed"])

    def test_429_waits_and_retries(self):
        n = [0]
        def req(sym, tok):
            n[0] += 1
            if n[0] == 1:
                raise urllib.error.HTTPError("u", 429, "x", {}, None)
            return csv_body(["2005-01-03"])
        m = self.run_fetch(["A"], req)
        self.assertEqual(m["symbols"]["A"]["status"], "ok")
        self.assertIn(600, self.sleeps)

    def test_endless_429_aborts(self):
        def req(sym, tok):
            raise urllib.error.HTTPError("u", 429, "x", {}, None)
        with self.assertRaises(F.FetchAbort):
            self.run_fetch(["A"], req)

    def test_auth_error_aborts_without_token_in_message(self):
        def req(sym, tok):
            raise urllib.error.HTTPError("u", 401, "x", {}, None)
        with self.assertRaises(F.FetchAbort) as c:
            self.run_fetch(["A"], req)
        self.assertNotIn("SECRETTOKEN", str(c.exception))

    def test_no_token_aborts(self):
        with self.assertRaises(F.FetchAbort):
            F.fetch_all(["A"], self.d, "", request=lambda s, t: b"")

    def test_retries_then_error(self):
        def req(sym, tok):
            raise urllib.error.URLError("net")
        m = self.run_fetch(["A"], req, max_retries=3)
        self.assertEqual(m["symbols"]["A"], {"status": "error", "what": "URLError"})

    def test_manifest_hash_changes_with_content_and_has_hashes(self):
        m = self.run_fetch(["A"], lambda s, t: csv_body(["2005-01-03"]))
        d1 = F.finalize_manifest(m, "u" * 64, "s" * 64)
        m2 = self.run_fetch(["A"], lambda s, t: csv_body(["2005-01-03"]))
        d2 = F.finalize_manifest(m2, "v" * 64, "s" * 64)
        self.assertNotEqual(d1["manifest_hash"], d2["manifest_hash"])
        self.assertEqual(len(m["symbols"]["A"]["sha256"]), 64)

    def test_token_never_in_url_or_headers_dump(self):
        import inspect
        src = inspect.getsource(F)
        self.assertNotIn("token=", src.lower().replace("token = ", ""))


class Cli(unittest.TestCase):
    def test_fetch_requires_matching_spec(self):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "u.json")
        json.dump({"spec_sha256": "0" * 64, "symbols": ["A"]}, open(p, "w"))
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            rc = cli.main(["fetch", "--universe", p, "--out", os.path.join(d, "o")])
        finally:
            sys.stdout = old
        self.assertEqual(rc, 4)

    def test_fetch_without_token_aborts(self):
        d = tempfile.mkdtemp()
        p = os.path.join(d, "u.json")
        json.dump({"spec_sha256": cli.SPEC_SHA256, "symbols": ["A"]}, open(p, "w"))
        os.environ.pop("TIINGO_TOKEN", None)
        old = sys.stdout
        sys.stdout = io.StringIO()
        try:
            rc = cli.main(["fetch", "--universe", p, "--out", os.path.join(d, "o")])
        finally:
            sys.stdout = old
        self.assertEqual(rc, 5)

    def test_universe_writes_once(self):
        d = tempfile.mkdtemp()
        old_fetch = U.fetch_html
        U.fetch_html = lambda *a, **k: WIKI.encode()
        old = sys.stdout
        sys.stdout = io.StringIO()
        try:
            rc1 = cli.main(["universe", "--out", d])
            rc2 = cli.main(["universe", "--out", d])
        finally:
            sys.stdout = old
            U.fetch_html = old_fetch
        self.assertEqual((rc1, rc2), (0, 4))
        doc = json.load(open(os.path.join(d, "universe.json")))
        self.assertEqual(doc["symbols"], ["AAPL", "BRK-B", "MMM", "SPY"])
        self.assertEqual(doc["spec_sha256"], cli.SPEC_SHA256)


if __name__ == "__main__":
    unittest.main()
