"""Statistik (RUNDE2_SPEC_v1 R6): Moving-Block-Bootstrap ueber Handelstage, BH-FDR, Placebo-Vergleich."""
import numpy as np

Z_SUM = 3.3393          # z(1-alpha') + z(1-beta), wie BAU_SPEC v2 V2.0
BLOCK = 20              # Mindestblocklaenge (Spec R6); Nachtrag N1: Blocklaenge = max(BLOCK, 4*H), siehe block_for
NBOOT = 5000
NBOOT_GATE = 2000
SEED = 20261024
DELTA_MIN = 2.0         # bp je Tag, Netto (A-R4)
Q_FDR = 0.05


def block_for(H):
    """Nachtrag N1 (Simulation auf synthetischen Daten, vor jeder Preisansicht): ueberlappende Kohorten mit Haltedauer H erzeugen eine
    MA(H-1)-Struktur. Gemessen (i.i.d., T = 1900, H = 21, 1200 Wiederholungen): Block 20 -> SE-Verhaeltnis ca. 0,82, Block 42 -> 0,87
    (Fehlalarm 6,8 %), Block 84 -> 0,915 (Fehlalarm 6,1 %). Regel: max(20, 4*H). Restunterschaetzung ca. 8 % bleibt (Bootstrap-Bias)."""
    return max(BLOCK, 4 * int(H))


def block_means(segments, block=BLOCK):
    """Blockmittel aller zulaessigen Blockstarts; Bloecke liegen komplett in einem Segment. segments: Liste von 1D-Arrays."""
    bms = []
    total = 0
    for seg in segments:
        seg = np.asarray(seg, dtype=float)
        total += len(seg)
        if len(seg) >= block:
            cs = np.concatenate([[0.0], np.cumsum(seg)])
            bms.append((cs[block:] - cs[:-block]) / block)
    if not bms:
        raise ValueError("kein Segment lang genug fuer die Blocklaenge")
    return np.concatenate(bms), total


def boot_mean(segments, block=BLOCK, ndraw=NBOOT, seed=SEED):
    """Bootstrap-Verteilung des Mittels. Gibt (boot_means, observed_mean, n_total) zurueck."""
    bm, total = block_means(segments, block)
    nb = max(1, total // block)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(bm), size=(ndraw, nb))
    boots = bm[idx].mean(axis=1)
    obs = float(np.mean(np.concatenate([np.asarray(s, dtype=float) for s in segments])))
    return boots, obs, total


def summarize(segments, block=BLOCK, ndraw=NBOOT, seed=SEED, delta_min=DELTA_MIN):
    boots, obs, total = boot_mean(segments, block, ndraw, seed)
    se = float(np.std(boots, ddof=1))
    lcb = float(np.quantile(boots, 0.05))
    p = float(np.mean((boots - obs) >= obs))        # Nullverteilung = Bootstrap zentriert um 0; einseitig "Mittel > 0"
    mde = Z_SUM * se
    return {"block": int(block), "n_days": int(total), "mean_bp_day": obs, "se_bp_day": se, "lcb95_bp_day": lcb, "p": p,
            "mde_bp_day": mde, "c1_power": bool(mde <= delta_min)}


def bh_reject(pvals, q=Q_FDR):
    """Benjamini-Hochberg: Liste von Booleans (Ablehnung der Nullhypothese) in Eingabereihenfolge."""
    m = len(pvals)
    order = np.argsort(pvals, kind="stable")
    thresh = -1
    for rank, i in enumerate(order, start=1):
        if pvals[i] <= rank / m * q:
            thresh = rank
    rej = [False] * m
    for rank, i in enumerate(order, start=1):
        if rank <= thresh:
            rej[i] = True
    return rej
