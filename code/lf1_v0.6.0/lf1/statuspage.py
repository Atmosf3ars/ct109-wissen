"""Statusseite des Runners als statische, selbstenthaltene HTML-Datei (kein Server, kein offener Port, kein Skript)."""
import html

STALE_S = 2 * 3600 + 600        # aelter als 2 h 10 min: Feed gilt als veraltet


def _fmt_ts(ts):
    import time as _t   # nur Formatierung eines uebergebenen Zeitstempels (UTC), keine Uhrabfrage
    return _t.strftime("%Y-%m-%d %H:%M:%SZ", _t.gmtime(int(ts)))


def render(status, events=None):
    e = html.escape
    rows = []
    for a in sorted(status["last_bar_ts"]):
        age = status["age_s"][a]
        bad = age > STALE_S or age < 0
        note = " VERALTET" if age > STALE_S else (" ZUKUNFT" if age < 0 else "")
        rows.append("<tr><td>%s</td><td>%s</td><td class=%s>%d s%s</td></tr>" % (
            e(a), e(_fmt_ts(status["last_bar_ts"][a])), "bad" if bad else "ok", age, note))
    for a in status.get("missing_assets", []):
        rows.append("<tr><td>%s</td><td>-</td><td class=bad>KEINE KERZE</td></tr>" % e(a))
    hyp = []
    for p in status["per_hypothesis"]:
        blocked = ", ".join("%s: %d" % (e(k or "-"), v) for k, v in sorted(p["blocked"].items())) or "-"
        hyp.append("<tr><td>%s</td><td>%d</td><td>%.2f</td><td>%s</td></tr>" % (e(p["id"]), p["trades"], p["net_sum_bp"], blocked))
    evs = ""
    if events:
        evs = "<h2>Letzte Ereignisse</h2><table><tr><th>UTC</th><th>Art</th><th>Detail</th></tr>%s</table>" % "".join(
            "<tr><td>%s</td><td>%s</td><td>%s</td></tr>" % (e(_fmt_ts(x["ts"])), e(x["kind"]), e((x["detail"] or "")[:200])) for x in events)
    kill = "<b class=bad>KILL-FLAG GESETZT</b>" if status["kill_flag"] else "kein Kill-Flag"
    return ("<!doctype html><html lang=de><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
            "<title>CT109 Paper-Runner</title><style>body{font:14px system-ui,sans-serif;margin:16px;max-width:900px}"
            "table{border-collapse:collapse;margin:8px 0}td,th{border:1px solid #888;padding:3px 8px;text-align:left}"
            ".bad{color:#b00020;font-weight:bold}.ok{color:#146c2e}"
            "@media (prefers-color-scheme:dark){body{background:#111;color:#eee}.ok{color:#6fd68a}.bad{color:#ff7a8a}}</style>"
            "<h1>CT109 Paper-Runner</h1><p>Stand %s &middot; Freeze <code>%s</code> &middot; Code <code>%s</code> &middot; lf1 %s</p>"
            "<p>Modus: %s &middot; %s &middot; offene Positionen: %d &middot; Lückenereignisse: %d &middot; <span class=%s>Fehlerereignisse 24 h: %d</span></p>"
            "<h2>Feed</h2><table><tr><th>Asset</th><th>letzte Kerze</th><th>Alter</th></tr>%s</table>"
            "<h2>Hypothesen</h2><table><tr><th>ID</th><th>Trades</th><th>Netto-Summe bp</th><th>gesperrte Entscheidungen</th></tr>%s</table>%s"
            "<p><small>Nur Anzeige. Simulation mit öffentlichen Marktdaten, keine Aufträge, kein Echtgeld.</small></p></html>") % (
        e(_fmt_ts(status["now_ts"])), e(status["freeze_hash"][:16]), e(status["code_hash"][:16]), e(status["lf1_version"]),
        e(str(status.get("mode"))), kill, status["open_positions"], status["gap_events"],
        "bad" if status.get("errors_24h", 0) else "ok", status.get("errors_24h", 0), "".join(rows), "".join(hyp), evs)
