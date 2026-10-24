# CT109 – Deploy-Paket Paper-Runner (Entwurf zu Spec S3 3.8 / V2.6)

Stand: lf1 v0.6.0 (Einarbeitung der Zweitpruefung QA2, 23.10.2026). **Nichts davon ist installiert oder auf CT109 getestet.** Jede schreibende Aktion auf dem Host braucht einen Einzel-GO nach Schablone `02` §3 (Befehlsblock mit Zeilenumbrüchen, Zweck/Nicht-Zweck, Risiken, Rollback, Abbruch, Nachweis, Satz `GO <Kurzname> – <Hash>`). Die GO-Texte entstehen am Mi 28.10. aus diesen Bausteinen, mit dem Hash des dann endgültigen Pakets.

## 1. Was läuft
- Ein Prozess `paper-run` (stündliche Schleife, 20 s nach Stundenbeginn): holt Kraken-Spot-OHLC 60 min (BTC, ggf. ETH/SOL nur wenn in der Freeze-Liste) und den öffentlichen Futures-Ticker (nur Log). **Zwei öffentliche GET-Ziele, keine Schlüssel, keine Aufträge, kein Zugriff auf Parquet, Registry oder IBKR.**
- Ein Timer `paper-status` (5 min): schreibt `status.html` atomar (statisch, kein Server, kein Port).
- Ein Timer `paper-watch` (stuendlich, Minute 25): `paper-status --max-age-s 7800`; Exit 8 (Kerze fehlt, aelter als 2 h 10 min oder aus der Zukunft, Datenbank/Konfiguration nicht lesbar) loest ueber `OnFailure=signal-unit-failed@%n.service` den bestehenden Alarm aus. Dasselbe `OnFailure` haengt an Runner- und Status-Unit. Der Alarmcode unter `/opt/new-signal-system` bleibt unveraendert (B5).
- Zustand: SQLite `/var/lib/ct109-paper/runner.sqlite` (Kerzen, Entscheidungen, Positionen, Trades, Ereignisse).

## 2. Pfade (alle neu, nichts Bestehendes wird verändert)
| Zweck | Pfad | Besitzer/Rechte |
|---|---|---|
| Code (entpacktes Paket, nur `lf1/`) | `/opt/ct109-paper/lf1/` | root, nur lesbar für den Dienst |
| Freeze-Datei (von Andis PC) | `/opt/ct109-paper/freeze.json` | root, nur lesbar |
| Konfiguration | `/opt/ct109-paper/runner_config.json` (Vorlage `runner_config.example.json`; **alle** Felder Pflicht, unbekannte oder fehlende Felder verweigern den Start; `expected_freeze_hash` und `expected_code_hash` kommen aus dem GO-Text, nicht aus der Datei selbst) | root, nur lesbar |
| Zustand + Statusseite + Kill-Datei | `/var/lib/ct109-paper/` (systemd `StateDirectory`) | dynamischer Benutzer `ct109-paper`, Modus 0755 |
| Unit-Dateien | `/etc/systemd/system/ct109-paper-{runner,status,watch}.service`, `ct109-paper-{status,watch}.timer` | root |
| Einzelinstanz-Sperre | `/var/lib/ct109-paper/runner.sqlite.lock` (flock, entsteht beim Start) | Dienst |

## 3. Betriebsgrenzen (Annahmen, nicht gemessen)
- CPU ≤ 25 % eines Kerns (`CPUQuota`), `Nice=10`; Speicher `MemoryHigh=200M`, `MemoryMax=300M` (erwartet < 80 MB: numpy-Fenster 400 Kerzen); `TasksMax=32`; `LimitFSIZE=256 MiB` je Datei (harte Obergrenze der Datenbank).
- Datenbankwachstum: je Stunde und Asset 1 Kerze, 1 Entscheidung je Hypothese, 1 Heartbeat; ≈ 100 Zeilen/Tag, **Schätzung < 15 MB/Jahr** (nicht gemessen; Messung nach 24 h Schatten, Abbruchkriterium unten).
- Netz: ≪ 1 Anfrage/min je Quelle (je Asset 1 Abruf/h + ≤ 2 Wiederholungen; Ticker 1/h). Kraken-Limits werden nicht berührt.
- Log: nur journald, `LogRateLimit` 100 Zeilen/60 s; der Runner schreibt nur Startzeile und Fehler auf stdout, alles andere in die Datenbank (Tabelle `events`).
- Sandbox der Unit: `ProtectSystem=strict`, `NoNewPrivileges`, leere Capability-Menge, nur `AF_INET/AF_INET6`, `ProtectHome`, `PrivateTmp`. Der Dienst kann außerhalb seines Zustandsordners nichts schreiben.

## 4. Ablauf (jeweils eigener GO, Reihenfolge fest)
**A. Vorprüfungen ohne Schreiben (kein GO nötig, einzelne lesende Aufträge):**
1. Auf Andis PC: `python -m lf1 feed-check` (ein Abruf je Quelle, gibt nur Formatflags aus, keine Preise). Erwartet `"ok": true`. Das prüft die bisher **nie gegen Live-Antworten geprüften** Parser (`feed.py`, Symbole `PF_XBTUSD`, `PF_ETHUSD`, `PF_SOLUSD`).
2. Auf CT109 lesend: `df -h /opt /var/lib`, `systemctl is-active signal-*` (Kapazität und Ausgangslage); `python3 -c "import numpy,sqlite3;print(numpy.__version__)"` → `1.24.2`.
3. Windows-Test des endgültigen Pakets (alle Tests OK, Anzahl und `code_hash` wie im GO).

**B. GO-DEPLOY (schreibend, einmalig):**
1. Paket und `freeze.json` nach CT109 kopieren (z. B. `scp` vom PC), SHA-256 beider Dateien auf dem Host mit den Werten im GO vergleichen.
2. `/opt/ct109-paper/` anlegen, `lf1/` entpacken, `freeze.json` und `runner_config.json` (mit `"shadow": true`) ablegen.
3. Unit-Dateien nach `/etc/systemd/system/`, dann **nur lesend prüfen**: `systemd-analyze verify /etc/systemd/system/ct109-paper-*.service`, `systemd-analyze security ct109-paper-runner.service --no-pager`.
4. `python3 -m lf1 selfcheck` im Verzeichnis `/opt/ct109-paper` (Code-Hash wie im Freeze).
5. `systemctl daemon-reload`, `systemctl enable --now ct109-paper-runner.service ct109-paper-status.timer`.

**C. Schattenbetrieb 24 h** (`"shadow": true`): Kerzen, Signale, Sperren und Lücken werden aufgezeichnet, **es gibt nie einen Einstieg**. Auswertung am Do 29.10.: Feed-Fehler, Verzögerung (`recv_ts − Stundenbeginn`), Lücken, CPU/RAM/Größe der Datenbank, Statusseite, Ereignisse `bar_error`/`open_changed`. Die Schatten-Datenbank zählt **nicht** für die Paper-Wertung und wird archiviert.

**D. GO-PAPER-START (eigener GO):** Dienst stoppen, Schatten-Datenbank nach `/var/lib/ct109-paper/archiv/` verschieben (nicht löschen), `runner_config.json` mit `"shadow": false`, Dienst starten. **Ab hier kein manuelles Eingreifen bei einzelnen Signalen.** Der Kill-Schalter bleibt die einzige Handhabe: `touch /var/lib/ct109-paper/KILL` blockiert neue Einstiege (offene Positionen laufen regulär aus); Entfernen der Datei hebt die Sperre auf. Jeder Einsatz wird mit Datum und Grund in `01` eingetragen und gilt als Abweichung.

## 5. Abbruchkriterien (sofort stoppen und Originalausgabe melden)
- Beim Start Ausgabe `RUNNER START VERWEIGERT` (Exit 6) oder Code-/Freeze-Hash weicht ab.
- Dienst nicht `active` nach 5 min; Neustartschleife (Runner-Unit: `RestartSec=60`, `StartLimitBurst=60` in 2 h, danach `failed` und Alarm; Start verweigert = Exit 6 = sofort `failed` und Alarm).
- `fetch_error` in 3 aufeinanderfolgenden Stunden für dasselbe Asset.
- Datenbank > 200 MB, Speicher an `MemoryMax`, CPU dauerhaft > 25 %.
- Jede Meldung, die ein anderes Netzziel als `api.kraken.com`/`futures.kraken.com` nennt, oder ein Schreibfehler außerhalb von `/var/lib/ct109-paper`.
- Auffälligkeit bei den bestehenden Diensten (Kollektoren, Gateway) seit dem Start: Alarm, Heartbeat oder Lücke, die zeitlich mit der Installation zusammenfällt.

## 6. Rollback (ungetestet)
```
systemctl disable --now ct109-paper-watch.timer ct109-paper-status.timer ct109-paper-runner.service
rm /etc/systemd/system/ct109-paper-runner.service /etc/systemd/system/ct109-paper-status.service /etc/systemd/system/ct109-paper-status.timer /etc/systemd/system/ct109-paper-watch.service /etc/systemd/system/ct109-paper-watch.timer
systemctl daemon-reload
mv /opt/ct109-paper /opt/ct109-paper.entfernt-<Datum>
```
Der Zustandsordner `/var/lib/ct109-paper/` bleibt unangetastet (Beweismaterial). Bestehende Dienste, Parquet und Registry werden zu keinem Zeitpunkt berührt. `apt`/Pakete werden nicht verändert.

## 7. Nachweise nach dem Start (lesend)
- `systemctl is-active ct109-paper-runner.service` → `active`; `journalctl -u ct109-paper-runner.service -n 20 --no-pager` → Zeile `RUNNER START freeze=… code=… assets=…` mit den Hashes aus dem GO.
- `python3 -m lf1 paper-status --config /opt/ct109-paper/runner_config.json` (nur lesend): `age_s` je Asset < 3700, `gap_events` 0, `kill_flag` false.
- Nach dem ersten vollen Stundenwechsel: neue Zeile in `events`/`decisions` (Statusseite zeigt `last_bar_ts` aktuell).

## 8. Bekannte Grenzen
- Antwortformate der Kraken-Endpunkte sind per `feed-check` noch nicht gegen eine Live-Antwort geprüft (Schritt A1).
- `DynamicUser=yes` mit gleichem `User=` in zwei Units (gemeinsamer Zustandsordner) ist nach meiner Kenntnis von systemd 252 unterstützt, auf CT109 aber ungetestet; Ersatz bei Fehler: `User=root` mit unveränderter Sandbox (Entscheid dann im GO-Text).
- Tagesverlustgrenze 1500 bp, `max_open` 2, `late_s` 300 sind Annahmen (Schutz vor Datenfehlern, keine Strategieparameter); jede Sperre wird als `blocked` gezählt und macht den Äquivalenzvergleich `paper-eval` für das Fenster „nicht anwendbar“.
- Ein zweiter Prozess auf derselben Datenbank erzeugt keine doppelten Trades (idempotente Verarbeitung), aber Fehlerereignisse. Betrieb nur über die eine Unit.
- Auswertung läuft offline: `python -m lf1 paper-eval --config … --out …` (Spec v2 V2.6a), beschreibend, ohne Kategorie.
- **Sandbox im unprivilegierten LXC (QA2 m9, Annahme):** `ProtectSystem`, `PrivateDevices`, `RestrictNamespaces`, `DynamicUser` koennen ohne `nesting` mit Exit 226/NAMESPACE scheitern. Dann ist der Dienst nach dem Start `failed` (Alarm), es entsteht kein Schaden; ein Ersatz mit abgeschwaechter Sandbox braucht einen neuen GO-Text. B6 (lesend) prueft vorab, ob bestehende `signal-*`-Units dieselben Direktiven schon nutzen.
- **Schattenbetrieb zaehlt Einstiege zu hoch (QA2 m10):** ohne Position blockiert kein Folgesignal; Schatten-Entscheidungen dienen nur der Feed- und Lastpruefung, nie der Trade-Frequenz oder dem Aequivalenzvergleich.
- **Modus und Datenbank (QA2 M2):** die Datenbank merkt sich beim Anlegen `shadow` oder `paper` (meta `mode`); ein Wechsel auf derselben Datei wird verweigert. Der Wechsel zu Paper laeuft deshalb ueber eine frische Datenbank (GO PAPER-START verschiebt die Schatten-DB).
- **Einzelinstanz (QA2 m4):** zweiter Schreibprozess auf derselben Datenbank wird per flock verweigert (nur Linux; auf Windows gibt es die Sperre nicht, dort laeuft der Runner nie).
- **Entscheidungsgrundlage (QA2 M4):** `decisions.close_px` haelt den Close der Entscheidungskerze fest; spaetere Aenderungen verarbeiteter Kerzen erscheinen als Ereignis `bar_revised`. Unplausible Kerzen (`bad_candle`) und Zukunftskerzen (`future_bar`) werden nicht gespeichert und erscheinen als Fehlerereignisse in der Statusseite (24 h).
- **Nicht abgedeckt:** keine Hashkette ueber die Tabellen (QA2 m12; ein Eingriff in die Datenbank per SQL bliebe unbemerkt, die Datei sollte nur der Dienst schreiben); Backup der einen SQLite-Datei fehlt (Sicherung nach `/var/lib/ct109-paper/archiv/` oder per GO R2-Muster, Entscheid offen); Funding bei spaetem Ausstieg nutzt das geplante H (QA2 m11).
