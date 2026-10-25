# insider_cover_v1.py - Abdeckung und Liquiditaet der Insider-Cluster (INSIDER-ALL, Phase 0). KEINE Renditen, nur Zaehlungen.
# python insider_cover_v1.py <cluster-csv> <alpaca-daily-ordner>
# Pro Cluster (k>=3, Preis>=2, Clusterdatum 2016-04-01 .. 2026-05-31): Bars fuer die 20 Handelstage davor vorhanden (>= 16)?
# Mindestens 21 Handelstage danach vorhanden (Haltedauer 20 Tage + Einstiegstag)? Median-Dollarvolumen (Schluss x Volumen) der 20 Tage davor.
# Gibt aus: Zaehlung je Jahr, Dollarvolumen-Klassen, Anteil mit Bars-Luecke, Delisting-Anteil (Bars enden vor Tag +21). Keine Kurse/Renditen.
import sys, os, csv, bisect, statistics
from collections import defaultdict
from datetime import date

def load_bars(path):
    d = []; cl = []; vol = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            d.append(r["date"]); cl.append(float(r["close"])); vol.append(float(r["volume"]))
    return d, cl, vol

def main(csvp, folder):
    ev = []
    with open(csvp, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if int(r["kmin"]) != 3 or float(r["avg_price"]) < 2.0: continue
            if not ("2016-04-01" <= r["cluster_date"] <= "2026-05-31"): continue
            s = r["symbol"].strip().upper()
            if not s or " " in s: continue
            ev.append((s, r["cluster_date"], float(r["total_usd"])))
    cache = {}
    tiers = ["<300k", "300k-2M", "2M-10M", ">=10M"]
    by_year = defaultdict(lambda: [0, 0, 0, 0, 0]); tier_n = defaultdict(int)
    nobars = nopre = nopost = delist = 0; used = 0
    for s, cd, tot in ev:
        y = int(cd[:4])
        by_year[y][0] += 1
        p = os.path.join(folder, s.replace("/", "_") + ".csv")
        if not os.path.exists(p):
            p2 = os.path.join(folder, s.replace("-", ".") + ".csv")
            p = p2 if os.path.exists(p2) else None
        if p is None: nobars += 1; continue
        if p not in cache: cache[p] = load_bars(p)
        d, cl, vol = cache[p]
        i = bisect.bisect_right(d, cd)          # erster Handelstag nach dem Clusterdatum
        pre = [k for k in range(max(0, i - 20), i)]
        if len(pre) < 16 or (date.fromisoformat(cd) - date.fromisoformat(d[pre[0]])).days > 40: nopre += 1; continue
        if i + 21 > len(d):
            delist += 1; by_year[y][3] += 1
            if i >= len(d): nopost += 1; continue
        dv = statistics.median(cl[k] * vol[k] for k in pre)
        t = 0 if dv < 3e5 else 1 if dv < 2e6 else 2 if dv < 1e7 else 3
        tier_n[t] += 1; by_year[y][1] += 1
        if t >= 1: by_year[y][2] += 1
        used += 1
    print("Cluster (k>=3, Preis>=2, 2016-04..2026-05): %d; ohne Bars-Datei %d; zu wenig Vorlauf-Bars %d; Bars enden vor Tag +21 (Delisting/Luecke) %d (davon ohne jeden Folgetag %d); verwendbar %d" % (len(ev), nobars, nopre, delist, nopost, used))
    print("Dollarvolumen-Klassen (Median 20 Tage davor): " + ", ".join("%s: %d" % (tiers[t], tier_n[t]) for t in range(4)))
    print("Jahr | Cluster | verwendbar | davon >= 300k USD | Bars enden zu frueh")
    for y in sorted(by_year):
        a = by_year[y]; print("%d | %d | %d | %d | %d" % (y, a[0], a[1], a[2], a[3]))
    ok = sum(tier_n[t] for t in (1, 2, 3))
    print("verwendbar mit Dollarvolumen >= 300k USD: %d; >= 2M: %d; >= 10M: %d" % (ok, tier_n[2] + tier_n[3], tier_n[3]))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
