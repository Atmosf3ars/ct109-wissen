# CT109 – 00 START HIER

**Stand:** 22.10.2026, Konsolidierung nach Modellwechsel (Quellen: Übergabe-ZIP, Hostbelege bis 22.10. ≈ 20:45 UTC, Repo-Check 22.10. abends). §8 „Dokumentationssicherung und Übergabe“ am 22.10. 22:55 Berlin ergänzt.
**Zweck:** Einziger Einstieg. Wer nur diese Datei und `01_STATUS.md` liest, kann morgen sicher weiterarbeiten.
**Doktrin:** Discovery offensiv. Validierung ohne Gnade. Gemessen bleibt gemessen, Annahmen bleiben Annahmen. Niemals PASS ohne Beleg.

## 1. Die fünf Dateien (alles andere liegt im Archiv)

| Datei | Inhalt | Änderungsrhythmus |
|---|---|---|
| `00_START_HIER.md` | Regeln, Lesereihenfolge, Grenzen, Evidenzstufen, Übergabe-/Sicherungsregeln (§8) | selten |
| `01_STATUS.md` | Gates, Komponenten, Kapazität, im Code geprüfte Fakten, Dokulücken | täglich (eine Zeile im Änderungslog) |
| `02_ENTSCHEIDUNGEN_GO.md` | Wer darf was, bisherige GOs, GO-Schablone, Incident 114, D1–D8, Risiko-Notiz Host-Schlüssel | bei jedem GO |
| `03_FORSCHUNG.md` | Ergebnisbilanz, Kostenhürden, SOL-O1, Forschungsrichtung | bei Ergebnissen |
| `04_PLAN.md` | Plan-Review, Entscheidung des Einsatzleiters, Tagesplan ab 23.10., Claude-Code-Aufträge | täglich |
| `ARCHIV/INDEX.md` | Zuordnung alt → neu mit SHA-256; Originale bleiben unverändert im ZIP | nie |

**Sechste Datei, mit Begründung (22.10.2026):** `GATE_SPEC_v1.md` – die Gate-Spezifikation. Sie muss **unveränderlich** sein, weil ihr SHA-256-Hash (eingetragen in `01` §1/§6) vor jedem Datenblick den Beweis liefert, dass Schwellen und Regeln nicht nachträglich angepasst wurden; in einer täglich geänderten Datei wäre das nicht möglich. Änderungen nur als v2 vor Datenzugriff. Zugleich Ausnahme von der Regel „keine V-Nummern“: die Versionsnummer gehört hier zur Hash-Kette.

Nicht angefasst und weiter maßgeblich: `PROJECT.md`, `PROJECT_PROMPT.md` (Gründungsdokumente), im Repo `BLUEPRINT.md`, `ARCHITECTURE.md`, `RUNBOOK.md`, `PREREGISTRATION.md`, `docs/CT109_SOL_PREREG_DRAFT_2026-10-21.md`.

**Neue Regel gegen Dokumentenflut:** Keine V-Nummern, keine vier Tagesdateien mehr. Tagesabschluss = Änderungslog-Zeile in `01_STATUS.md` + Update `04_PLAN.md`. Neue Dateien nur mit Begründung hier.

## 2. Lesereihenfolge morgen
1. Diese Datei (5 Min). 2. `01_STATUS.md` §1–§3. 3. `04_PLAN.md` §3 und §5 (erste Aufträge). 4. Rest bei Bedarf.

## 3. Evidenzstufen (jede Aussage trägt eine)
Aufsteigend in der Beweiskraft:

| Stufe | Bedeutung |
|---|---|
| L1 | Dokumentierte Aussage (Übergabe, Chat, Bericht, Textangabe des Owners ohne Ausgabe) |
| L2 | Bericht von Claude Code |
| L3 | Terminalausgabe/Screenshot vom Owner |
| L4 | Lokales Git-Objekt |
| L5 | GitHub-API/PR |
| L6 | Synthetischer Test |
| L7 | Realer Produktionstest |
| L8 | Unabhängiger Restore |
| L9 | Authentisches Owner-GO |
| **C** | **Code gelesen/getestet in der Cloud-Sandbox am Repo-Stand `13d58ad` (nicht auf dem Host).** Beweist Codeverhalten, nicht Hostzustand. |

Status-Vokabular: `PASS` (nur mit Beleg, Stufe genannt), `PASS-OFFLINE`, `BLOCKED`, `UNKNOWN`, `OPEN`. Alle Zeiten UTC; Berlin = UTC+2 bis 25.10. 03:00 Uhr, danach UTC+1.

## 4. Absolute Grenzen (gelten, bis Andi je Einzelfall anders entscheidet)
Ohne separates, eng umrissenes Owner-GO **nicht**: Registry-Schreiben, `seal_fs rollback`/Entsiegelung, Stage-2-/Archivlöschung, Produktiv-Merge/-Push/-Deploy, Dienst starten/stoppen/ändern, SSD-Migration/LVM-Resize, Schlüsselprovisionierung, echte Daten im unsicheren `analysis-run`, neuer Lernbot-Canary, BTC/ETH-L2-Live ohne Gates, C2, Echtgeld, Orders, Broker-Aktionen. **Der 10-Tage-Plan ist kein GO.** Es wird keine Fernverbindung zum Proxmox-Host angenommen.

Vor jeder schreibenden Aktion dokumentieren: exakter Befehl, Zweck, Risiken, Sicherung/Rollback, Abbruchkriterien, separates GO (Schablone in `02`).

## 5. Arbeitsmodus
- Ein kurzer Read-only-Auftrag pro Runde (`04` §5), Host und UTC-Zeit festhalten, Originalausgabe anfordern, erst dann PASS/BLOCKED/UNKNOWN.
- Projektregeln: höchstens 6–8 Hypothesen, Benjamini-Hochberg-FDR bei Bestätigung, Hypothesenliste vor Bestätigungsdaten fixiert, mindestens zwei Marktregime, Maßstab immer Expectancy je Trade gegen die faire Rate 1/(1+R) (Review R12 vom 09.10. merkt an, dass 1/(1+R) nicht universell gilt; ob und wie das entschieden wurde, ist nicht dokumentiert – Netto-Expectancy in bp nach Kosten wird deshalb immer mitgeführt), Paper-Trading vollautomatisch und Pflicht vor Echtgeld.
- Lab (`ct109-agentic-lab`) ≠ Produktion (`new-signal-system`). Lab-PASS ist nie Produktiv-PASS.
- Befehlsblöcke für den Host immer **mit Zeilenumbrüchen** und mit Hinweis, sie als Block einzufügen (Beinahe-Fehler R1, `01` §5.13).

## 6. Beantwortete und offene Fragen (Stand 22.10. 22:50 Berlin)
1. **Entscheidungsregime (D1) – entschieden von Andi:** „Entscheiden, nicht fragen“. Gefragt wird nur, wenn es wirklich kritisch ist: Orders/Echtgeld/Broker, Löschung von Rohdaten, Siegel/Entsiegelung/Registry-Schreiben, Schlüssel, Abo-Klicks (Kosten), Produktiv-Merge/-Deploy/-Dienststart am Host, alles Irreversible. Alles andere (Read-only, Offline-Design, Sandbox-Code, Auswertungen auf öffentlichen Daten, Doku) entscheidet der Einsatzleiter und meldet es im Ergebnis. Die absoluten Grenzen in §4 bleiben GO-pflichtig.
2. **Paid Feeds – Antwort von Andi (Angabe, nicht gemessen):** IBKR läuft; ca. 40 USD/Monat für Abos zu 3 Aktien inkl. Depth (NASDAQ, „glaube ich“). Passt zu PROJEKTSTAND §10 (44,50 USD/Monat; NYSE OpenBook nicht gebucht). Kraken-Feeds kostenlos. Genaue Abo-Liste und Abrechnungsdatum: Auftrag B bzw. IBKR-Kontoansicht.
3. **„Ja“ von Andi zu den offenen Empfehlungen:** D2 E-129-Frist → Kapazitäts-Trigger; D4 „Kein Feed ohne Hypothese“; D6 Offline-Code; D7 Historie-Download. **D3 und D8 sind am 22.10. 22:20 Berlin vom Einsatzleiter entschieden (`02` §6)**; dort auch die Risiko-Notiz zum Schreibrecht des Host-Schlüssels (`02` §7). **Erledigt am 22.10.:** E2, E4, Windows-Hashvergleich des Codes, R1 (Registry-Kopie, Hash-Vergleich auf `D:` laut Andi), Deploy-Key-Abgleich. **Offen:** E4b, Deploy-Key auf Read-only (Ruleset ist im kostenlosen Plan bei privatem Repo nicht wirksam), GO R2 (täglicher Registry-Timer), A1 (Fr 23.10. ab 03:30 UTC), A2 (Proxmox-Backup), A3.

## 7. Prompt für den neuen Chat (Kopiervorlage)
```
Du bist leitender Systemarchitekt und Quant-Researcher von CT109 („Neues Signalsystem“). Projektinstruktionen gelten.
Lies zuerst im Projekt die fünf Dateien unter ct109/: 00_START_HIER, 01_STATUS, 02_ENTSCHEIDUNGEN_GO, 03_FORSCHUNG, 04_PLAN (nur diese; Originale liegen im ARCHIV-Index) sowie GATE_SPEC_v1. Prüfe Aussagen mit Evidenzstufen; kein PASS ohne Beleg. Mach als Erstes die Übergabeprüfung nach 00 §8 (neue Lücken in 01 §5 eintragen, Zeile im Änderungslog).
Ziel: bis Mo 02.11.2026 läuft ein vollautomatischer Paper-Betrieb (eingefrorene LF-1-Hypothesenliste + Placebo-Kontrolle), davor Gate-Ergebnis und Discovery/Bestätigung auf Historie in zwei Regimen (04_PLAN §4, Version 2 „parallel“). Wir sind mutig, die Validierung ist gnadenlos.
Regeln: Regime „Entscheiden, nicht fragen“ außer bei wirklich Kritischem (00 §6); Host-Schreibaktionen/GitHub-Push/Registry nur mit Einzel-GO (02 §3), ein Read-only-Auftrag pro Runde, Originalausgaben anfordern, Lab ≠ Produktion. Höchstens 8 Hypothesen, Freeze vor Signalauswertung, BH-FDR, zwei Regime, Netto-Expectancy je Trade nach Kosten. Code nur Offline/Sandbox (D6). Kein manueller Eingriff im Paper-Lauf. Tagesabschluss = Änderungslog-Zeile in 01 + Update 04, keine neuen V-Dateien (Sicherungspaket nach 00 §8).
Antworte auf Deutsch, knapp, mit klaren Entscheidungen statt Optionslisten.
```

## 8. Dokumentationssicherung und Übergabe (gegen Verlust beim Modell-/Sitzungswechsel; Beschluss des Einsatzleiters 22.10. 22:55 Berlin)
**Was beim letzten Wechsel abhanden gekommen ist (Befunde der Konsolidierung vom 22.10., Details `01` §5):** (1) Entscheidungen standen nur im Chat (E-129-Wortlaut, SOL-Kategorienentscheid); (2) Arbeit existierte nur auf dem Host (Paper-Harness nie committet; Registry seit 11.10. ohne Sicherung); (3) Zusammenfassungen ersetzten Quellen, Belege nicht auffindbar (R01–R17, Phase-1-Abnahme, H-ML-A-Ergebnis, V169-Systembackup); (4) es gab keine Übergabeprüfung – das Fehlende fiel erst durch das Nachlesen auf.

**Regeln:**
1. **Nichts gilt, was nur im Chat steht.** Jede Entscheidung, jedes GO, jedes Ergebnis wird noch am selben Tag mit Wortlaut, Datum, Quelle und Stufe in `02` (Entscheidung/GO) oder `01` (Befund) eingetragen; Zusagen wie „ja“ in `02` §6.
2. **Arbeit existiert erst, wenn sie gesichert ist:** in Git (GitHub) **oder** auf `D:` mit Hash. Der Host ist Laufzeit, nicht Werkstatt: Entwicklung nur in einem Git-Checkout in der Cloud-Sitzung oder auf Andis PC, der Host bekommt Code nur per Deploy-GO. Vor jedem Modell-/Sitzungswechsel und mindestens wöchentlich läuft eine Read-only-Inventur im Stil von E1/E4 (ungepushte Commits, Dirty/Untracked, neue Dateien außerhalb von Test-Venvs).
3. **Zustand sichern:** Registry-Kopie täglich (GO R2 offen), Hash-Kopie nach `D:`; Laufzeitdaten nach D3 (Blockebene).
4. **Quellen nicht durch Zusammenfassungen ersetzen:** `ARCHIV` bleibt unverändert mit Hash im INDEX; jede Aussage nennt Quelle und Stufe; eine Aussage ohne auffindbare Quelle ist höchstens L1 oder UNKNOWN.
5. **Keine stillen Streichungen:** Wird in 00–04 etwas entfernt oder umgedeutet, steht es im Änderungslog.
6. **Sicherungspaket (Tagesabschluss, mindestens wöchentlich und immer vor einem Modellwechsel):** Der Einsatzleiter liefert ein ZIP aus `00`–`04` und `GATE_SPEC_v1.md` mit `SHA256SUMS`; Andi legt es auf `D:\CT109-Backup\doku-JJJJ-MM-TT\` ab. Der ZIP-Hash steht im Änderungslog. Grund: Die Projektdokumente liegen sonst nur im claude.ai-Projekt (Einzelmedium). Erstes Paket: Fr 23.10.
7. **Übergabe-Gate, vor dem Wechsel (bisheriger Einsatzleiter):** `01` aktuell inkl. Änderungslog bis jetzt; `02` enthält alle GOs/Entscheidungen; `04` enthält offene Aufträge im Wortlaut; Repo-Inventur zeigt nichts Ungesichertes; Sicherungspaket erstellt und abgelegt.
8. **Übergabeprüfung, nach dem Wechsel (neuer Einsatzleiter):** liest `00`–`04` und `GATE_SPEC_v1`, prüft jede Hauptaussage gegen ihre Stufe, trägt neue Lücken in `01` §5 ein und schreibt eine Zeile im Änderungslog („Übergabeprüfung: n Lücken, davon m neu“). Erst danach wird weitergearbeitet.
9. **Wiederherstellungstest (einmal vor dem Paper-Start, bis 28.10.):** Eine frische Sitzung bekommt nur das Sicherungspaket von `D:`. Sie muss die offenen Punkte aus `01` §5 und den Stand der GOs aus `02` §2 korrekt wiedergeben. Gelingt das nicht, ist das Paket oder die Doku lückenhaft.
