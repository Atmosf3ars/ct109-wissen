# basis_probe_v1.py - Phase 0 CARRY-HOLD: laedt Binance-Vision-Monatsdateien (Tageskerzen, Spot und USDM-Perp) fuer BTCUSDT/ETHUSDT
# (Monate 2019-09 .. 2026-06; nichts nach 30.06.2026) und gibt NUR Anzahlen und ZENTRIERTE Streuungen aus (keine Mittelwerte von Funding/Basis,
# keine Vorzeichenstatistik): Wochen je Fenster, sigma der woechentlichen Basis-Aenderung (ln perp_close - ln spot_close, Wochenende Sonntag),
# sigma der woechentlichen Funding-Summe. Fenster: Training 2019-09..2023-12, Test 2024-01..2026-06.
# Aufruf: python -u basis_probe_v1.py <ausgabeordner> <funding-binance-ordner>
import sys, os, io, csv, zipfile, math, urllib.request, urllib.error, hashlib
from datetime import date, datetime, timedelta, timezone
SYMS = ["BTCUSDT", "ETHUSDT"]
def months():
    y, m = 2019, 9
    while (y, m) <= (2026, 6):
        yield "%04d-%02d" % (y, m); m += 1
        if m == 13: y += 1; m = 1
def get(url, p):
    if os.path.exists(p) and os.path.getsize(p) > 0: return True
    try:
        with urllib.request.urlopen(url, timeout=60) as r, open(p, "wb") as f: f.write(r.read())
        return True
    except urllib.error.HTTPError as e:
        if e.code == 404: return False
        raise
def load(p):
    out = {}
    z = zipfile.ZipFile(p)
    for n in z.namelist():
        for row in csv.reader(io.TextIOWrapper(z.open(n), "utf-8")):
            try: t = int(row[0]); c = float(row[4])
            except ValueError: continue
            if t > 10**14: t //= 1000
            out[datetime.fromtimestamp(t / 1000, timezone.utc).date()] = c
    return out
def sd(x):
    n = len(x)
    if n < 3: return float("nan")
    m = sum(x) / n; return math.sqrt(sum((v - m) ** 2 for v in x) / (n - 1))
def main(outd, fd):
    os.makedirs(outd, exist_ok=True); h = hashlib.sha256()
    for s in SYMS:
        spot = {}; perp = {}; miss = 0
        for mo in months():
            for kind, store, base in (("spot", spot, "https://data.binance.vision/data/spot/monthly/klines/%s/1d/%s-1d-%s.zip"), ("um", perp, "https://data.binance.vision/data/futures/um/monthly/klines/%s/1d/%s-1d-%s.zip")):
                p = os.path.join(outd, "%s_%s_%s.zip" % (kind, s, mo))
                if not get(base % (s, s, mo), p): miss += 1; continue
                store.update(load(p))
        print("%s: Tage spot %d, perp %d, fehlende Monatsdateien %d" % (s, len(spot), len(perp), miss), flush=True)
        # Funding je Tag (Summe der 8h-Raten)
        fund = {}
        with open(os.path.join(fd, s + ".csv"), encoding="utf-8") as f:
            for r in csv.DictReader(f):
                d = datetime.fromtimestamp(int(r["fundingTimeMs"]) / 1000, timezone.utc).date()
                if d <= date(2026, 6, 30): fund[d] = fund.get(d, 0.0) + float(r["fundingRate"])
        for name, a, b in (("Training 2019-09..2023-12", date(2019, 9, 8), date(2023, 12, 31)), ("Test 2024-01..2026-06", date(2024, 1, 1), date(2026, 6, 30))):
            ends = []; d = a
            while d.weekday() != 6: d += timedelta(days=1)
            while d <= b: ends.append(d); d += timedelta(days=7)
            bas = []; fw = []; prev = None
            for e in ends:
                if e in spot and e in perp:
                    bv = math.log(perp[e]) - math.log(spot[e])
                    if prev is not None: bas.append((bv - prev) * 1e4)
                    prev = bv
                    fw.append(sum(fund.get(e - timedelta(days=k), 0.0) for k in range(7)) * 1e4)
                else: prev = None
            print("%s | %s | Wochen %d | Basis-Aenderungen %d, sigma %.1f bp/Woche | Funding-Wochensumme n %d, sigma %.1f bp/Woche" % (s, name, len(ends), len(bas), sd(bas), len(fw), sd(fw)), flush=True)
if __name__ == "__main__": main(sys.argv[1], sys.argv[2])
