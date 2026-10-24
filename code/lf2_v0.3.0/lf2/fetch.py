"""Preisabruf Tiingo End-of-Day (RUNDE2_SPEC_v1 R1/R8). Laeuft auf Andis PC.

- Token nur aus der Umgebungsvariable TIINGO_TOKEN, nie ausgeben, nie in URL (Header Authorization).
- Drosselung unter dem Limit (50 Anfragen/Stunde): Standard 75 s zwischen Anfragen.
- Wiederaufnehmbar: vorhandene, gueltige Dateien werden uebersprungen.
- Ausgabe nur Zaehler. Rohdaten bleiben im Zielordner (Lizenz: nur eigene Nutzung).
"""
import csv
import io
import json
import os
import time
import urllib.error
import urllib.request

from .util import sha256_bytes, sha256_file, json_hash, code_hash

BASE = "https://api.tiingo.com/tiingo/daily/%s/prices"
START, END = "2005-01-03", "2026-06-30"
REQUIRED = ("date", "open", "close", "volume", "adjopen", "adjclose")
FULL = ("date", "close", "high", "low", "open", "volume", "adjclose", "adjhigh", "adjlow", "adjopen",
        "adjvolume", "divcash", "splitfactor")
MIN_GAP_S = 75.0
MAX_BODY = 20_000_000


class FetchAbort(Exception):
    pass


def validate_csv(body):
    """Prueft Kopfzeile und dass Zeilen existieren und Datumswerte aufsteigend sind. Gibt (rows, first, last) zurueck."""
    text = body.decode("utf-8")
    rd = csv.reader(io.StringIO(text))
    try:
        head = [h.strip().lower() for h in next(rd)]
    except StopIteration:
        raise ValueError("leer")
    miss = [c for c in REQUIRED if c not in head]
    if miss:
        raise ValueError("Spalten fehlen: %s" % ",".join(miss))
    di = head.index("date")
    n, first, last = 0, None, None
    for row in rd:
        if not row:
            continue
        d = row[di][:10]
        if len(d) != 10 or d[4] != "-" or d[7] != "-":
            raise ValueError("Datum ungueltig")
        if last is not None and d <= last:
            raise ValueError("Datum nicht aufsteigend")
        if first is None:
            first = d
        last = d
        n += 1
    if n == 0:
        raise ValueError("keine Zeilen")
    return n, first, last


def _request(sym, token, timeout=60):
    url = BASE % sym + "?startDate=%s&endDate=%s&format=csv" % (START, END)
    req = urllib.request.Request(url, headers={"Authorization": "Token " + token, "Content-Type": "text/csv",
                                               "User-Agent": "ct109-lf2/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read(MAX_BODY + 1)
    if len(body) > MAX_BODY:
        raise ValueError("Antwort zu gross")
    return body


def fetch_all(symbols, out_dir, token, request=_request, sleep=time.sleep, now=time.monotonic, min_gap_s=MIN_GAP_S,
              max_retries=3, log=print):
    """Ruft alle Symbole ab (Reihenfolge wie uebergeben). Gibt das Manifest-Dict zurueck.
    request/sleep/now sind austauschbar (Tests). Status je Symbol: ok | not_found | error."""
    if not token:
        raise FetchAbort("TIINGO_TOKEN nicht gesetzt")
    os.makedirs(out_dir, exist_ok=True)
    manifest = {"symbols": {}, "start": START, "end": END}
    last_req = None
    done = 0
    max_429 = 12
    for sym in symbols:
        path = os.path.join(out_dir, sym + ".csv")
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    body = f.read()
                n, a, b = validate_csv(body)
                manifest["symbols"][sym] = {"status": "ok", "rows": n, "first": a, "last": b,
                                            "sha256": sha256_bytes(body), "bytes": len(body), "resumed": True}
                continue
            except Exception:
                pass                                    # kaputte Datei: neu abrufen
        tries = 0
        n429 = 0
        while True:
            if last_req is not None:
                wait = min_gap_s - (now() - last_req)
                if wait > 0:
                    sleep(wait)
            last_req = now()
            try:
                body = request(sym, token)
                n, a, b = validate_csv(body)
                tmp = path + ".tmp"
                with open(tmp, "wb") as f:
                    f.write(body)
                os.replace(tmp, path)
                manifest["symbols"][sym] = {"status": "ok", "rows": n, "first": a, "last": b,
                                            "sha256": sha256_bytes(body), "bytes": len(body), "resumed": False}
                break
            except urllib.error.HTTPError as e:
                if e.code in (401, 403):
                    raise FetchAbort("Zugriff abgelehnt (HTTP %d): Token oder Plan pruefen" % e.code)
                if e.code == 404:
                    manifest["symbols"][sym] = {"status": "not_found"}
                    break
                if e.code == 429:
                    n429 += 1
                    if n429 > max_429:
                        raise FetchAbort("Dauerhaft HTTP 429 (Limit); spaeter fortsetzen, bereits geladene Dateien bleiben")
                    log("HTTP 429, warte 600 s")
                    sleep(600)
                    continue                            # Limit erreicht: kein Fehlversuch zaehlen
                tries += 1
                if tries >= max_retries:
                    manifest["symbols"][sym] = {"status": "error", "http": e.code}
                    break
                sleep(60)
            except (urllib.error.URLError, OSError, ValueError, UnicodeDecodeError) as e:
                tries += 1
                if tries >= max_retries:
                    manifest["symbols"][sym] = {"status": "error", "what": type(e).__name__}
                    break
                sleep(60)
        done += 1
        if done % 25 == 0:
            ok = sum(1 for v in manifest["symbols"].values() if v["status"] == "ok")
            log("Fortschritt: %d/%d abgerufen, davon ok %d" % (len(manifest["symbols"]), len(symbols), ok))
    return manifest


def manifest_summary(manifest):
    st = {}
    for v in manifest["symbols"].values():
        st[v["status"]] = st.get(v["status"], 0) + 1
    return {"n_symbols": len(manifest["symbols"]), "status": st}


def finalize_manifest(manifest, universe_hash, spec_hash):
    doc = {"tool": "lf2.fetch", "code_hash": code_hash(), "universe_hash": universe_hash, "spec_hash": spec_hash,
           "manifest": manifest}
    doc["manifest_hash"] = json_hash({k: v for k, v in doc.items() if k != "manifest_hash"})
    return doc
