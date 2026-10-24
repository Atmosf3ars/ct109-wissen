# CT109 lf1 – Lauf auf dem Windows-PC (Gate-Tool, v0.6.0)

Nur Aggregate werden ausgegeben. Rohdaten nie öffnen, nie in Excel laden, nie in den Chat kopieren.
Das ZIP wird **nicht entpackt**: das Tool liest die drei Preisdateien direkt aus dem ZIP.

## 0. Einmalig vorbereiten (PowerShell)
```
python --version
python -m pip install numpy
```
(`python` fehlt? Dann `py` statt `python` benutzen oder Python 3.12 von python.org installieren.)

## 1. Paket entpacken und prüfen
```
Expand-Archive -Path D:\CT109-Bau\CT109_BAU_lf1_v0.6.0_2026-10-23.zip -DestinationPath D:\CT109-Bau\lf1
cd D:\CT109-Bau\lf1
python -W ignore -m unittest discover -s tests
python -m lf1 selfcheck --spec GATE_SPEC_v1.md
```
Erwartet: `Ran <Anzahl laut Meldung> tests ... OK` und in `selfcheck` `"ok": true` bei `spec_check`. Meldung an den Chat: die letzte Zeile der Tests, `code_hash` und `spec_check.ok`.

## 2. Gate-Ablauf (erst nach meinem Signal, Sa 24.10.)
```
$Z = "D:\CT109-Data\kraken-ohlcvt\Kraken_OHLCVT_Full.zip"
cd D:\CT109-Bau\lf1
python -m lf1 file-q --zip $Z --out out
python -m lf1 regime --zip $Z --out out
python -m lf1 window-q --zip $Z --regime out\regime_selection.json --out out --window A
```
Nach `regime` zuerst nur die Zeile `REGIME_HASH` und das Feld `status`, `W`, `A`, `B` an den Chat. **Erst danach** der einmalige Gate-Lauf:
```
python -m lf1 gate --zip $Z --regime out\regime_selection.json --spec GATE_SPEC_v1.md --out out
```
Der Gate-Lauf ist einmalig (Sperrdatei `out\gate_lock_A.json`). Bei einem technischen Fehler nichts löschen, Fehlermeldung an den Chat. `out\` komplett aufbewahren (später auf `D:\CT109-Backup\` mit Hash).

## 2a. Epochen-Qualität für die Bestätigung (Spec v2 V2.2; nur Zähler, auf Anweisung)
```
python -m lf1 epoch-q --zip $Z --regime out\regime_selection.json --out out --assets BTC
```
Ausgabe: je Epoche (E1 bis 2020, E2 ab 2021) erwartete/vorhandene Bars, Fehlend-Quote, größte Lücke, `valid`. Keine Signale, keine Renditen. Den Inhalt von `out\q_epochs.json` bitte an den Chat.

## 2b. Freeze und Backtest (erst nach meinem Signal, So 25.10.)
Die Hypothesenliste (`hypotheses.json`, höchstens 2 Klasse-W-Hypothesen) liefere ich als fertigen Block. Danach genau zwei einmalige Schritte:
```
python -m lf1 freeze --zip $Z --regime out\regime_selection.json --gate out\gate_result_A.json --hyps hypotheses.json --bau-spec BAU_SPEC_S1S3_v2.md --out out
python -m lf1 backtest --zip $Z --regime out\regime_selection.json --freeze out\freeze.json --stage discovery_A --out out
```
`freeze` schreibt `out\freeze.json` (Zeile `FREEZE_HASH` an den Chat, **vor** dem Backtest). Stufe D (`discovery_A`) ist beschreibend (Spec v2). Die Bestätigung (Spec v2, Montag, erst nach meinem Signal) ist ein dritter, ebenfalls einmaliger Schritt: `python -m lf1 backtest --zip $Z --regime out\regime_selection.json --freeze out\freeze.json --stage confirm --out out` (verlangt vorher Stufe D; prüft die Qualität je Epoche und lehnt ab, wenn E2 ungültig ist, ohne die Sperre zu verbrauchen). Alle Schritte sind einmalig; bei technischem Fehler nichts löschen, Meldung an den Chat. Ausgabe nur Aggregate.

## 2c. Paper-Runner (nur Deploy, nach Owner-GO; auf dem Windows-PC nicht ausführen)
`python -m lf1 paper-run --config runner_config.json` (Schleife) bzw. `--once` (ein Zyklus), `paper-status` (JSON). Das Modul `lf1/feed.py` ist das einzige mit Netzzugriff: zwei öffentliche GET-Ziele, keine Schlüssel, keine Aufträge. Der Start wird verweigert (Exit 6), wenn Freeze-Hash, Code-Hash oder die Bindung der Datenbank an den Freeze nicht passen.

Zusätze v0.5.0: `shadow: true` in `runner_config.json` (Schattenbetrieb, nie ein Einstieg), `paper-status` öffnet die Datenbank nur lesend, eine unverarbeitbare Kerze wird als `bar_error` protokolliert und blockiert den Lauf nicht. Deploy-Entwurf (Unit-Dateien, Quoten, Rollback, Abbruchkriterien): `deploy/DEPLOY.md`.
Zusätze v0.6.0 (Zweitprüfung QA2): `runner_config.json` verlangt jetzt **alle** Felder (inkl. `expected_freeze_hash`, `expected_code_hash`), unbekannte Felder verweigern den Start; Zukunfts- und unplausible Kerzen werden nicht gespeichert (Ereignisse `future_bar`, `bad_candle`); `paper-status --max-age-s N` liefert Exit 8 bei fehlender/zu alter/zukünftiger Kerze; Datenbank merkt sich den Modus (Wechsel Schatten→Paper nur mit frischer Datenbank); zweiter Schreibprozess wird verweigert (Linux).

## 2d. Formatprüfung der Live-Abrufe (PC, ohne GO, nur Lesen)
`python -m lf1 feed-check` ruft je Quelle einmal die öffentliche Kraken-Schnittstelle ab und gibt nur Zähler und Flags aus (keine Preise). Erwartet: `"ok": true`, Exit 0. Bei Abweichung Exit 7: die Ausgabe unverändert an den Chat.

## 2e. Offline-Auswertung des Paper-Laufs (später, nach Start)
`python -m lf1 paper-eval --config runner_config.json --out out`: liest die Runner-Datenbank nur lesend, rechnet Netto-Expectancy, Block-Bootstrap, Placebo-Zwillinge (feste Seeds) und vergleicht den Runner mit dem Backtest auf denselben gespeicherten Kerzen. Rein beschreibend, **keine Kategorie**.

## 3. Exit-Codes
0 ok, 2 Spec-Hash falsch, 3 Regimewahl BLOCKED, 4 Gate/Freeze/Backtest abgelehnt (Sperre/Regeln), 5 Datenfehler, 6 Runner-Start/Paper-Eval verweigert, 7 Formatprüfung der Live-Abrufe fehlgeschlagen.
