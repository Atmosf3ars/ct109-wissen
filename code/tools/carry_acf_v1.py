# carry_acf_v1.py - CARRY-HOLD: Autokorrelation (nur Struktur, kein Mittelwert) der woechentlichen Funding-Summe und der Wochen-P&L "immer-an" (Funding - Basisaenderung)
# NUR Trainingsfenster 2019-09-08..2023-12-31 (hart). Ausgabe: sigma (zentriert), ACF Lag 1..8, Varianzaufschlag fuer den Mittelwert (Bartlett, Lags <= 12) und Zahl der Wochen.
# Aufruf: python -u carry_acf_v1.py <binance-klines> <funding-binance>
import sys, os, io, csv, zipfile, math
from datetime import date, datetime, timedelta, timezone
A = date(2019, 9, 8); B = date(2023, 12, 31)
def months():
    y, m = 2019, 9
    while (y, m) <= (2023, 12):
        yield "%04d-%02d" % (y, m); m += 1
        if m == 13: y += 1; m = 1
def load(p):
    out = {}; z = zipfile.ZipFile(p)
    for n in z.namelist():
        for row in csv.reader(io.TextIOWrapper(z.open(n), "utf-8")):
            try: t = int(row[0]); c = float(row[4])
            except ValueError: continue
            if t > 10**14: t //= 1000
            out[datetime.fromtimestamp(t / 1000, timezone.utc).date()] = c
    return out
def acf(x, k):
    n = len(x); m = sum(x) / n; v = sum((a - m) ** 2 for a in x)
    return sum((x[i] - m) * (x[i + k] - m) for i in range(n - k)) / v
def sd(x):
    n = len(x); m = sum(x) / n; return math.sqrt(sum((a - m) ** 2 for a in x) / (n - 1))
def report(name, x):
    r = [acf(x, k) for k in range(1, 13)]
    infl = 1 + 2 * sum((1 - k / 13.0) * r[k - 1] for k in range(1, 13))        # Bartlett-Varianzaufschlag fuer den Mittelwert
    print("%s | Wochen %d | sigma %.1f bp | ACF1..8: %s | Varianzaufschlag(Bartlett,12) %.2f => SE-Faktor %.2f" % (name, len(x), sd(x), ",".join("%.2f" % v for v in r[:8]), infl, math.sqrt(max(infl, 0))))
def main(kd, fd):
    for s in ["BTCUSDT", "ETHUSDT"]:
        spot = {}; perp = {}
        for mo in months():
            for kind, store in (("spot", spot), ("um", perp)):
                fp = os.path.join(kd, "%s_%s_%s.zip" % (kind, s, mo))
                if os.path.exists(fp) and os.path.getsize(fp) > 0: store.update(load(fp))
        fund = {}
        with open(os.path.join(fd, s + ".csv"), encoding="utf-8") as f:
            for r in csv.DictReader(f):
                d = datetime.fromtimestamp(int(r["fundingTimeMs"]) / 1000, timezone.utc).date()
                if d <= B: fund[d] = fund.get(d, 0.0) + float(r["fundingRate"])
        d = A
        while d.weekday() != 6: d += timedelta(days=1)
        fw = []; pw = []; prev = None
        while d <= B:
            f = sum(fund.get(d - timedelta(days=k), 0.0) for k in range(7)) * 1e4
            fw.append(f)
            if d in spot and d in perp:
                bv = math.log(perp[d]) - math.log(spot[d])
                if prev is not None: pw.append(f - (bv - prev) * 1e4)
                prev = bv
            else: prev = None
            d += timedelta(days=7)
        report(s + " Funding-Wochensumme", fw); report(s + " Wochen-P&L immer-an", pw)
        # Teilfenster 2022-01..2023-12 (Niedrig-Funding-Regime im Training), ohne Mittelwert
        sub = [fw[i] for i in range(len(fw)) if (A + timedelta(days=7 * (i + 1))) >= date(2022, 1, 1)]
        report(s + " Funding-Wochensumme 2022-01..2023-12", sub)
if __name__ == "__main__": main(sys.argv[1], sys.argv[2])
