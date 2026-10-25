# carry_null_v1.py - CARRY-HOLD Nullwelt-Kalibrierung der Standardfehler-Schaetzer (reine Simulation, KEINE Marktdaten).
# Nullwelt: Gaussian-Copula-Prozess mit der im TRAINING gemessenen ACF (carry_acf_v1.py, Lags 1..8, danach linear auf 0 bis Lag 12),
# t(5)-Randverteilung, Mittelwert 0, sigma = Wochen-sigma des Testfensters (16.4 bp, nur zentrierte Streuung bekannt), T = 130 Wochen.
# Statistik 1 "immer-an": Mittel aller T Wochen. Statistik 2 "Phasen": Mittel ueber zufaellige zusammenhaengende Phasen (~54 % der Wochen, Phasenlaenge 8..30).
# Schaetzer: iid-t, Newey-West (Bartlett, 8 Lags), Block-Bootstrap (Bloecke 4, 8, 13; B=399). Ausgabe: Fehlpass-Rate z > 2.807 (alpha_i 0.25 %), sd(z), SE-Faktor gegen iid.
# Aufruf: python -u carry_null_v1.py <anzahl_welten> <seed>
import sys, math
import numpy as np
from statistics import NormalDist
Z = NormalDist().inv_cdf(1 - 0.0025)
ACFS = {"BTC 2022-23": [0.48, 0.31, 0.20, 0.16, 0.06, 0.07, 0.05, 0.01], "ETH 2022-23": [0.50, 0.31, 0.23, 0.16, 0.09, 0.05, 0.07, 0.15],
        "Stress voll BTC": [0.69, 0.48, 0.43, 0.40, 0.40, 0.32, 0.25, 0.24]}
def acf_full(a8, L=12):
    a = list(a8); last = a[-1]
    for k in range(9, L + 1): a.append(last * (L + 1 - k) / (L + 1 - 8))
    return np.array([1.0] + a + [0.0] * 200)
def chol_for(a8, T):
    r = acf_full(a8)
    for shrink in (1.0, 0.9, 0.8, 0.6, 0.4):
        rr = np.array([1.0] + [x * shrink for x in r[1:]])
        M = np.array([[rr[abs(i - j)] for j in range(T)] for i in range(T)])
        try: return np.linalg.cholesky(M)
        except np.linalg.LinAlgError: continue
    raise SystemExit("keine PD-Matrix")
def t5_scaled(g, rng, sigma):
    # Gaussian-Copula: g ist je Woche N(0,1); Randverteilung t(5), auf Varianz 1 normiert (Var t5 = 5/3), dann sigma. KEINE Zentrierung je Welt (Mittelwert bleibt zufaellig, Erwartung 0).
    from scipy import stats
    u = stats.norm.cdf(g)
    return stats.t.ppf(u, 5) / math.sqrt(5.0 / 3.0) * sigma
def se_nw(x, L=8):
    n = len(x); e = x - x.mean(); v = (e * e).sum() / n
    for k in range(1, L + 1): v += 2 * (1 - k / (L + 1)) * (e[k:] * e[:-k]).sum() / n
    return math.sqrt(max(v, 1e-12) / n)
def se_boot(x, L, rng, B=399):
    n = len(x); nb = int(math.ceil(n / L)); starts = rng.integers(0, n - L + 1, size=(B, nb))
    idx = (starts[:, :, None] + np.arange(L)[None, None, :]).reshape(B, -1)[:, :n]
    return x[idx].mean(axis=1).std(ddof=1)
def phases(T, rng):
    m = np.zeros(T, bool); target = int(0.54 * T); n = 0
    while n < target:
        ln = int(rng.integers(8, 31)); s = int(rng.integers(0, T - ln + 1)); n -= m[s:s + ln].sum(); m[s:s + ln] = True; n += m[s:s + ln].sum()
    return m
def main(W, seed):
    rng = np.random.default_rng(seed); T = 130; sigma = 16.4
    print("Nullwelten %d, Seed %d, T=%d, sigma=%.1f bp; alpha_i 0.25 %% einseitig (z=%.3f)" % (W, seed, T, sigma, Z))
    print("ACF-Satz | Statistik | Schaetzer | Fehlpass z>2.807 | Fehlpass z>2.468 (=1.5*1.645, HINWEIS-Kriterium) | sd(z) | SE-Faktor (sd Mittel / iid-SE)")
    for name, a8 in ACFS.items():
        Lc = chol_for(a8, T)
        res = {}
        for stat in ("immer-an", "Phasen"):
            zs = {"iid": [], "NW8": [], "B4": [], "B8": [], "B13": []}; means = []; iid_se = []
            for w in range(W):
                g = Lc @ rng.standard_normal(T); x = t5_scaled(g, rng, sigma)
                if stat == "Phasen": x = x[phases(T, rng)]
                n = len(x); mu = x.mean(); means.append(mu); s_iid = x.std(ddof=1) / math.sqrt(n); iid_se.append(s_iid)
                zs["iid"].append(mu / s_iid); zs["NW8"].append(mu / se_nw(x))
                for L in (4, 8, 13): zs["B%d" % L].append(mu / se_boot(x, L, rng))
            fac = np.std(means, ddof=1) / np.mean(iid_se)
            for k, v in zs.items():
                v = np.array(v); print("%s | %s | %s | %.2f %% (%d/%d) | %.2f %% (%d/%d) | %.2f | %.2f" % (name, stat, k, 100 * (v > Z).mean(), (v > Z).sum(), W, 100 * (v > 2.4675).mean(), (v > 2.4675).sum(), W, v.std(ddof=1), fac), flush=True)
if __name__ == "__main__": main(int(sys.argv[1]), int(sys.argv[2]))
