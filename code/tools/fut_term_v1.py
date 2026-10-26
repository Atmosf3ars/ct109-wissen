# fut_term_v1.py - Phase 0 CARRY-DATED (D57): Terminkurve datierter BTC-Futures (Binance-Vision, Quartals-Lieferkontrakte, 1d) gegen Spot BTCUSDT.
# Misst nur den ex ante bekannten Aufschlag am Rolltag (Einstieg am Verfallstag des Vorgaengers, Kontrakt = naechster Verfall); KEIN Renditetest eines Signals.
# Bei Haltedauer bis zum Verfall und Abrechnung zum Index entspricht der Aufschlag am Einstieg dem Ertrag der Position vor Kosten (Abrechnungsabweichung zum Spot ignoriert [A]).
# Nichts nach 2026-06-30. Aufruf: python -u fut_term_v1.py <ausgabeordner> <binance-klines-ordner>
import sys, os, io, csv, zipfile, calendar, urllib.request, urllib.error, math
from datetime import date, datetime, timedelta, timezone
CUT = date(2026, 7, 1)
def last_friday(y, m):
    d = date(y, m, calendar.monthrange(y, m)[1])
    while d.weekday() != 4: d -= timedelta(days=1)
    return d
def expiries():
    out = []
    for y in range(2020, 2027):
        for m in (3, 6, 9, 12):
            e = last_friday(y, m)
            if date(2020, 3, 1) <= e < CUT: out.append(e)
    return out
def get(url, p):
    if os.path.exists(p) and os.path.getsize(p) > 0: return True
    try:
        with urllib.request.urlopen(url, timeout=60) as r, open(p, "wb") as f: f.write(r.read())
        return True
    except urllib.error.HTTPError as e:
        if e.code in (403, 404): return False
        raise
def load(p):
    out = {}; z = zipfile.ZipFile(p)
    for n in z.namelist():
        for row in csv.reader(io.TextIOWrapper(z.open(n), "utf-8")):
            try: t = int(row[0]); c = float(row[4])
            except ValueError: continue
            if t > 10**14: t //= 1000
            d = datetime.fromtimestamp(t / 1000, timezone.utc).date()
            if d < CUT: out[d] = c
    return out
def months_between(a, b):
    y, m = a.year, a.month; out = []
    while (y, m) <= (b.year, b.month):
        out.append("%04d-%02d" % (y, m)); m += 1
        if m == 13: y += 1; m = 1
    return out
def contract(outd, kind, sym, e):
    px = {}; n = 0
    for mo in months_between(e - timedelta(days=270), e):
        fn = "%s-1d-%s.zip" % (sym, mo); p = os.path.join(outd, kind + "_" + fn)
        if get("https://data.binance.vision/data/futures/%s/monthly/klines/%s/1d/%s" % (kind, sym, fn), p): px.update(load(p)); n += 1
    return px
def quantile(x, q):
    x = sorted(x); k = (len(x) - 1) * q; f = int(math.floor(k)); c = min(f + 1, len(x) - 1); return x[f] + (x[c] - x[f]) * (k - f)
def main(outd, kd):
    os.makedirs(outd, exist_ok=True); spot = {}
    for fn in sorted(os.listdir(kd)):
        if fn.startswith("spot_BTCUSDT_"): spot.update(load(os.path.join(kd, fn)))
    ex = expiries()
    for kind, base, label in (("cm", "BTCUSD_", "COIN-M BTCUSD"), ("um", "BTCUSDT_", "USDT-M BTCUSDT")):
        print("== %s ==" % label); cyc = []
        px = {e: contract(outd, kind, base + e.strftime("%y%m%d"), e) for e in ex}
        print("Kontrakte mit Daten: %d von %d" % (sum(1 for e in ex if px[e]), len(ex)))
        for k in range(1, len(ex)):
            entry, e = ex[k - 1], ex[k]
            for off in range(0, 4):
                d = entry + timedelta(days=off)
                if d in px[e] and d in spot: break
            else: continue
            dte = (e - d).days; prem = (px[e][d] / spot[d] - 1) * 1e4
            cyc.append((d, e, dte, prem, prem * 365.0 / dte / 100.0))
        print("Zyklen %d | Einstieg | Verfall | Tage | Aufschlag bp | annualisiert %%" % len(cyc))
        for d, e, dte, prem, ann in cyc: print("%s | %s | %d | %.0f | %.1f" % (d, e, dte, prem, ann))
        if cyc:
            ann = [c[4] for c in cyc]
            print("annualisiert %%: min %.1f, q25 %.1f, Median %.1f, q75 %.1f, max %.1f; Zyklen mit Aufschlag > 84 bp (Einzelzyklus-Kosten): %d von %d; mit annualisiert < 3 %%: %d" % (min(ann), quantile(ann, .25), quantile(ann, .5), quantile(ann, .75), max(ann), sum(1 for c in cyc if c[3] > 84), len(cyc), sum(1 for a in ann if a < 3)))
            for y in sorted(set(c[1].year for c in cyc)):
                cs = [c for c in cyc if c[1].year == y]
                print("Verfallsjahr %d: Zyklen %d, Summe Aufschlaege %.0f bp, abzueglich einmal 84 bp Spot-/Futures-Kosten und je Roll 4 bp: %.0f bp" % (y, len(cs), sum(c[3] for c in cs), sum(c[3] for c in cs) - 84 - 4 * len(cs)))
if __name__ == "__main__": main(sys.argv[1], sys.argv[2])
