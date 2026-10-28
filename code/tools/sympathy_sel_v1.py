# sympathy_sel_v1.py - SYMPATHY-REVERSION Phase 0: Auswahl-Datei (Tag x Symbol) fuer den Ganztags-5-Min-Abruf des festen Sektor-Universums.
# Aufruf: python sympathy_sel_v1.py <first5-Ordner> --out <sel.csv> [--from 2016-01-04] [--to 2019-12-31]
# Handelstage = Tage aus <first5-Ordner>\_done_days.txt (Entwicklungsfenster, schon vorhanden). KEIN Datenabruf, KEIN Ergebnis.
# Danach: python -u alpaca_day5_v1.py <sel.csv> --out <Ordner> --chunk 80   (Testfenster-Sperre ist dort eingebaut).
# Sektor-Universum VORAB FEST (ANNAHME, Zusammensetzung grob nach Gewichten 2016-2019 aus Allgemeinwissen, nicht aus Daten; Ueberlebens-Verzerrung moeglich):
import sys, os, csv

SECTORS = {
    "SMH": {"leaders": ["INTC", "NVDA", "TXN"], "followers": ["AMD", "MU", "AMAT", "LRCX", "KLAC", "ADI", "MCHP", "XLNX", "NXPI", "MXIM", "SWKS", "QCOM", "AVGO", "ON"]},
    "XLF": {"leaders": ["JPM", "BAC", "WFC"], "followers": ["C", "GS", "MS", "USB", "PNC", "SCHW", "AXP", "BK", "COF", "BLK", "MET", "PRU"]},
    "XLE": {"leaders": ["XOM", "CVX", "SLB"], "followers": ["COP", "EOG", "OXY", "PSX", "VLO", "MPC", "KMI", "WMB", "HAL", "PXD", "APC", "HES"]},
    "XLV": {"leaders": ["JNJ", "PFE", "UNH"], "followers": ["MRK", "ABT", "AMGN", "LLY", "BMY", "GILD", "MDT", "CELG", "BIIB", "ABBV"]},
    "XLK": {"leaders": ["AAPL", "MSFT", "CSCO"], "followers": ["ORCL", "IBM", "ADBE", "CRM", "ACN", "INTU", "CTSH", "HPQ", "PYPL", "EBAY"]},
}

def all_symbols():
    s = []
    for etf, d in SECTORS.items():
        for x in [etf] + d["leaders"] + d["followers"]:
            if x not in s: s.append(x)
    return s

def main(first5, out, dfrom="2016-01-04", dto="2019-12-31"):
    if dto >= "2020-01-01": sys.exit("Testfenster gesperrt (Phase 0 nur Entwicklungsfenster bis 2019-12-31).")
    p = os.path.join(first5, "_done_days.txt")
    days = sorted(set(x.strip() for x in open(p, encoding="utf-8") if x.strip()))
    days = [d for d in days if dfrom <= d <= dto]
    syms = all_symbols()
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["date", "symbol", "rank", "rv5"])
        for d in days:
            for k, s in enumerate(syms, 1): w.writerow([d, s, k, 0])
    print("Handelstage %d | Symbole %d (davon ETF %d) | Zeilen %d | Datei %s" % (len(days), len(syms), len(SECTORS), len(days) * len(syms), out))

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    def opt(k, d): return a[a.index(k) + 1] if k in a else d
    main(a[0], opt("--out", "sympathy_sel.csv"), opt("--from", "2016-01-04"), opt("--to", "2019-12-31"))
