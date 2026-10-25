# fund_hist_v1.py - Phase 0 Funding-Carry: laedt die oeffentliche Funding-Historie der Kraken-Perpetuals (PF_<X>USD) und schreibt je Symbol eine CSV.
# Nur lesend, oeffentlicher Endpunkt, KEIN Schluessel. Daten ab 2026-07-01 werden beim Schreiben verworfen (gesperrt).
# Aufruf (PowerShell, Ordner tools):  python -u fund_hist_v1.py D:\CT109-Data\funding | Out-File -Encoding utf8 fund_hist_out.txt; type fund_hist_out.txt
# Ausgabe: nur Abdeckung (Anzahl Stunden, erste/letzte Zeit, Luecken) und zentrierte Streuung - KEINE Mittelwerte/Vorzeichen des Funding.
import sys, os, json, time, math, hashlib, urllib.request, urllib.error
from datetime import datetime, timezone
URL = "https://futures.kraken.com/derivatives/api/v4/historicalfundingrates?symbol=%s"
POOL = ["XBT","ETH","SOL","XRP","XDG","ADA","LTC","DOT","LINK","XMR","ZEC","XLM","BCH","ATOM","SUI","PEPE","AVAX","TAO","FIL","UNI","TRX","AAVE","FET","NEAR","DASH","CRV","ICP","FARTCOIN","INJ","PENGU","ONDO","SEI","TIA","TRUMP"]
CUT = datetime(2026, 7, 1, tzinfo=timezone.utc)
KR = {"XDG": "DOGE"}      # PF-Name der Perps (Spot heisst XDG)
def parse(js):
    rows = []
    for r in js.get("rates", []):
        t = datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00"))
        if t >= CUT: continue
        rows.append((t, float(r["fundingRate"]), float(r["relativeFundingRate"])))
    rows.sort(key=lambda x: x[0])
    return rows
def get(sym):
    for k in range(4):
        try:
            req = urllib.request.Request(URL % sym, headers={"User-Agent": "ct109-fundhist/1"})
            with urllib.request.urlopen(req, timeout=60) as r: return json.loads(r.read().decode("utf-8")), None
        except urllib.error.HTTPError as e:
            if e.code in (404, 400): return None, "http%d" % e.code
            err = "http%d" % e.code
        except Exception as e: err = type(e).__name__
        time.sleep(3 * (k + 1))
    return None, err
def main(outd):
    os.makedirs(outd, exist_ok=True); allsd = []
    print("Skript-SHA256 %s" % hashlib.sha256(open(__file__, "rb").read()).hexdigest()[:16], flush=True)
    print("Symbol | Zeilen | erste | letzte | Luecken >2h | zentrierte Streuung relativ (bp/h) | Datei", flush=True)
    for x in POOL:
        sym = "PF_%sUSD" % KR.get(x, x)
        js, err = get(sym)
        if js is None: print("%s | FEHLER %s" % (sym, err), flush=True); time.sleep(2); continue
        rows = parse(js)
        if not rows: print("%s | leer (Antwortschluessel: %s)" % (sym, list(js.keys())), flush=True); time.sleep(2); continue
        p = os.path.join(outd, sym + ".csv")
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write("timestamp,fundingRate,relativeFundingRate\n")
            for t, a, b in rows: f.write("%s,%.12g,%.12g\n" % (t.isoformat(), a, b))
        rel = [r[2] for r in rows]; m = sum(rel) / len(rel)
        sd = math.sqrt(sum((v - m) ** 2 for v in rel) / max(1, len(rel) - 1)) * 1e4
        gaps = sum(1 for i in range(1, len(rows)) if (rows[i][0] - rows[i - 1][0]).total_seconds() > 7200)
        print("%s | %d | %s | %s | %d | %.2f | %s" % (sym, len(rows), rows[0][0].date(), rows[-1][0].date(), gaps, sd, p), flush=True)
        time.sleep(1.5)
    print("FERTIG", flush=True)
if __name__ == "__main__": main(sys.argv[1] if len(sys.argv) > 1 else r"D:\CT109-Data\funding")
