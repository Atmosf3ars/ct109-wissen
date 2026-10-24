"""Universumsliste (RUNDE2_SPEC_v1 R1): aktuelle S&P-500-Mitglieder aus dem Wikipedia-Artikel.

Die abgerufene Rohdatei wird gehasht; der Hash gehoert in 01_STATUS.md, BEVOR der erste Preis abgerufen wird.
Es werden keine Preise abgerufen und keine Preise gelesen.
"""
import html.parser
import re
import urllib.request

WIKI_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
MAX_STOCKS = 495
UA = "ct109-lf2/0.1 (research; contact: owner)"
SYMBOL_OK = re.compile(r"^[A-Z][A-Z0-9]{0,5}([.\-][A-Z])?$")


class _ConstituentsParser(html.parser.HTMLParser):
    """Liest die erste Spalte (Symbol) der ersten Tabelle mit id="constituents"."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_table = False
        self.depth = 0
        self.in_tr = False
        self.td_index = -1
        self.in_first_td = False
        self.cur = []
        self.symbols = []
        self.done = False

    def handle_starttag(self, tag, attrs):
        if self.done:
            return
        a = dict(attrs)
        if tag == "table":
            if not self.in_table and a.get("id") == "constituents":
                self.in_table = True
                self.depth = 1
            elif self.in_table:
                self.depth += 1
        elif self.in_table and self.depth == 1:
            if tag == "tr":
                self.in_tr = True
                self.td_index = -1
            elif tag == "td" and self.in_tr:
                self.td_index += 1
                if self.td_index == 0:
                    self.in_first_td = True
                    self.cur = []

    def handle_endtag(self, tag):
        if self.done or not self.in_table:
            return
        if tag == "table":
            self.depth -= 1
            if self.depth == 0:
                self.done = True
                self.in_table = False
        elif self.depth == 1:
            if tag == "td" and self.in_first_td:
                self.in_first_td = False
                self.symbols.append("".join(self.cur).strip())
            elif tag == "tr":
                self.in_tr = False

    def handle_data(self, data):
        if self.in_first_td and not self.done:
            self.cur.append(data)


def parse_constituents(html_text):
    """Gibt die Symbole in Dokumentreihenfolge zurueck (roh, unverandert bis auf Leerraum)."""
    p = _ConstituentsParser()
    p.feed(html_text)
    return [s for s in p.symbols if s]


def to_tiingo(sym):
    """Wikipedia schreibt Klassen mit Punkt (BRK.B); Tiingo mit Bindestrich (BRK-B)."""
    return sym.replace(".", "-")


def build_universe(raw_symbols, max_stocks=MAX_STOCKS):
    """Aus der rohen Liste: Format pruefen, Duplikate zaehlen, alphabetisch sortieren, auf max_stocks kuerzen.
    Gibt (liste, bericht) zurueck. Keine Auswahl nach Preisen oder Renditen; Reihenfolge nur alphabetisch."""
    cleaned, bad, seen, dups = [], [], set(), 0
    for s in raw_symbols:
        t = to_tiingo(s.strip().upper())
        if not SYMBOL_OK.match(t.replace("-", ".")):
            bad.append(s)
            continue
        if t in seen:
            dups += 1
            continue
        seen.add(t)
        cleaned.append(t)
    cleaned.sort()
    cut = cleaned[max_stocks:]
    uni = cleaned[:max_stocks]
    return uni, {"raw": len(raw_symbols), "valid_unique": len(cleaned), "bad_format": bad, "duplicates": dups,
                 "used": len(uni), "cut_off": cut}


def fetch_html(url=WIKI_URL, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()
