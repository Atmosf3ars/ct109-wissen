# fund_probe_v1.py - Phase 0 Funding: wie weit reicht die oeffentliche Funding-Historie zurueck? Nur Anzahl/erste/letzte Zeit/Zeitschritt, KEINE Funding-Werte.
# Aufruf (PowerShell): python -u fund_probe_v1.py | Out-File -Encoding utf8 fund_probe_out.txt; type fund_probe_out.txt
import json, time, urllib.request, urllib.error, hashlib
from datetime import datetime, timezone
from collections import Counter
def get(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ct109-fundprobe/1"})
        with urllib.request.urlopen(req, timeout=60) as r: return json.loads(r.read().decode("utf-8")), None
    except urllib.error.HTTPError as e: return None, "http%d" % e.code
    except Exception as e: return None, type(e).__name__
def tsx(s): return datetime.fromisoformat(s.replace("Z", "+00:00"))
def kr(url, label):
    js, err = get(url)
    if js is None: print("%-34s | FEHLER %s" % (label, err)); return
    rows = js.get("rates") or []
    if not rows: print("%-34s | leer, Schluessel %s" % (label, list(js.keys()))); return
    t = [tsx(r["timestamp"]) for r in rows]; t.sort()
    st = Counter(int((t[i] - t[i - 1]).total_seconds() // 60) for i in range(1, len(t))).most_common(3)
    print("%-34s | %d Zeilen | %s .. %s | haeufigste Schritte (min): %s | Felder %s" % (label, len(t), t[0].date(), t[-1].date(), st, sorted(rows[0].keys())))
def binance(sym):
    n = 0; first = None; last = None; start = int(datetime(2019, 1, 1, tzinfo=timezone.utc).timestamp() * 1000); err = None
    while True:
        js, err = get("https://fapi.binance.com/fapi/v1/fundingRate?symbol=%s&startTime=%d&limit=1000" % (sym, start))
        if js is None or not js: break
        n += len(js); first = first or js[0]["fundingTime"]; last = js[-1]["fundingTime"]
        start = last + 1
        if len(js) < 1000: break
        time.sleep(0.4)
    if first is None: print("Binance %-14s | FEHLER/leer %s" % (sym, err)); return
    f = datetime.fromtimestamp(first / 1000, timezone.utc).date(); l = datetime.fromtimestamp(last / 1000, timezone.utc).date()
    print("Binance %-14s | %d Zeilen | %s .. %s | (8-h-Takt)" % (sym, n, f, l))
print("Skript-SHA256 %s" % hashlib.sha256(open(__file__, "rb").read()).hexdigest()[:16])
kr("https://futures.kraken.com/derivatives/api/v4/historicalfundingrates?symbol=PF_XBTUSD", "Kraken v4 PF_XBTUSD")
time.sleep(1.5)
kr("https://futures.kraken.com/derivatives/api/v3/historicalfundingrates?symbol=PF_XBTUSD", "Kraken v3 PF_XBTUSD")
time.sleep(1.5)
kr("https://futures.kraken.com/derivatives/api/v3/historicalfundingrates?symbol=PI_XBTUSD", "Kraken v3 PI_XBTUSD (invers)")
time.sleep(1.5)
kr("https://futures.kraken.com/derivatives/api/v3/historicalfundingrates?symbol=PI_ETHUSD", "Kraken v3 PI_ETHUSD (invers)")
for s in ("BTCUSDT", "ETHUSDT", "SOLUSDT"): binance(s); time.sleep(1)
print("FERTIG")
