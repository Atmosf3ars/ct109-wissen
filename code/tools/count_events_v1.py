# count_events_v1.py - reine Ereigniszaehlung (keine Nachereignis-Renditen)
# python count_events_v1.py shocks <agg-Ordner>      (liest XBTUSD_1m.csv, ETHUSD_1m.csv, SOLUSD_1m.csv)
# python count_events_v1.py funding <funding-Ordner> (liest <SYMBOL>/*.zip der Binance-Funding-Monatsdateien)
import sys, os, csv, glob, zipfile, io
from collections import deque, defaultdict
from datetime import datetime, timezone

def year_of(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).year

def shocks(agg_dir):
    THR = [0.02, 0.03, 0.05]      # Rueckgang vom 15-Min-Hoch (Tief/Hoch - 1)
    WIN = 15 * 60                 # Fenster in Sekunden
    COOL = 60 * 60                # Ereignis-Abkuehlung 1 h
    GAP = 24 * 3600               # neue Episode nach >= 24 h ohne Ereignis
    for name in ("XBTUSD", "ETHUSD", "SOLUSD"):
        path = os.path.join(agg_dir, name + "_1m.csv")
        if not os.path.exists(path):
            print(name, "FEHLT"); continue
        ev = {t: defaultdict(int) for t in THR}
        ep = {t: defaultdict(int) for t in THR}
        last_ev = {t: None for t in THR}
        cool_until = {t: -1 for t in THR}
        dq = deque()              # (ts, high) mit absteigenden Hochs
        prev_close = None
        verworfen = 0; bars = 0
        with open(path, newline="") as f:
            r = csv.reader(f); next(r)
            for row in r:
                ts = int(row[0]); hi = float(row[2]); lo = float(row[3]); cl = float(row[4])
                bars += 1
                # Plausibilitaet: Fehlticks verwerfen
                if lo <= 0 or lo / hi < 0.7 or (prev_close is not None and (lo / prev_close < 0.7 or hi / prev_close > 1.4)):
                    verworfen += 1
                    continue
                prev_close = cl
                while dq and dq[0][0] < ts - WIN + 60:
                    dq.popleft()
                while dq and dq[-1][1] <= hi:
                    dq.pop()
                dq.append((ts, hi))
                H = dq[0][1]
                dd = lo / H - 1.0
                for t in THR:
                    if dd <= -t and ts >= cool_until[t]:
                        y = year_of(ts)
                        ev[t][y] += 1
                        if last_ev[t] is None or ts - last_ev[t] >= GAP:
                            ep[t][y] += 1
                        last_ev[t] = ts
                        cool_until[t] = ts + COOL
        years = sorted(set(y for t in THR for y in ev[t]) | set(range(2013, 2027)))
        print("== %s  Minuten-Bars %d, verworfen (Fehlticks) %d" % (name, bars, verworfen))
        print("Jahr  " + "  ".join("E%d%%/P%d%%" % (int(t * 100), int(t * 100)) for t in THR) + "   (E=Ereignisse, P=unabhaengige Episoden, Abstand >=24h)")
        tot = {t: [0, 0] for t in THR}
        for y in years:
            cells = []
            for t in THR:
                e = ev[t].get(y, 0); p = ep[t].get(y, 0)
                tot[t][0] += e; tot[t][1] += p
                cells.append("%4d/%-3d" % (e, p))
            if any(ev[t].get(y, 0) for t in THR):
                print("%d  " % y + "  ".join(cells))
        print("Summe " + "  ".join("%4d/%-3d" % (tot[t][0], tot[t][1]) for t in THR))

def funding(fdir):
    POS = [0.0003, 0.0005, 0.0010]   # je 8 h: 3, 5, 10 bp
    NEG = [-0.0001, -0.0003, -0.0005]
    GAP = 72 * 3600
    for sym in ("BTCUSDT", "ETHUSDT", "SOLUSDT"):
        files = sorted(glob.glob(os.path.join(fdir, sym, "*.zip")))
        if not files:
            print(sym, "FEHLT"); continue
        rows = []
        for fn in files:
            with zipfile.ZipFile(fn) as z:
                for nm in z.namelist():
                    txt = io.TextIOWrapper(z.open(nm), encoding="utf-8")
                    rd = csv.reader(txt); hdr = next(rd)
                    ci = 0
                    ri = len(hdr) - 1
                    for i, h in enumerate(hdr):
                        if "rate" in h.lower(): ri = i
                    for row in rd:
                        try:
                            rows.append((int(row[ci]) / 1000.0, float(row[ri])))
                        except Exception:
                            pass
        rows.sort()
        print("== %s  Funding-Zeilen %d, von %s bis %s" % (sym, len(rows), datetime.fromtimestamp(rows[0][0], tz=timezone.utc).strftime("%Y-%m-%d"), datetime.fromtimestamp(rows[-1][0], tz=timezone.utc).strftime("%Y-%m-%d")))
        by_year = defaultdict(list)
        for ts, r in rows:
            by_year[year_of(ts)].append(r)
        print("Jahr   n   Mittel(bp)  Median(bp)  " + "  ".join("P>=%dbp/E" % round(t * 1e4) for t in POS) + "  " + "  ".join("P<=%dbp/E" % round(t * 1e4) for t in NEG))
        for y in sorted(by_year):
            v = sorted(by_year[y])
            mean = sum(v) / len(v) * 1e4
            med = v[len(v) // 2] * 1e4
            cells = []
            for t in POS + NEG:
                last = None; e = 0; p = 0
                for ts, r in rows:
                    if year_of(ts) != y: continue
                    hit = r >= t if t > 0 else r <= t
                    if hit:
                        e += 1
                        if last is None or ts - last >= GAP: p += 1
                        last = ts
                cells.append("%4d/%-4d" % (p, e))
            print("%d %5d  %9.2f  %9.2f  " % (y, len(v), mean, med) + "  ".join(cells))

if __name__ == "__main__":
    if sys.argv[1] == "shocks": shocks(sys.argv[2])
    elif sys.argv[1] == "funding": funding(sys.argv[2])
