# carry_train_v1.py - CARRY-HOLD Discovery NUR im TRAININGSFENSTER 2019-09-08 .. 2023-12-31 (Testfenster 2024-01..2026-06 wird NICHT gelesen: harte Grenze im Code).
# Strategie: long Spot, short Perp (gleicher Notional) BTCUSDT/ETHUSDT (Binance-Proxy). Taegliche Entscheidung 00:00 UTC auf Basis des
# nachlaufenden 7-Tage-Fundings (annualisiert), Wirkung ab dem Folgetag. Einstieg wenn F7 > E, Ausstieg wenn F7 < X (X < E).
# P&L pro Tag in Position: Funding des Tages (Summe 8h-Raten) - Aenderung der Basis (ln perp - ln spot, Tagesschlusskurse); Kosten je Phase:
# Spot-Bein 2 x spot_bp + Perp-Bein 2 x perp_bp. Kostenvarianten: basis (maker-Spot 40 bp/Seite, Perp 5 bp/Seite), stress (taker-Spot 80 bp/Seite, Perp 5).
# Aufruf: python -u carry_train_v1.py <binance-klines> <funding-binance>
import sys, os, io, csv, zipfile, math
from datetime import date, datetime, timedelta, timezone
A = date(2019, 9, 8); B = date(2023, 12, 31)           # Trainingsfenster, hart
def months():
    y, m = 2019, 9
    while (y, m) <= (2023, 12):
        yield "%04d-%02d" % (y, m); m += 1
        if m == 13: y += 1; m = 1
def load(p):
    out = {}; z = zipfile.ZipFile(p)
    for n in z.namelist():
        for row in csv.reader(io.TextIOWrapper(z.open(n), "utf-8")):
            try: t = int(row[0]); c = float(row[4])
            except ValueError: continue
            if t > 10**14: t //= 1000
            out[datetime.fromtimestamp(t / 1000, timezone.utc).date()] = c
    return out
def run(spot, perp, fund, E, X, cost_bp, always=False):
    days = [A + timedelta(days=i) for i in range((B - A).days + 1)]
    pos = False; phases = 0; gross_f = 0.0; basis_pl = 0.0; cost = 0.0; inpos = 0; week = {}
    for i in range(7, len(days) - 1):
        d = days[i]
        f7 = sum(fund.get(d - timedelta(days=k), 0.0) for k in range(1, 8)) / 7 * 365      # annualisiert, Information bis d-1
        want = True if always else (f7 > E if not pos else f7 >= X)
        if want and not pos: pos = True; phases += 1; cost += cost_bp / 2; week_c = cost_bp / 2
        elif (not want) and pos: pos = False; cost += cost_bp / 2
        if pos and d in spot and d in perp and (d - timedelta(days=1)) in spot and (d - timedelta(days=1)) in perp:
            p = d - timedelta(days=1)
            f = fund.get(d, 0.0) * 1e4
            b = ((math.log(perp[d]) - math.log(spot[d])) - (math.log(perp[p]) - math.log(spot[p]))) * 1e4
            gross_f += f; basis_pl += -b; inpos += 1
    if pos: cost += cost_bp / 2
    return phases, inpos, gross_f, basis_pl, cost
def main(kd, fd):
    for s in ["BTCUSDT", "ETHUSDT"]:
        spot = {}; perp = {}
        for mo in months():
            for kind, store in (("spot", spot), ("um", perp)):
                fp = os.path.join(kd, "%s_%s_%s.zip" % (kind, s, mo))
                if os.path.exists(fp) and os.path.getsize(fp) > 0: store.update(load(fp))
        fund = {}
        with open(os.path.join(fd, s + ".csv"), encoding="utf-8") as f:
            for r in csv.DictReader(f):
                d = datetime.fromtimestamp(int(r["fundingTimeMs"]) / 1000, timezone.utc).date()
                if d <= B: fund[d] = fund.get(d, 0.0) + float(r["fundingRate"])
        wk = (B - A).days / 7.0
        print("== %s Training (%.0f Wochen) ==" % (s, wk))
        print("Regel | Kosten | Phasen | Tage in Pos | Funding bp | Basis bp | Kosten bp | Netto bp gesamt | Netto bp je Kalenderwoche | Netto bp je Woche in Pos")
        for name, E, X, always in [("immer-an", 0, 0, True)] + [("E%.0f%%/X%.0f%%" % (e * 100, x * 100), e, x, False) for e in (0.05, 0.10, 0.15) for x in (0.0, 0.03, 0.05) if x < e]:
            for cn, cb in (("basis", 2 * 40 + 2 * 5), ("stress", 2 * 80 + 2 * 5)):
                ph, ip, gf, bp, c = run(spot, perp, fund, E, X, cb, always)
                net = gf + bp - c
                print("%s | %s | %d | %d | %.0f | %.0f | %.0f | %.0f | %.2f | %s" % (name, cn, ph, ip, gf, bp, c, net, net / wk, ("%.2f" % (net / (ip / 7.0))) if ip else "-"))
if __name__ == "__main__": main(sys.argv[1], sys.argv[2])
