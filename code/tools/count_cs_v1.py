# count_cs_v1.py - Zaehlung/Streuung fuer Querschnitts-Kandidaten (CS_MOM, RESREV) im Krypto-Pool, OHNE Vorzeichen-Statistik der Strategien
# Aufruf: python count_cs_v1.py <agg-Ordner> [Paare...]   (Standard: K4P-Pool 39 Paare + XBT + ETH)
# Ausgabe: Verfuegbarkeit je Woche, Nullwelt-Streuung des Long/Short-Quintil-Portfolios (Zufallsranking), MDE je Woche und annualisiert.
import sys, os, math, random
MINA = int(os.environ.get("MINA", "10"))
from collections import defaultdict
import count_events_v2 as v2

POOL = ["XBT", "ETH", "SOL", "XRP", "XDG", "ADA", "LTC", "DOT", "LINK", "XMR", "ZEC", "XLM", "BCH", "ATOM", "SUI", "ALGO", "PEPE",
        "AVAX", "TAO", "FIL", "UNI", "TRX", "AAVE", "XTZ", "FET", "NEAR", "SHIB", "ETC", "DASH", "MANA", "CRV", "ICP",
        "FARTCOIN", "INJ", "PENGU", "ONDO", "SEI", "TIA", "KAS", "FLOW", "TRUMP"]
START_DAY = int(v2.START // 86400)

def weekly_closes(path):
    ts, op, hi, lo, cl = v2.load(path)
    last = {}
    for t, c in zip(ts, cl):
        last[t // 86400] = c            # letzter Schluss je UTC-Tag
    # Woche = Montag 00:00 UTC (Tag 4 = Montag, da 1970-01-01 ein Donnerstag war)
    wk = {}
    for d in sorted(last):
        w = (d + 3) // 7                # Wochenindex, Woche beginnt Montag
        wk[w] = last[d]                 # letzter Tag der Woche
    return wk

def main(agg, pairs, nsim=200, seed=7):
    rnd = random.Random(seed)
    closes = {}
    for p in pairs:
        path = os.path.join(agg, p + "USD_1m.csv")
        if os.path.exists(path):
            closes[p] = weekly_closes(path)
    w0 = (START_DAY + 3) // 7; w1 = (int(v2.CUT // 86400) + 3) // 7
    weeks = list(range(w0, w1))
    rets = {}                           # (p,w) -> log-Rendite der Woche w (Schluss w / Schluss w-1)
    for p, c in closes.items():
        for w in weeks:
            if w in c and (w - 1) in c and c[w] > 0 and c[w - 1] > 0:
                rets[(p, w)] = math.log(c[w] / c[w - 1])
    avail = []
    for w in weeks:
        ps = [p for p in closes if (p, w) in rets and (p, w - 1) in rets and (p, w - 2) in rets]
        avail.append(ps)
    n_by_year = defaultdict(list)
    for w, ps in zip(weeks, avail):
        y = 1970 + (w * 7 * 86400) // 31556952
        n_by_year[y].append(len(ps))
    print("Paare geladen: %d; Wochen im Fenster: %d" % (len(closes), len(weeks)))
    print("verfuegbare Assets je Woche (Mittel je Jahr): %s" % ", ".join("%d:%.1f" % (y, sum(v) / len(v)) for y, v in sorted(n_by_year.items())))
    ok = [i for i, ps in enumerate(avail) if len(ps) >= MINA]
    print("Wochen mit >= %d Assets: %d; Wochen mit >= 20: %d" % (MINA, len(ok), sum(1 for ps in avail if len(ps) >= 20)))
    if not ok:
        print("keine Woche mit genug Assets"); return
    # Querschnittsstreuung der Wochenrenditen (zentriert) und Nullwelt des Long/Short-Quintil-Portfolios
    disp = []; sd_ls = []
    for i in ok:
        ps = avail[i]; w = weeks[i]
        r = [rets[(p, w)] for p in ps]
        m = sum(r) / len(r)
        disp.append(math.sqrt(sum((x - m) ** 2 for x in r) / (len(r) - 1)))
    k_ls = []
    for _ in range(nsim):
        s = []
        for i in ok:
            ps = avail[i][:]; w = weeks[i]
            rnd.shuffle(ps)
            q = max(2, len(ps) // 5)
            top = sum(rets[(p, w)] for p in ps[:q]) / q
            bot = sum(rets[(p, w)] for p in ps[-q:]) / q
            s.append(top - bot)
        k_ls.append(s)
    # Streuung je Woche des Zufalls-L/S: Standardabweichung ueber Wochen und Simulationen (Mittel 0 erwartet)
    allv = [x for s in k_ls for x in s]
    m = sum(allv) / len(allv)
    sd = math.sqrt(sum((x - m) ** 2 for x in allv) / (len(allv) - 1))
    n = len(ok)
    mde_w = 3.649 * sd / math.sqrt(n)
    print("Querschnittsstreuung der Wochenrendite (Median): %.1f %%" % (100 * sorted(disp)[len(disp) // 2]))
    print("Zufalls-L/S-Quintil (Nullwelt): Streuung je Woche %.1f %%; n = %d Wochen" % (100 * sd, n))
    print("MDE je Woche (alpha 0,0025, Power 0,8, ohne Kosten): %.0f bp; annualisiert (x52): %.0f %%; SR-MDE ≈ %.2f" % (1e4 * mde_w, 100 * 52 * mde_w, (mde_w * 52) / (sd * math.sqrt(52))))
    print("Hinweis: Pool = heute handelbare Coins mit Perp und >= 150 MB T&S (Survivorship: ausgeschiedene Coins fehlen); Kosten Rundreise 26 bp je Position nicht abgezogen.")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:] if len(sys.argv) > 2 else POOL)
