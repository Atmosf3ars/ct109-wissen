"""Marktdaten-Zugang des Runners: genau zwei oeffentliche GET-Endpunkte (Allowlist), nur Lesen, keine Schluessel.

Spot-Kerzen (60 min) dienen als Preisproxy. Der Futures-Ticker (Mark/Index/Funding) wird nur geloggt.
Antwortformate laut Herstellerdokumentation (Abruf 23.10.2026); nicht gegen eine Live-Antwort geprueft.
"""
import json
import urllib.parse
import urllib.request

OHLC_URL = "https://api.kraken.com/0/public/OHLC"
TICKERS_URL = "https://futures.kraken.com/derivatives/api/v3/tickers"
ALLOWED_URLS = (OHLC_URL, TICKERS_URL)

SPOT_PAIRS = {"BTC": "XBTUSD", "ETH": "ETHUSD", "SOL": "SOLUSD"}
PERP_SYMBOLS = {"BTC": "PF_XBTUSD", "ETH": "PF_ETHUSD", "SOL": "PF_SOLUSD"}   # Annahme, unbelegt


class FeedError(Exception):
    pass


def parse_ohlc(obj):
    """Gibt Liste (ts, o, h, l, c, v) aufsteigend zurueck; die letzte Kerze ist die laufende."""
    if not isinstance(obj, dict) or obj.get("error"):
        raise FeedError("Fehlerantwort: %r" % (obj.get("error") if isinstance(obj, dict) else obj))
    res = obj.get("result")
    if not isinstance(res, dict):
        raise FeedError("kein result")
    keys = [k for k in res if k != "last"]
    if len(keys) != 1:
        raise FeedError("erwartet genau ein Paar, gefunden %d" % len(keys))
    out = []
    for row in res[keys[0]]:
        try:
            out.append((int(row[0]), float(row[1]), float(row[2]), float(row[3]), float(row[4]), float(row[6])))
        except (IndexError, TypeError, ValueError):
            raise FeedError("Kerze nicht lesbar: %r" % (row,))
    out.sort(key=lambda x: x[0])
    return out


def parse_tickers(obj, symbols):
    if not isinstance(obj, dict) or obj.get("result") != "success":
        raise FeedError("Ticker-Antwort ohne success")
    want = set(symbols)
    out = {}
    for t in obj.get("tickers", []):
        if t.get("symbol") in want:
            out[t["symbol"]] = {k: t.get(k) for k in ("markPrice", "indexPrice", "last", "fundingRate")}
    return out


MAX_BYTES = 5_000_000


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Umleitungen werden nie befolgt: die Allowlist gilt auch fuer das Ziel (QA2 m1)."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise FeedError("Umleitung abgelehnt (%s)" % code)


def _get(base, params, timeout=20):
    if base not in ALLOWED_URLS:
        raise FeedError("URL nicht in der Allowlist")
    url = base + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "ct109-paper-runner/1"})
    opener = urllib.request.build_opener(_NoRedirect)
    with opener.open(req, timeout=timeout) as r:
        raw = r.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise FeedError("Antwort groesser als %d Bytes" % MAX_BYTES)
    return json.loads(raw.decode("utf-8"))


def fetch_ohlc(asset, interval=60):
    return parse_ohlc(_get(OHLC_URL, {"pair": SPOT_PAIRS[asset], "interval": interval}))


def fetch_tickers(assets):
    syms = [PERP_SYMBOLS[a] for a in assets]
    return parse_tickers(_get(TICKERS_URL, {}), syms)
