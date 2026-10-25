# count_gs_v1.py - Zaehlung/Streuung GOLD-SILBER (GLD/SLV, Tageskerzen), OHNE Vorzeichen-/Autokorrelations-Statistik der Strategie
# Aufruf: python count_gs_v1.py <bars-ordner>
import sys, os, csv, math, hashlib
import numpy as np
from datetime import date
def load(folder, sym):
    d, o, c = [], [], []
    with open(os.path.join(folder, sym + ".csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            x = date.fromisoformat(r["date"])
            if x >= date(2026, 7, 1): continue
            d.append(x.toordinal()); o.append(float(r["open"])); c.append(float(r["close"]))
    return np.array(d), np.array(o), np.array(c)
def main(folder):
    print("Skript-SHA256 %s" % hashlib.sha256(open(__file__, "rb").read()).hexdigest()[:16])
    g = load(folder, "GLD"); s = load(folder, "SLV")
    common, ig, is_ = np.intersect1d(g[0], s[0], return_indices=True)
    cg = g[2][ig]; cs = s[2][is_]
    print("GLD: %d Tage (%s .. %s); SLV: %d Tage (%s .. %s); gemeinsame Tage %d" % (len(g[0]), date.fromordinal(int(g[0][0])), date.fromordinal(int(g[0][-1])), len(s[0]), date.fromordinal(int(s[0][0])), date.fromordinal(int(s[0][-1])), len(common)))
    gaps = int(np.sum(np.diff(common) > 5)); print("Luecken > 5 Kalendertage: %d" % gaps)
    rg = np.diff(np.log(cg)); rs = np.diff(np.log(cs))
    beta = float(np.cov(rs, rg)[0, 1] / np.var(rg, ddof=1)); corr = float(np.corrcoef(rs, rg)[0, 1])
    sp = rs - beta * rg
    print("Tagesrendite zentriert-Streuung GLD %.0f bp, SLV %.0f bp; gleichzeitige Korrelation %.2f; Beta SLV auf GLD %.2f; Spread-Streuung (SLV - Beta*GLD) %.0f bp je Tag" % (np.std(rg, ddof=1) * 1e4, np.std(rs, ddof=1) * 1e4, corr, beta, np.std(sp, ddof=1) * 1e4))
    n = len(sp)
    for lab, h in (("Tag", 1), ("Woche (5 Handelstage)", 5), ("Monat (21 Handelstage)", 21)):
        m = n // h; x = np.array([sp[i * h:(i + 1) * h].sum() for i in range(m)])
        sd = np.std(x, ddof=1) * 1e4
        print("Horizont %-24s: n = %d, Spread-Streuung %.0f bp, MDE80 (alpha 0,0025) = %.1f bp je Periode, %.1f %% p. a. (nur Spread)" % (lab, m, sd, 3.649 * sd / math.sqrt(m), 3.649 * sd / math.sqrt(m) * 252 / h / 100))
    T = n / 252.0
    print("Jahre: %.1f; SR_MDE = 3,34/sqrt(T) = %.2f" % (T, 3.34 / math.sqrt(T)))
    print("Kosten-Anhalt je Tag-Wechsel (4 ETF-Seiten x 1,5 bp [A]) = 6 bp; je Woche 6 bp je Wechsel")
main(sys.argv[1])
