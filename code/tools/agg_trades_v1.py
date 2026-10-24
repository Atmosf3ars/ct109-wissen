# agg_trades_v1.py - Kraken Time & Sales -> 1-Minuten-Aggregate (nur Daten < 2026-07-01 00:00:00 UTC)
# Aufruf: python agg_trades_v1.py <csv-Pfad> <Ausgabe-Ordner>
# Liest zeilenweise, schreibt nur Aggregate, gibt eine Zusammenfassung (nur Kennzahlen) aus.
import sys, os, json
from datetime import datetime, timezone

CUT = datetime(2026, 7, 1, tzinfo=timezone.utc).timestamp()  # Zeilen mit ts >= CUT werden nie verwendet

def iso(x):
    return datetime.fromtimestamp(x, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def main(path, outdir):
    os.makedirs(outdir, exist_ok=True)
    name = os.path.splitext(os.path.basename(path))[0]
    outp = os.path.join(outdir, name + "_1m.csv")
    rows = used = disorder = bad = nonpos = 0
    seen_cut = 0
    first_ts = last_ts = None
    pmin = None; pmax = None
    tick = {}
    prev_p = None
    cur = None  # [key, o, h, l, c, vol, vb, vs, vm, n, notional]
    nmin = 0
    with open(path, "r", buffering=1 << 20, newline="") as f, open(outp, "w", buffering=1 << 20, newline="") as out:
        out.write("minute_utc_epoch,open,high,low,close,vol,vol_b,vol_s,vol_m,n,notional\n")
        f.readline()  # Kopfzeile
        for line in f:
            rows += 1
            try:
                a = line.split(",")
                ts = float(a[0]); p = float(a[1]); v = float(a[2]); t = a[3]; ot = a[4]
            except Exception:
                bad += 1
                continue
            if ts >= CUT:
                seen_cut += 1
                break  # chronologisch: ab hier nichts mehr lesen
            if p <= 0 or v <= 0:
                nonpos += 1
                continue
            used += 1
            if first_ts is None:
                first_ts = ts
            if last_ts is not None and ts < last_ts:
                disorder += 1
            last_ts = ts
            if pmin is None or p < pmin: pmin = p
            if pmax is None or p > pmax: pmax = p
            if prev_p is not None and p != prev_p:
                k = (t, ot, "up" if p > prev_p else "dn")
                tick[k] = tick.get(k, 0) + 1
            prev_p = p
            key = int(ts // 60)
            if cur is None or key > cur[0]:
                if cur is not None:
                    out.write("%d,%r,%r,%r,%r,%r,%r,%r,%r,%d,%r\n" % (cur[0] * 60, cur[1], cur[2], cur[3], cur[4], cur[5], cur[6], cur[7], cur[8], cur[9], cur[10]))
                    nmin += 1
                cur = [key, p, p, p, p, 0.0, 0.0, 0.0, 0.0, 0, 0.0]
            if p > cur[2]: cur[2] = p
            if p < cur[3]: cur[3] = p
            cur[4] = p
            cur[5] += v
            if t == "b": cur[6] += v
            elif t == "s": cur[7] += v
            if ot == "m": cur[8] += v
            cur[9] += 1
            cur[10] += p * v
            if rows % 20000000 == 0:
                print("... %d Zeilen" % rows, flush=True)
        if cur is not None:
            out.write("%d,%r,%r,%r,%r,%r,%r,%r,%r,%d,%r\n" % (cur[0] * 60, cur[1], cur[2], cur[3], cur[4], cur[5], cur[6], cur[7], cur[8], cur[9], cur[10]))
            nmin += 1
    summ = {
        "datei": name, "zeilen_gelesen": rows, "zeilen_verwendet": used, "minuten_mit_handel": nmin,
        "erste_zeit": iso(first_ts) if first_ts else None, "letzte_verwendete_zeit": iso(last_ts) if last_ts else None,
        "schnitt_erreicht": seen_cut, "unordnung": disorder, "unlesbar": bad, "preis_oder_menge_nichtpositiv": nonpos,
        "preis_min": pmin, "preis_max": pmax,
        "ticktest_typ_ordertyp_richtung": {"%s/%s/%s" % k: v for k, v in sorted(tick.items())},
    }
    print("ZUSAMMENFASSUNG " + json.dumps(summ, ensure_ascii=False))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
