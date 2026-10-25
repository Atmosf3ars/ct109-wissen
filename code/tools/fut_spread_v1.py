# fut_spread_v1.py - Kostencheck K6: oeffentliche Kraken-Futures-Ticker (nur Lesen, keine Schluessel, keine Orders)
# v1.1 (Alias DOGE->XDG ergaenzt). Aufruf:  python fut_spread_v1.py [Anzahl_Schnappschuesse=15] [Abstand_s=20]  > fut_spread_out.txt
# Gibt je Perp-Symbol aus: Median Spread (bp), Median Top-of-Book-Tiefe (USD, kleinere Seite), Volumen 24h (USD),
# offenes Interesse (USD), Funding (annualisiert, Betrag). Nur Aggregate, keine Rohdaten-Ausgabe.
import sys, json, time, statistics, urllib.request
URL = "https://futures.kraken.com/derivatives/api/v3/tickers"
POOL = ["XBT","ETH","SOL","XRP","XDG","ADA","LTC","DOT","LINK","XMR","ZEC","XLM","BCH","ATOM","SUI","ALGO","PEPE","AVAX",
        "TAO","FIL","UNI","TRX","AAVE","XTZ","FET","NEAR","SHIB","ETC","DASH","MANA","CRV","ICP","FARTCOIN","INJ","PENGU",
        "ONDO","SEI","TIA","KAS","FLOW","TRUMP"]
# K6-Ereigniszahlen (Zaehlung E4, Raster 20/0.7) fuer die Gewichtung
EV = {"XBT":3,"ETH":6,"SOL":4,"XRP":39,"XDG":428,"ADA":206,"LTC":44,"DOT":72,"LINK":97,"XMR":206,"ZEC":987,"XLM":274,
      "BCH":355,"ATOM":432,"SUI":460,"ALGO":177,"PEPE":64,"AVAX":155,"TAO":12,"FIL":496,"UNI":251,"TRX":416,"AAVE":345,
      "XTZ":848,"FET":371,"NEAR":357,"SHIB":67,"ETC":1437,"DASH":1547,"MANA":564,"CRV":417,"ICP":384,"FARTCOIN":3,
      "INJ":595,"PENGU":4,"ONDO":23,"SEI":209,"TIA":86,"KAS":4,"FLOW":587,"TRUMP":20}
def alias(sym):
    s = sym[3:-3] if sym.startswith("PF_") and sym.endswith("USD") else None
    return {"XBT":"XBT","BTC":"XBT","DOGE":"XDG"}.get(s, s)
def snap():
    req = urllib.request.Request(URL, headers={"User-Agent": "ct109-spread-check/1"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())
def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    gap = float(sys.argv[2]) if len(sys.argv) > 2 else 20.0
    sp = {}; dp = {}; meta = {}
    for k in range(n):
        try:
            d = snap()
        except Exception as e:
            print("Schnappschuss %d Fehler: %s" % (k, type(e).__name__)); time.sleep(gap); continue
        for t in d.get("tickers", []):
            nm = alias(t.get("symbol", ""))
            if nm is None or not t.get("bid") or not t.get("ask") or t.get("suspended"): continue
            b, a = float(t["bid"]), float(t["ask"])
            if b <= 0 or a <= 0: continue
            mid = (a + b) / 2
            sp.setdefault(nm, []).append((a - b) / mid * 1e4)
            dp.setdefault(nm, []).append(min(float(t.get("bidSize") or 0) * b, float(t.get("askSize") or 0) * a))
            meta[nm] = (float(t.get("volumeQuote") or 0), float(t.get("openInterest") or 0) * mid,
                        float(t.get("fundingRate") or 0), t.get("symbol"))
        if k < n - 1: time.sleep(gap)
    print("Schnappschuesse: bis zu %d, Abstand %.0f s; Zeit (UTC): %s" % (n, gap, time.strftime("%Y-%m-%d %H:%M", time.gmtime())))
    print("Symbol | Ereignisse(K6) | n | Spread Median bp | Spread p90 bp | Tiefe Median USD | Vol24h USD | OI USD | Funding(rate)")
    tot = 0; wsum = 0.0; miss = []
    for nm in POOL:
        if nm not in sp:
            miss.append(nm); continue
        s = sorted(sp[nm]); m = statistics.median(s); p90 = s[int(0.9 * (len(s) - 1))]
        dep = statistics.median(dp[nm]); v, oi, fr, sy = meta[nm]
        print("%s | %d | %d | %.1f | %.1f | %.0f | %.0f | %.0f | %.6f" % (sy, EV[nm], len(s), m, p90, dep, v, oi, fr))
        tot += EV[nm]; wsum += EV[nm] * m
    if tot: print("ereignisgewichteter Median-Spread (bp): %.1f ueber %d Ereignisse" % (wsum / tot, tot))
    print("ohne Perp im Ticker: %s" % (", ".join(miss) if miss else "keine"))
main()
