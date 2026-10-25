# count_events_v3.py - E2c: Zaehlung der K4P-Replikation (Alt-Coins) nach Spec-Entwurf Runde 3
# Aufruf (im Ordner tools, dort liegt count_events_v2.py):  python count_events_v3.py <agg-Ordner> [Paare...]
# Ohne Paarliste: alle Paare der festen ex-ante-Liste unten, die als <NAME>USD_1m.csv im agg-Ordner liegen.
# Auslöser: Rueckgang vom 15-Min-Hoch um >= theta_t, theta_t = max(3 %, 6 * sigma15_t), sigma15_t = Streuung der
# 15-Min-Renditen der letzten 30 Tage (nur Daten bis Vortag). Einstiegs-/Ausstiegsregel wie K4 (Spec §7).
# Gibt NUR Zaehlungen und Betrags-/Streuungskennzahlen aus (keine Vorzeichen-Statistik der Nachereignis-Rendite).
import sys, os, math
from bisect import bisect_left
from collections import deque, defaultdict
from datetime import datetime, timezone
import count_events_v2 as v2

START = v2.START
NAMES = v2.NAMES
# feste Liste (ex ante, F6/F7-Schnitt, siehe D39); XBT/ETH sind K4 selbst, nicht Teil des Replikationspools
POOL = ["SOL", "XRP", "XDG", "ADA", "LTC", "DOT", "LINK", "XMR", "ZEC", "XLM", "BCH", "ATOM", "SUI", "ALGO", "PEPE",
        "AVAX", "TAO", "FIL", "UNI", "TRX", "AAVE", "XTZ", "FET", "NEAR", "SHIB", "ETC", "DASH", "MANA", "CRV", "ICP",
        "FARTCOIN", "INJ", "PENGU", "ONDO", "SEI", "TIA", "KAS", "FLOW", "TRUMP"]

def sigma15_by_day(ts, cl):
    """Tageswerte (Summe r^2, Anzahl) der 15-Min-Log-Renditen, danach trailing 30 Tage ohne den laufenden Tag."""
    sq = defaultdict(float); cnt = defaultdict(int)
    prev_key = None; prev_c = None; cur_key = None; cur_c = None
    for t, c in zip(ts, cl):
        k = t // 900
        if cur_key is None:
            cur_key, cur_c = k, c; continue
        if k != cur_key:
            if prev_key is not None and cur_key == prev_key + 1 and prev_c > 0 and cur_c > 0:
                r = max(-0.15, min(0.15, math.log(cur_c / prev_c)))
                d = (cur_key * 900) // 86400
                sq[d] += r * r; cnt[d] += 1
            prev_key, prev_c = cur_key, cur_c
            cur_key, cur_c = k, c
        else:
            cur_c = c
    sig = {}
    days = sorted(sq)
    if not days: return sig
    for d in range(days[0] + 30, days[-1] + 2):
        s = 0.0; n = 0; nd = 0
        for x in range(d - 30, d):
            if x in cnt:
                s += sq[x]; n += cnt[x]; nd += 1
        if nd >= 20 and n > 0:
            sig[d] = math.sqrt(s / n)
    return sig

def sim_k4g(data, st, sig, floor=0.03, mult=6.0):
    ts, op, hi, lo, cl = data
    n = len(ts)
    WIN = 15 * 60
    dq = deque(); prev_close = None; blocked = 0
    out = []; glitch = 0; notheta = 0
    i = 0
    while i < n:
        t = ts[i]; h = hi[i]; l = lo[i]
        if l <= 0:
            glitch += 1; i += 1; continue
        while dq and dq[0][0] < t - WIN + 60: dq.popleft()
        while dq and dq[-1][1] <= h: dq.pop()
        dq.append((t, h))
        if t >= START and t >= blocked:
            day = t // 86400
            s15 = sig.get(day)
            if s15 is None:
                notheta += 1
            else:
                theta = max(floor, mult * s15)
                if l / dq[0][1] - 1.0 <= -theta:
                    tau = t
                    sday = st.get(day)
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
                    out.append((tau, sday, r, theta))
                    if r is None: blocked = tau + 3600
        i += 1
    return out, glitch, notheta

def iso(t): return datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%d")

def main(agg, pairs):
    st, _hc = v2.k4(agg)      # K4-Referenz XBT/ETH mit bereinigten Daten (druckt Zaehlungen je Paar/Zustand)
    for nm in ("XBTUSD", "ETHUSD"):
        print("Bereinigung %s: Zeilen, entfernt, laengste Serie = %s" % (nm, v2.FLAGGED.get(os.path.join(agg, nm + "_1m.csv"))))
    xbt = v2.load(os.path.join(agg, "XBTUSD_1m.csv"))
    # K4-Referenzepisoden (XBT+ETH, theta 3 %) fuer die Ueberlappungsangabe
    ref = []
    for nm in ("XBTUSD", "ETHUSD"):
        d = xbt if nm == "XBTUSD" else v2.load(os.path.join(agg, nm + "_1m.csv"))
        ref += [e[0] for e in v2.sim_k4(nm, d, st) if e[2] is not None]
    ref_ep = v2.episodes(ref, 86400)
    print("K4-Referenz (XBT+ETH): %d Episoden" % len(ref_ep))
    allev = []   # (tau, state, r, pair)
    for p in pairs:
        path = os.path.join(agg, p + "USD_1m.csv")
        if not os.path.exists(path):
            print("== %s: Datei fehlt" % p); continue
        data = v2.load(path)
        ts = data[0]
        if len(ts) < 1000:
            print("== %s: zu wenig Daten (%d Minuten)" % (p, len(ts))); continue
        sig = sigma15_by_day(ts, data[4])
        ev, gl, nt = sim_k4g(data, st, sig)
        ent = [e for e in ev if e[2] is not None]
        ep = v2.episodes([e[0] for e in ent], 86400)
        r = [e[2] for e in ent]
        th = [e[3] for e in ent]
        line = "== %s: Daten %s..%s, Minuten %d, Auslöser %d, mit Einstieg %d, Episoden %d, Zustaende %s" % (
            p, iso(ts[0]), iso(ts[-1]), len(ts), len(ev), len(ent), len(ep),
            "/".join(str(len(v2.episodes([e[0] for e in ent if e[1] == s], 86400))) for s in (0, 1, 2)))
        print(line)
        if len(r) > 1:
            fl = v2.FLAGGED.get(path, (0, 0, 0))
            print("   theta Median %.1f %%, Streuung 4-h (zentriert) %.0f bp, Mittel |r| %.0f bp, entfernte Zeilen %d von %d (laengste Serie %d), ohne sigma15 %d" % (
                100 * sorted(th)[len(th) // 2], v2.sd(r), sum(abs(x) for x in r) / len(r), fl[1], fl[0], fl[2], nt))
        allev += [(e[0], e[1], e[2], p) for e in ent]
    if not allev:
        print("keine Ereignisse"); return
    ep = v2.episodes([e[0] for e in allev], 86400)
    print("== K4P vereinigt (alle Paare): Einstiege %d, Episoden (24-h-Cluster ueber alle Paare) %d" % (len(allev), len(ep)))
    print("   je Zustand: %s" % ", ".join("%s %d" % (NAMES[s], len(v2.episodes([e[0] for e in allev if e[1] == s], 86400))) for s in (0, 1, 2)))
    print("   je Jahr: %s" % ", ".join("%d:%d" % (y, len([t for t in ep if v2.yr(t) == y])) for y in range(2019, 2027)))
    # Ueberlappung mit K4-Episoden (+-24 h)
    refs = sorted(ref_ep)
    def near(t):
        k = bisect_left(refs, t)
        for x in refs[max(0, k - 1):k + 1]:
            if abs(x - t) < 86400: return True
        return False
    ov = sum(1 for t in ep if near(t))
    print("   davon innerhalb +-24 h einer K4-Episode (Abhaengigkeit!): %d, ausserhalb: %d" % (ov, len(ep) - ov))
    # Einstiege je Paar-Tag-Cluster: wie viele Paare gleichzeitig (Abhaengigkeit innerhalb des Pools)
    byday = defaultdict(set)
    for t, s, r, p in allev:
        byday[int(t) // 86400].add(p)
    multi = sum(1 for d, v in byday.items() if len(v) >= 3)
    print("   Tage mit Einstieg: %d, davon >= 3 Paare am selben Tag: %d" % (len(byday), multi))
    r = [e[2] for e in allev]
    print("   Streuung 4-h (alle Einstiege, zentriert) %.0f bp, Mittel |r| %.0f bp" % (v2.sd(r), sum(abs(x) for x in r) / len(r)))

if __name__ == "__main__":
    pairs = sys.argv[2:] if len(sys.argv) > 2 else POOL
    main(sys.argv[1], pairs)
