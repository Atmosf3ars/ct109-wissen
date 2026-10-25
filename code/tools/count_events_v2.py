# count_events_v2.py - Zaehlungen fuer die Runde-3-Spec (Zustaende, relative Funding-Schwelle, Wochenende, Streuung nur als Betrag)
# Keine Vorzeichen-Statistik der Nachereignis-Renditen: nur Streuung (zentriert) und Mittelwert des Betrags.
# python count_events_v2.py all <agg-Ordner> <funding-Ordner>
import sys, os, csv, glob, zipfile, io, math
from array import array
from bisect import bisect_left
from collections import deque, defaultdict
from datetime import datetime, timezone, date

START = datetime(2019, 1, 1, tzinfo=timezone.utc).timestamp()
CUT = datetime(2026, 7, 1, tzinfo=timezone.utc).timestamp()

def yr(ts): return datetime.fromtimestamp(ts, tz=timezone.utc).year

def load(path):
    ts = array("q"); op = array("d"); hi = array("d"); lo = array("d"); cl = array("d")
    with open(path, newline="") as f:
        r = csv.reader(f); next(r)
        for row in r:
            t = int(row[0])
            if t >= CUT: break
            ts.append(t); op.append(float(row[1])); hi.append(float(row[2])); lo.append(float(row[3])); cl.append(float(row[4]))
    return ts, op, hi, lo, cl

def hourly(ts, cl):
    d = {}
    for t, c in zip(ts, cl):
        d[t // 3600] = c
    return d

def state_table(hc):
    """tagesweise Zustand (0 NIEDRIG,1 MITTEL,2 HOCH) aus BTC-RV30-Perzentil gegen 3 Jahre; Zustand fuer Tag D nutzt nur Daten bis D-1"""
    days = {}
    for h in sorted(hc):
        days[h // 24] = hc[h]      # letzter Stundenschluss des Tages
    ds = sorted(days)
    rets = {}
    for a, b in zip(ds, ds[1:]):
        if b == a + 1 and days[a] > 0 and days[b] > 0:
            rets[b] = math.log(days[b] / days[a])
    rv = {}
    for d in ds:
        w = [rets[x] for x in range(d - 29, d + 1) if x in rets]
        if len(w) >= 25:
            m = sum(w) / len(w)
            rv[d] = math.sqrt(sum((x - m) ** 2 for x in w) / (len(w) - 1)) * math.sqrt(365)
    st = {}
    keys = sorted(rv)
    for d in range(keys[0] + 365, keys[-1] + 3):
        prev = d - 1
        if prev not in rv: continue
        hist = [rv[x] for x in range(prev - 1095, prev) if x in rv]
        if len(hist) < 365: continue
        p = sum(1 for x in hist if x < rv[prev]) / len(hist)
        st[d] = 0 if p < 1 / 3 else (2 if p > 2 / 3 else 1)
    return st

NAMES = ["NIEDRIG", "MITTEL", "HOCH"]

def episodes(times, gap):
    ep = []
    last = None
    for t in sorted(times):
        if last is None or t - last >= gap: ep.append(t)
        last = t
    return ep

def sd(v):
    if len(v) < 2: return float("nan")
    m = sum(v) / len(v)
    return math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1))

def sim_k4(name, data, st, theta=0.03):
    ts, op, hi, lo, cl = data
    n = len(ts)
    WIN = 15 * 60
    dq = deque(); prev_close = None; blocked = 0
    out = []   # (tau, state, r4h or None)
    i = 0
    while i < n:
        t = ts[i]; h = hi[i]; l = lo[i]
        if l <= 0 or l / h < 0.7 or (prev_close is not None and (l / prev_close < 0.7 or h / prev_close > 1.4)):
            i += 1; continue
        prev_close = cl[i]
        while dq and dq[0][0] < t - WIN + 60: dq.popleft()
        while dq and dq[-1][1] <= h: dq.pop()
        dq.append((t, h))
        if t >= START and t >= blocked and l / dq[0][1] - 1.0 <= -theta:
            tau = t
            sday = st.get(tau // 86400)
            if sday is None:
                i += 1; continue
            low = l; lastnew = t; j = i + 1; r = None
            while j < n and ts[j] <= tau + 7200:
                if lo[j] < low:
                    low = lo[j]; lastnew = ts[j]
                if ts[j] >= tau + 1200 and ts[j] - lastnew >= 600:
                    k = bisect_left(ts, ts[j] + 60)
                    if k < n and ts[k] - (ts[j] + 60) <= 600:
                        m = bisect_left(ts, ts[k] + 14400)
                        if m < n and ts[m] - (ts[k] + 14400) <= 600 and op[k] > 0 and op[m] > 0:
                            r = math.log(op[m] / op[k]) * 1e4
                            blocked = ts[m] + 6 * 3600
                    break
                j += 1
            out.append((tau, sday, r))
            if r is None: blocked = tau + 3600
        i += 1
    return out

def k4(agg):
    hc = {}
    data = {}
    for nm in ("XBTUSD", "ETHUSD"):
        p = os.path.join(agg, nm + "_1m.csv")
        data[nm] = load(p)
        if nm == "XBTUSD": hc = hourly(data[nm][0], data[nm][4])
    st = state_table(hc)
    allev = []
    for nm in ("XBTUSD", "ETHUSD"):
        ev = sim_k4(nm, data[nm], st)
        ent = [e for e in ev if e[2] is not None]
        print("== K4 %s (theta 3 %%, ab 2019-01-01): Ereignisse %d, mit Einstieg %d, ohne Einstieg %d" % (nm, len(ev), len(ent), len(ev) - len(ent)))
        ep = episodes([e[0] for e in ent], 86400)
        print("   unabhaengige Episoden (Abstand >= 24 h): %d; je Zustand: %s" % (len(ep), ", ".join("%s %d" % (NAMES[s], len(episodes([e[0] for e in ent if e[1] == s], 86400))) for s in (0, 1, 2))))
        r = [e[2] for e in ent]
        if len(r) > 1:
            print("   Streuung der 4-h-Rendite (ohne Stop, zentriert): %.0f bp; Mittelwert des Betrags: %.0f bp" % (sd(r), sum(abs(x) for x in r) / len(r)))
            for s in (0, 1, 2):
                rs = [e[2] for e in ent if e[1] == s]
                if len(rs) > 4: print("     %s: n=%d, Streuung %.0f bp" % (NAMES[s], len(rs), sd(rs)))
        allev += ent
    ep = episodes([e[0] for e in allev], 86400)
    print("== K4 XBT+ETH vereinigt: unabhaengige Episoden (24 h): %d; je Zustand: %s" % (len(ep), ", ".join("%s %d" % (NAMES[s], len(episodes([e[0] for e in allev if e[1] == s], 86400))) for s in (0, 1, 2))))
    for y in range(2019, 2027):
        print("   %d: %d" % (y, len([t for t in ep if yr(t) == y])), end="")
    print()
    return st, hc

def fundrel(fdir, st):
    FLOOR_P = 0.0002; FLOOR_N = -0.0001
    for sym in ("BTCUSDT", "ETHUSDT", "SOLUSDT"):
        files = sorted(glob.glob(os.path.join(fdir, sym, "*.zip")))
        rows = []
        for fn in files:
            with zipfile.ZipFile(fn) as z:
                for nm in z.namelist():
                    rd = csv.reader(io.TextIOWrapper(z.open(nm), encoding="utf-8")); hdr = next(rd)
                    ri = len(hdr) - 1
                    for i, h in enumerate(hdr):
                        if "rate" in h.lower(): ri = i
                    for row in rd:
                        try: rows.append((int(row[0]) / 1000.0, float(row[ri])))
                        except Exception: pass
        rows.sort()
        pos = []; neg = []
        for i in range(270, len(rows)):
            w = sorted(r for _, r in rows[i - 270:i])
            q_hi = w[int(0.975 * len(w))]; q_lo = w[int(0.025 * len(w))]
            t, f = rows[i]
            if t < START: continue
            if f >= max(FLOOR_P, q_hi): pos.append(t)
            if f <= min(FLOOR_N, q_lo): neg.append(t)
        print("== Funding relativ %s (ab 2019/Start; pos: f >= max(2 bp, P97,5 der letzten 90 Tage); neg: f <= min(-1 bp, P2,5))" % sym)
        for label, lst in (("positiv", pos), ("negativ", neg)):
            ep = episodes(lst, 72 * 3600)
            per = ", ".join("%d:%d" % (y, len([t for t in ep if yr(t) == y])) for y in range(2020, 2027))
            sts = ", ".join("%s %d" % (NAMES[s], len([t for t in ep if st.get(int(t) // 86400) == s])) for s in (0, 1, 2))
            print("   %s: Ereignisse %d, Episoden %d (je Jahr %s); je Zustand: %s" % (label, len(lst), len(ep), per, sts))

def weekend(hc, st):
    print("== Wochenende XBT (Fr 21:00 bis So 21:00 UTC), ab 2019-01-01")
    def P(T):
        return hc.get(int(T) // 3600 - 1)
    d0 = date(2014, 1, 3)   # ein Freitag
    rs = []
    d = d0
    while True:
        T1 = datetime(d.year, d.month, d.day, 21, tzinfo=timezone.utc).timestamp()
        T2 = T1 + 2 * 86400
        if T2 >= CUT: break
        a, b = P(T1), P(T2)
        if a and b: rs.append((T2, math.log(b / a)))
        d = date.fromordinal(d.toordinal() + 7)
    res = {k: [0, 0, 0, defaultdict(int)] for k in (1.0, 1.5, 2.0)}
    tot = 0
    for i in range(52, len(rs)):
        T2, R = rs[i]
        if T2 < START: continue
        tot += 1
        s = sd([x for _, x in rs[i - 52:i]])
        for k in res:
            if abs(R) >= k * s:
                res[k][0] += 1
                res[k][1 if R > 0 else 2] += 1
                res[k][3][st.get(int(T2) // 86400, -1)] += 1
    print("   Wochenenden im Fenster: %d" % tot)
    for k, v in res.items():
        print("   k=%.1f: Ereignisse %d (Aufwaerts %d, Abwaerts %d); je Zustand: %s" % (k, v[0], v[1], v[2], ", ".join("%s %d" % (NAMES[s], v[3].get(s, 0)) for s in (0, 1, 2))))

if __name__ == "__main__":
    agg, fdir = sys.argv[2], sys.argv[3]
    st, hc = k4(agg)
    fundrel(fdir, st)
    weekend(hc, st)
