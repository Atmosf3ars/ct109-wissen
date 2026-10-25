# count_events_v4.py - E4: Zaehlung fuer Order-Flow-Kandidat K6 (Volumenschock mit Aggressor-Ungleichgewicht)
# Aufruf: python count_events_v4.py <agg-Ordner> [Paare...]   (Standard: 41-Paare-Pool)
# Ereignis (Paar-Stunde h): Notional_h >= m * Median(Notional der 720 Vorstunden) UND |Imbalance_h| >= i, Imbalance = (vol_b - vol_s)/(vol_b + vol_s).
# Ausgabe NUR Zaehlungen (Ereignisse, Episoden, Richtung, Jahre, Zustaende) und Betrags-/Streuungskennzahlen der 4-h-Folgerendite
# (zentriert, ohne Vorzeichenbezug zur Ereignisrichtung). KEINE Fortsetzungs-/Umkehr-Statistik.
import sys, os, csv, math
import numpy as np
from collections import defaultdict
import count_events_v2 as v2
import count_cs_v1 as cs

START = v2.START; CUT = v2.CUT
RASTER_M = (5, 10, 20)
RASTER_I = (0.3, 0.5, 0.7)
HOURS_BACK = 720

def hourly(path):
    """Stundenreihen aus 1-Min-Aggregat: Notional, vol_b, vol_s, erster Open, letzter Close (Fehldruck-Regel wie v2.load)."""
    agg = {}
    prev = None
    with open(path, newline="") as f:
        r = csv.reader(f); next(r)
        for row in r:
            t = int(row[0])
            if t >= CUT: break
            o = float(row[1]); h = float(row[2]); l = float(row[3]); c = float(row[4])
            bad = l <= 0 or l < 0.7 * h or (prev is not None and (l < 0.7 * prev or h > 1.4 * prev))
            prev = c
            if bad: continue
            k = t // 3600
            a = agg.get(k)
            if a is None:
                agg[k] = [float(row[10]), float(row[6]), float(row[7]), o, c]
            else:
                a[0] += float(row[10]); a[1] += float(row[6]); a[2] += float(row[7]); a[4] = c
    return agg

def events_for_pair(agg, st):
    ks = sorted(agg)
    if len(ks) < HOURS_BACK + 10: return []
    k0, k1 = ks[0], ks[-1]
    n = k1 - k0 + 1
    notional = np.zeros(n); vb = np.zeros(n); vs = np.zeros(n); op = np.full(n, np.nan)
    for k, a in agg.items():
        i = k - k0
        notional[i] = a[0]; vb[i] = a[1]; vs[i] = a[2]; op[i] = a[3]
    med = np.full(n, np.nan)
    CH = 4000
    for s in range(HOURS_BACK, n, CH):
        e = min(n, s + CH)
        idx = np.arange(s, e)[:, None] - np.arange(1, HOURS_BACK + 1)[None, :]
        med[s:e] = np.median(notional[idx], axis=1)
    tot = vb + vs
    imb = np.divide(vb - vs, tot, out=np.zeros(n), where=tot > 0)
    out = []   # (stunde_epoch, ratio, imb, ret4h_bp oder nan, zustand)
    for i in range(HOURS_BACK, n - 5):
        if not (med[i] > 0 and tot[i] > 0): continue
        t = (k0 + i) * 3600
        if t < START: continue
        ratio = notional[i] / med[i]
        if ratio < RASTER_M[0]: continue
        if np.isnan(op[i + 1]) or np.isnan(op[i + 5]) or op[i + 1] <= 0 or op[i + 5] <= 0: continue
        r = math.log(op[i + 5] / op[i + 1]) * 1e4
        s = st.get(t // 86400)
        if s is None: continue
        out.append((t, ratio, imb[i], r, s))
    return out

def episodes(times, gap):
    ep = []; last = None
    for t in sorted(times):
        if last is None or t - last >= gap: ep.append(t)
        last = t
    return ep

def main(agg_dir, pairs):
    xbt = v2.load(os.path.join(agg_dir, "XBTUSD_1m.csv"))
    st = v2.state_table(v2.hourly(xbt[0], xbt[4]))
    allev = {}
    for p in pairs:
        path = os.path.join(agg_dir, p + "USD_1m.csv")
        if not os.path.exists(path): continue
        ev = events_for_pair(hourly(path), st)
        allev[p] = ev
        print("%s: Stunden-Ereignisse (Verhaeltnis >= %d): %d" % (p, RASTER_M[0], len(ev)), flush=True)
    print("== Raster (m = Volumenverhaeltnis, i = |Imbalance|): Ereignisse / Episoden (4-h-Cluster ueber alle Paare) / Kaeufer-Anteil / je Zustand (Episoden) / sd der 4-h-Folgerendite (zentriert) / Mittel |r|")
    for m in RASTER_M:
        for i in RASTER_I:
            sel = [(p, e) for p, ev in allev.items() for e in ev if e[1] >= m and abs(e[2]) >= i]
            if not sel:
                print("m=%d i=%.1f: 0" % (m, i)); continue
            times = [e[0] for _, e in sel]
            ep = episodes(times, 4 * 3600)
            buy = sum(1 for _, e in sel if e[2] > 0) / len(sel)
            per_state = [len(episodes([e[0] for _, e in sel if e[4] == s], 4 * 3600)) for s in (0, 1, 2)]
            r = [e[3] for _, e in sel]
            mu = sum(r) / len(r)
            sd = math.sqrt(sum((x - mu) ** 2 for x in r) / (len(r) - 1)) if len(r) > 1 else float("nan")
            ab = sum(abs(x) for x in r) / len(r)
            yrs = ", ".join("%d:%d" % (y, len([t for t in ep if v2.yr(t) == y])) for y in range(2019, 2027))
            print("m=%4.1f i=%.1f: Ereignisse %6d, Episoden %5d, Kaeuferanteil %.2f, Zustaende %s, sd %.0f bp, Mittel|r| %.0f bp; Episoden/Jahr %s" % (m, i, len(sel), len(ep), buy, per_state, sd, ab, yrs))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:] if len(sys.argv) > 2 else cs.POOL)
