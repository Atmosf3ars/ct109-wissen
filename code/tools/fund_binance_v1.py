# fund_binance_v1.py - Phase 0 FUND_XS: oeffentliche Binance-USDT-M-Funding-Historie (Vergleichsvenue, Mehr-Regime-Proxy) fuer den Kraken-Pool.
# Nur lesend, kein Schluessel. Werte ab 2026-07-01 UTC werden NICHT gespeichert (gesperrt). Ausgabe: nur Abdeckung + zentrierte Streuung, keine Mittelwerte/Vorzeichen.
# Aufruf: python -u fund_binance_v1.py D:\CT109-Data\funding-binance | Out-File -Encoding utf8 fund_binance_out.txt; type fund_binance_out.txt
import sys, os, json, time, math, hashlib, urllib.request, urllib.error
from datetime import datetime, timezone
POOL = ["XBT","ETH","SOL","XRP","XDG","ADA","LTC","DOT","LINK","XMR","ZEC","XLM","BCH","ATOM","SUI","PEPE","AVAX","TAO","FIL","UNI","TRX","AAVE","FET","NEAR","DASH","CRV","ICP","FARTCOIN","INJ","PENGU","ONDO","SEI","TIA","TRUMP"]
BN = {"XBT": "BTC", "XDG": "DOGE"}
CUT_MS = int(datetime(2026, 7, 1, tzinfo=timezone.utc).timestamp() * 1000)
def get(url):
    for k in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ct109-fundbn/1"})
            with urllib.request.urlopen(req, timeout=60) as r: return json.loads(r.read().decode("utf-8")), None
        except urllib.error.HTTPError as e:
            if e.code in (400, 404): return None, "http%d" % e.code
            err = "http%d" % e.code
        except Exception as e: err = type(e).__name__
        time.sleep(3 * (k + 1))
    return None, err
def fetch(sym):
    rows = []; start = int(datetime(2019, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
    while start < CUT_MS:
        js, err = get("https://fapi.binance.com/fapi/v1/fundingRate?symbol=%s&startTime=%d&limit=1000" % (sym, start))
        if js is None: return (rows or None), err
        if not js: break
        for r in js:
            if r["fundingTime"] < CUT_MS: rows.append((int(r["fundingTime"]), float(r["fundingRate"])))
        start = js[-1]["fundingTime"] + 1
        if len(js) < 1000: break
        time.sleep(0.4)
    return rows, None
def main(outd):
    os.makedirs(outd, exist_ok=True)
    print("Skript-SHA256 %s" % hashlib.sha256(open(__file__, "rb").read()).hexdigest()[:16], flush=True)
    print("Kraken-Symbol | Binance-Symbol | Zeilen | erste | letzte | zentrierte Streuung (bp je 8 h) | Datei", flush=True)
    for x in POOL:
        base = BN.get(x, x); done = False
        for sym in (base + "USDT", "1000" + base + "USDT"):
            rows, err = fetch(sym)
            if rows: done = True; break
            time.sleep(0.5)
        if not done: print("%s | -- | nicht vorhanden (%s)" % (x, err), flush=True); continue
        p = os.path.join(outd, sym + ".csv")
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write("fundingTimeMs,fundingRate\n")
            for t, v in rows: f.write("%d,%.12g\n" % (t, v))
        v = [r[1] for r in rows]; m = sum(v) / len(v)
        sd = math.sqrt(sum((a - m) ** 2 for a in v) / max(1, len(v) - 1)) * 1e4
        d = lambda ms: datetime.fromtimestamp(ms / 1000, timezone.utc).date()
        print("%s | %s | %d | %s | %s | %.2f | %s" % (x, sym, len(rows), d(rows[0][0]), d(rows[-1][0]), sd, p), flush=True)
        time.sleep(1.0)
    print("FERTIG", flush=True)
if __name__ == "__main__": main(sys.argv[1] if len(sys.argv) > 1 else r"D:\CT109-Data\funding-binance")
