# CT109 – 04 PLAN

**Stand:** 23.10.2026 ≈ 20:40 Berlin (Freeze, Stufe D und B gelaufen, beide Hypothesen `NULLBEFUND`; Hostbelege zu CT109 bis 23.10. B6; Abschnitte älter als §5k sind Verlauf). Der Plan des Owners (`10_TAGE_PLAN`, beschlossen 19.10., Original im ARCHIV) ist **Arbeitsplanung, kein GO**. Dieses Dokument enthält das Review des Einsatzleiters, den daraus folgenden Kurs und die nächsten Read-only-Aufträge.

## 1. Warum der 10-Tage-Plan gemacht wurde – und wie kritisch er wirklich ist
Auslöser (aus den Dokumenten, L1): Hostausfall 19.10. (Datenlücke ≈ 09:10–09:43 UTC), Incident 114 am 18.10., E-129-Frist 23.10., SOL-Siegelübergang 26.10. ohne eine einzige registrierte Hypothese, neuer Code (V142, 23 Dateien) nur auf CT109. Der Plan ist damit **ein Schutz- und Integritätsplan mit einem Forschungsanteil**, kein Forschungsplan.

| Klasse | Gilt hier? | Was konkret |
|---|---|---|
| Sicherheitskritisch (Geld, Orders) | **Nein** | Nichts ist live, keine Orders, kein Echtgeld, C2 tot, Lernbot aus. |
| Verlustkritisch (irreversibel) | **Ja** | V142 + 23 Dateien (inzwischen gesichert, `01` §1); versiegelte Rohdaten (3994 Dateien) laut Code **nicht im Archiv** → Einzelkopie auf der Root-LV, Sicherung UNKNOWN (`01` §3.2); Archiv-SSD ein Einzelmedium. **Neu (E2/E4):** Registry `meta.sqlite` war seit 11.10. ungesichert (jetzt R1 + Kopie auf `D:`, tägliche Sicherung fehlt); Host-only-Arbeit unter `/root/run` (u. a. Paper-Harness, nie committet) nicht in Git. |
| Integritätskritisch | **Ja** | Siegel/Registry (Incident 114) und Freeze-Kette: ohne sie ist kein späteres Ergebnis belastbar – hier entscheidet sich, ob Bestätigungsdaten überhaupt gültig bleiben. |
| Platzkritisch | **mittelfristig, nicht akut** | 36 % belegt, ≈ 62 GiB bis Alarm, 16–76 Tage je nach (unsicherer) Rate; Pool systemisch überprovisioniert. |
| Kalenderkritisch | teils | 25.10. Zeitumstellung (alles in UTC), 26.10. SOL sealed; E-129-Datum war nur abgeleitet (§2). |

**Selbstkritik:** Vier der fünf P0-Punkte schützen Infrastruktur, nur einer (SOL) ist Forschung – bei laufenden Datenkosten und null Edge ist das schief. Infrastrukturarbeit ist nur dort gerechtfertigt, wo Verlust irreversibel ist (Code, Rohdaten-Kopie, Siegelintegrität, Registry) oder wo sie Forschung entsperrt (sicherer Reader).

## 2. Entscheidung des Einsatzleiters (Punkt für Punkt)
| Plan-Punkt | Entscheidung | Begründung |
|---|---|---|
| **E-129 Stage 2 „bis 23.10.“** | **Frist durch Kapazitäts-Trigger ersetzen** (Owner-OK nötig, D2). 23.10.: ehrliche Meldung „Stage 1 läuft (Journal), Stage 2 nicht gestartet, BLOCKED“. | Das Datum ist aus der Schätzung vom 11.10. „85-%-Alarm in ≈ 19 Tagen“ abgeleitet (Annahmen: Parquet 0,7 GB/Tag, Spool 13 GB/Tag). Gemessen heute ≈ 62 GiB Luft. Stage 2 löscht irreversibel, hat **keinen Reader-Fallback im Code**, widerspricht dem Beschluss vom 26.09. (keine Rohdaten löschen) und kann nach Code nur Discovery-Tage betreffen – der Großteil (sealed) bliebe ohnehin. Löschen unter Zeitdruck ist das gefährlichste Element des Plans. **Trigger:** Stage-2-*Design* startet, wenn aus ≥ 5 Messpunkten die Restlaufzeit bis 85 % < 30 Tage oder die Luft < 30 GiB ist. Stage-2-*Ausführung* nie ohne: Reader-Fallback implementiert+getestet, unabhängiger Stichproben-Restore, Andis Entscheid zu 26.09. |
| V142 Offhost + Dirty-Arbeit (23 Dateien) + alle lokal-only Branches | **ERLEDIGT (22.10.)** – war P0 Platz 1 (drei RCs `889b52c`, `66b4b0b`, `9d29b94` nachweislich nicht auf GitHub) | Reihenfolge: E1/E1b/E3/E1c → GO Schritt 1 → 2A (GitHub, L5) → 2B (Windows `D:`, Hash vollständig gleich, L3). Details §5b. Offen nur optional: `git bundle verify` auf Windows; age-Empfänger (Auftrag D) nur nötig, falls verschlüsselt kopiert werden soll. |
| Sicherung der **versiegelten Rohdaten** | **Neu, P0 (Information zuerst)** | Auftrag A2 klärt, ob Proxmox-Backup/Snapshots existieren. D3 entschieden (`02` §6): nur Blockebene, nie über Entsiegelung. |
| **Registry-Sicherung (`meta.sqlite`)** | **R1 AUSGEFÜHRT (22.10. 20:37 UTC, PASS, L3); Kopie auf `D:` mit Hashvergleich (Owner-Angabe, L1); tägliche Sicherung = R2 offen** | R1-Ergebnis: §5c. Damit existiert erstmals seit 11.10. eine Sicherung außerhalb der Live-DB und außerhalb der LV. Die Registry wächst weiter; eine Einzelkopie reicht nicht → Entwurf GO R2 (täglicher Timer, Rotation, Kopie auf `D:`) als eigene Host-Schreibaktion. Restore- und Zeilenabgleich-Test nicht erbracht. |
| Sicherung Host-only-Arbeit (`/root/run` u. a.) | **ERLEDIGT (L3): GO H1 ausgeführt 15:24 Berlin, Kopie auf `D:` per Hash geprüft 15:27; Rest-Lücke: 6× `test_wp6_night1.py` (E5 optional)** | E4: Masse ist Test-Venv-Ballast, Paper-Harness nie committet (`git log` leer). Secret-Scan war wegen Venv-Rauschen unbrauchbar → E4b (ohne Venvs). Sicherungs-GO danach nach Schablone Schritt 1: Tar der Werte (Harness, Skripte, Doku, Ledger-Kopien, `/root`-md/Patches) ohne `tmp-ro`/`fv`, ohne Secret-/Konfig-Dateien, **Kopie nach `D:` mit Hash (kein GitHub-Push vom Host)**. |
| Sicherer Reader (R1–R9 im SOL-Entwurf) | **Neu, P0-Forschungs-Enabler** | Ohne ihn kann *keine* echte Analyse sauber laufen (B3). Erst Offline-Design + synthetische Tests, dann eigenes GO. |
| SOL-Freeze am 23.10. | **Verschieben, kriteriengetrieben** | Termin erzwingt Pfusch (unsicherer Reader, unauthentischer Freeze). Der Siegelübergang 26.10. macht neue Tage zu Bestätigungsdaten – das ist gewollt, kein Verlust. Erst Bewegungsbudget-Gate (`03` §5, `GATE_SPEC_v1.md`), dann Hypothesentexte. |
| Lernbot-Guard/Autostopp | **Auf P2 herabstufen** | Dienst ist inactive/disabled; Risiko besteht nur bei versehentlichem Start. Placebo ist −11,30 bp/Trade – ein weiterer Canary prüft Plumbing, keinen Edge. Option für Andi: Unit *maskieren* (reversibel, eigenes GO) statt Watchdog-Bau. |
| SSD-Pfad A (Deploy/Migration) | **Zurückstellen** | Kein akuter Platzdruck, hohes Risiko (Mount, Rollback, geteilter Pool). Stattdessen Messreihe + Thin-Pool-Alarm entwerfen. |
| BTC/ETH-L2 Live (T0 28.10.) | **Aus dem Zeitplan nehmen**, bleibt BLOCKED | Regel „Kein Feed ohne Hypothese“ (D4) und fehlende 30-Tage-Kapazität. |
| Incident 114 | **Behalten** | Read-only, billig, Basis der Siegelintegrität. |
| Status-App 8000 | erledigt (GO ausgeführt) | – |
| Agentic-Lab | **Nur prüfen (Auftrag C), nicht erweitern** | `CT109_AGENTS_ENABLED=true` laut Owner, Läufe/Kosten unbekannt; Lab-Output ist nie Produktivbeleg. |
| Doku | erledigt mit diesen 5 Dateien (+ `GATE_SPEC_v1.md`); **Wissensspeicher `ct109-wissen` (GitHub) angelegt, Migration läuft** (`00` §8, `01` §1) | – |
| **Neu:** Bewegungsbudget-Gate + LF-1-Design (Offline) | **Neu, P1-Forschung – künftige Hauptlinie** | Mit bereits gemessenen σ-Werten ist die Kostenwand belegt: bis 5 min braucht jedes Signal ρ ≥ 0,4–1,0 (`03` §5). Stunden–Tage-Horizonte und US-Aktien (2,3–3,9 bp) sind der plausible Raum; L2-Aufzeichnung wird dafür nicht gebraucht. Spezifikation eingefroren (Hash in `01`). |
| **Neu:** Kapazitäts-Messreihe | **P0, täglich eine Zeile** | Die Rate ist die größte Unsicherheit hinter dem Platzargument. |

## 3. Plan gegen Ist (Stufe L1, nicht neu geprüft)
- 20.10.: Code-Recovery begrenzt PASS (V166), Incident 114 lesend geprüft. Owner-Signaturschlüssel: kein Beleg.
- 21.10.: CT9109-Teilrestore PASS, SOL-Entwurf, Status-App gestoppt, Lernbot lesend inventarisiert.
- 22.10.: SSD-Pfad A BLOCKED (wie vorhergesehen), V142 lokaler Commit, Lernbot-Sicherheitslaufplan nicht erledigt. Stage 1 läuft stabil.
- Fazit: Schutzteil im Rahmen, Forschungsteil (SOL) auf dem Stand „Entwurf, 0 Hypothesen“ – wie der Plan selbst („Null-Befund wahrscheinlich“) erwartet.

## 4. Sprint bis Mo 02.11.2026 – Version 2 „mutig, parallel“ (ersetzt Version 1)
**Ehrliche Lage (Einsatzleiter, 22.10. abends):**
- **Paper-Betrieb läuft am 02.11.: haltbar, aber nur mit dem parallelisierten Plan unten.** Der lineare Plan (Bau erst nach Discovery, Paper-Start 31.10.) hat keinen Puffer und wird am 02.11. nicht halten.
- **Edge-Erkenntnis am 02.11.: nicht haltbar.** Auf Stunden-/Tageshorizont entstehen bis dahin nur wenige Forward-Trades. Am 02.11. haben wir: Gate-Ergebnis, Historien-Ergebnis in zwei Regimen (Kandidat oder Nullbefund) und einen laufenden, unbeaufsichtigten Automaten. Forward-Aussagen frühestens Ende November.
- Der Zeitplan fällt, wenn eine der drei Bedingungen reißt: (1) Andi beantwortet D1–D8 und erteilt die zwei Host-GOs (Mi 28.10. Deploy+Shadow, Do 29.10. Paper-Start) rechtzeitig; (2) die Kraken-Historie ist am Sa 24.10. nutzbar (Fallback: REST-OHLC, Tageskerzen ≈ 2 Jahre, genügt für Tageshorizont); (3) der Bau läuft interaktiv mit Claude Code (nach D6); das Lab ist nur Zusatzkapazität, bis es umgebaut und geprüft ist (Auftrag C).

**Prioritätsregel (22.10. 23:25 Berlin, Einsatzleiter):** Kritischer Pfad ist die Bauspur (Runner-RC + QA-PASS bis Di 27.10.; Stand 22.10.: noch kein Code). Am Fr 23.10. kommen zuerst D7 (Kraken-Download), S1–S3 und Baubeginn der Bibliothek in der Sandbox sowie Auftrag C. Sicherungsarbeit (GO für `/root/run`, GO R2, Doku-Paket) ist bis Fr 15:00 Berlin gedeckelt; A1 (ab 03:30 UTC) und E4b laufen als kurze Read-only-Aufträge nebenher. Meldet sich bis Sa 24.10. abends keine nutzbare Historie, greift der Fallback (Tageskerzen); ohne Runner-QA-PASS am Di 27.10. verschiebt sich das Deploy, die QA wird nie gekürzt.

**Kernprinzipien**
1. **Ein Code, zwei Einsatzorte:** Signal- und Fill-/Kostenlogik liegen in **einer** gemeinsamen Bibliothek; Backtest und Paper-Runner importieren sie. Dann kann das Live-Modell nicht vom Backtest abweichen.
2. **Runner generisch:** Er führt eingefrorene Regeltypen (Ausbruch, Zeitreihen-Momentum, Fade nach Schock) aus einer Parameterdatei aus – er braucht die endgültige Hypothesenliste erst zum Start, nicht zum Bau. Dadurch Bau parallel zur Discovery.
3. **Discovery bleibt streng seriell:** Gate → Freeze → Discovery (Regime A, einmalig) → Bestätigung (Regime B). Parallel wird nur Werkzeug gebaut, nie ausgewertet.
4. **Lab-Realität (gelesen am 22.10., Lab-main `e82a78d`):** Die Bots laufen aktuell nicht, und ihre Aufgabenliste gehört zum alten Plan. Das Lab fährt **höchstens einen Coding-Lauf pro Tag** (A/B im Wechsel), Abhängigkeiten brauchen manuelle Freigabe (`DONE_QA_OWNER_ACK`), Coding pausiert ab 30.10. und am Wochenende, Codex-QA ist nicht als verbunden belegt. Damit **können die Bots den kritischen Pfad nicht tragen**. Entscheidung: Der kritische Pfad (Bibliothek, Gate, Backtest, Runner) wird **interaktiv mit Claude Code** gebaut (Andis PC bzw. Cloud-Sitzung, nach D6); die Lab-Bots übernehmen parallel abgegrenzte Teile (Mutationstests, Härtung, Adapter, Review-Template), sobald das Lab umgebaut ist. Umbau-Liste: `lab_draft/CHANGES_LAB_REPO.md`; neue Queue: `lab_draft/docs/TASKS.json`; Bot-Spezifikation: `lab_draft/docs/SPRINT_LF1_SPEC.md` (alle als Entwurf, nichts im Lab geändert). Reale Daten und echte Läufe bleiben außerhalb des Labs.
5. **Rollenbild:** *Claude Code interaktiv* = Hauptentwicklung und Ausführung auf echten Daten (Aggregate zurück an den Chat). *Bot A/B* = Zusatzkapazität im Lab, nur synthetisch. *Codex/QA* = unabhängige Prüfung vor jedem Host-Schritt.
6. **Runner-Basis (D8, `02` §6):** neuer eigener Runner; die Lernbot-Engine ist nicht Basis (Buch-/Tick-gebunden). **Neu offen (E2/E4-Fund):** Der host-only Paper-Harness unter `/root/run/ct109-D3-build922-2026-10-16/r/` (`src/paper`: 11 Dateien ≈ 90 KB, u. a. machine, broker, ib_adapter, fake_ib, async_fake_ib, risk, ledger, alerts, fwguard, harness; `tests/paper` wp1–wp12; `docs/paper` 17 Dateien ≈ 247 KB; `deploy/paper`) ist für Track S (IBKR-Paper-Konto) potenziell wiederverwendbar. **Nie committet** (E4, L3). Entscheid über Wiederverwendung erst nach Sicherung (E4b → Sicherungs-GO) und Review; bis dahin weder bauen noch verwerfen.

| Tag | Parallelspur 1: Forschung (seriell) | Parallelspur 2: Bau (Claude Code interaktiv; Lab-Bots + QA ergänzend) | Andi / GO |
|---|---|---|---|
| **Fr 23.10.** | **Erledigt:** D7 (Download, Hash), Q-Prüfung, Regimewahl, **Gate-Lauf A** (24/72 h zulässig, Klasse W, höchstens 2 Hypothesen), Sicherung. **Backtest-Modul (Freeze, Einmal-Lauf, C1–C5) gebaut, 89 Tests, 31 Mutationen, Paket v0.2.0** (Windows-Test folgt). **Runner-Gerüst gebaut** (122 Tests, 21 Mutationen). Offen: Spec-v2-Entwurf (Sa), Bestätigungsstufe C7 (nach Spec v2), Runner: Deploy-Paket, Statusseite, Zweitprüfung | `lf1` v0.1.1 (Gate, Kern) auf Windows PASS; **Backtest `lf1.backtest` bauen** (Freeze, Einmal-Lauf, Block-Bootstrap, BH-FDR, Placebo, Stress); einmaliger Codex-Review von `lf1` vor Abo-Ende nur mit Andis Freigabe für Push-Zugriff aufs Lab (`02` D14) | Variable auf `false` (erledigt, laut Andi); E4b-Ausgabe; ab 15:00 Entwürfe für GO `/root/run` und GO R2 |
| **Sa 24.10.** | **`BAU_SPEC_S1S3_v2` (**festgeschrieben und gehasht Fr 23.10.**, `34d6add4…e068`; Einspruch bis So-Freeze möglich):** Bestätigung auf der Vorhistorie außerhalb von A, Regime-Aufteilung, Fenster B als Pflicht-Teilprüfung; Kostenmodell je Epoche; Hypothesen-Kandidaten (≤ 2) vorbereiten, **ohne** Signalauswertung | Backtest fertig + Mutationstests (≥ 15); Runner-Skelett (Zustandsspeicher, Kill-Switch, Hash-Wächter) | v2 lesen (Entwurf), keine Rechenläufe |
| **So 25.10.** | **Vorgezogen auf Fr 23.10. Abend (Entscheidung D18, `02`; vorher: So abends, ursprünglich vormittags/nachmittags) Freeze** der Liste (**höchstens 2**, nur 24/72 h) → Hash, danach **Discovery Regime A**, einmalig, in einem Zug (Block 1–3 in §5k; Freeze-Hash prüfe ich vor Stufe D selbst; Windows-Lauf, nur Aggregate zurück). EU-Zeitumstellung: alles UTC | Runner feature-complete (Datenpfad, Placebo, Logging); Äquivalenztest Runner = Backtest | Freeze-Hash bestätigen; Discovery-Befehl ausführen (E-Q erledigt 23.10.: E1 ungültig, E = E2, D16) |
| **Mo 26.10.** | **Bestätigung nach Spec v2 (abends, wenn Andi am PC ist; Entscheidung 23.10.)** (unberührte Vorhistorie), BH-FDR → ≤ 1 Kandidat oder Nullbefund | Mutationstests Runner (Doppel-Fill, Kosten=0, Lücken, Reboot, Zeitumstellung); **Zweitprüfung durch einen Claude-Agenten mit frischem Kontext** (kein Codex mehr, `02` D14) | Bestätigungs-Befehl ausführen |
| **Di 27.10.** | Bericht Discovery/Bestätigung. **Runde-2-Liste** (u. a. `XDGUSD`, `XRPUSD`, Kostenannahme je Coin, Perp-Existenz prüfen; `02` D12) einfrieren, bei Nullbefund Pflicht | **Runner-RC + QA-PASS (intern: Mutationen, Äquivalenz, Zweitprüfung; nicht unabhängig im Sinne von Codex)**; Deploy-Paket CT109 + GO-Texte | GO-Texte lesen |
| **Mi 28.10.** | Kapazitätsaussage (≥ 5 Messpunkte); Wiederherstellungstest der Doku (`00` §8.9) | **GO Deploy → Shadow-Modus 24 h** (Live-Daten, keine Paper-Einstiege) | **GO Deploy + Start** |
| **Do 29.10.** | Shadow-Auswertung (Feed, Latenz, Lücken, Last) | Bei PASS: **GO Paper-Start** – eingefrorene Liste (+ Runde 2 als separate zweite Liste, falls vorhanden) + Placebo | **GO Paper-Start** |
| **Fr 30.10.–So 01.11.** | Beobachten ohne Eingriff (jeder Eingriff macht den Test ungültig); Aktien-Track: Datenquelle + IBKR-Paper klären, Gate mit 2,3–3,9 bp | Aktien-Backtest-Adapter (Offline, durch mich) | – |
| **Mo 02.11.** | **Bilanz:** laufender Paper-Betrieb ≥ 4 Tage, Modell-vs.-Realität-Abweichungen, Deskriptivzahlen ohne Entscheidungen; nächste Runde | – | Sprint-Review |

**Abbruch-/Verzögerungslogik:** Gate ohne bestandenen Horizont → keine LF-1-Discovery, Runde 2 sofort, Paper-Start bleibt (Placebo + Runde 2). Runner nicht QA-PASS am 27.10. → Deploy verschiebt sich um Tage, nie abkürzen. Historie unbrauchbar am 24.10. → Fallback Tageskerzen via REST, Horizonte auf ≥ 1 Tag beschränkt.
**Kosten-/Lastwarnung:** **Stand 23.10.: Lab-Bots aus (`CT109_AGENTS_ENABLED=false`, Andi), ChatGPT-Abo und damit Codex-QA enden heute.** Die Bots entfallen im Sprint; Bau und QA liegen bei Claude allein (Engpass: ein Bauer; Verzögerung wird sofort gemeldet, QA wird nie verkürzt). Vor jeder späteren Reaktivierung Auftrag C (erledigt 23.10.) und Umbau-Liste (`lab_draft/CHANGES_LAB_REPO.md`) abarbeiten. Datenzugang bleibt < 50 €/Monat (keine neuen Feeds).
**Track S (Aktien):** erst ab Fr 30.10.; nativer IBKR-Paper-Account, kein Order-Pfad ohne eigenes GO.

## 5. Claude-Code-Aufträge (Read-only, eine Runde = ein Auftrag)
**Stand der Aufträge (23.10.):** A1 ausgeführt (Teilergebnis, `du`-Befehl fehlerhaft, `01` §5.25), A1b ausgeführt (23.10. 08:55 UTC) · C ausgeführt (Cloud, lesend; Variable offen) · E4b danach · A2/A3/B/D offen · D7-Anleitung §5d.
Jeweils: Host und UTC-Zeit in die Ausgabe, Originalausgabe/Screenshot an mich zurück. Alle Befehle lesen nur; `du` mit `nice/ionice`, damit die Aufzeichnung nicht gestört wird.

**Auftrag E1 – Inventur lokaler, ungepushter Git-Arbeit (CT109, root, read-only; ausgeführt 22.10. 19:41 UTC):**
```
date -u; cd /opt/new-signal-system && pwd
git worktree list
git for-each-ref --format='%(refname:short) %(objectname:short) %(committerdate:short)' refs/heads refs/tags | sort -k3
git log --branches --not --remotes --oneline | head -150
git stash list
for w in $(git worktree list --porcelain | awk '/^worktree /{print $2}'); do echo "== $w"; git -C "$w" status --short | wc -l; git -C "$w" log --branches --not --remotes --oneline | wc -l; done
for s in 66b4b0b 9d29b94 889b52c; do git cat-file -t $s; git branch --contains $s; done
git count-objects -vH
```
Zweck: Welche Commits existieren nur lokal, welche Worktrees/Stashes/Dirty-Dateien gibt es. Falls `/opt/new-signal-system` nicht der Git-Pfad ist: `git -C <Pfad>` des Produktiv-Checkouts verwenden.

**Auftrag E2 – Arbeit außerhalb von Git (CT109, root, read-only; ausgeführt 22.10. 20:20:36 UTC):** Der ursprüngliche Plan-Wortlaut wurde am 22.10. erweitert (Registry-Schutz-Metadaten, `SHA256SUMS`, Git-Zugangs-Metadaten); der ausgeführte Block (nur Namen/Größen/Zeiten, nie Inhalte):
```
date -u; hostname
ls -la --time-style=long-iso /root /root/run 2>/dev/null | head -80
for d in /root/backup-*; do echo "-- $d"; find "$d" -maxdepth 2 -printf '%y %s B %TY-%Tm-%Td %TH:%TM %p\n' | sort -k5 | head -40; nice -n19 ionice -c3 du -sxB1 "$d"; done
stat -c '%s B %a %U %y %n' /root/secrets.env.bak
ls -la --time-style=long-iso /var/lib/new-signal-system | head -40
nice -n19 ionice -c3 find / -xdev -type f \( -name 'meta*.sqlite*' -o -name 'meta*.db*' \) -not -path '/proc/*' -printf '%s B %TY-%Tm-%Td %TH:%TM %p\n' 2>/dev/null | tail -40
systemctl list-timers --all --no-pager | grep -Ei 'backup|meta|registry|dump|snapshot' || echo "kein Backup-Timer gefunden"
ls /etc/cron.d /etc/cron.daily 2>/dev/null
cat /root/backup-code/SHA256SUMS
for f in /opt/new-signal-system/deploy/systemd/*; do b=$(basename "$f"); if [ -f /etc/systemd/system/$b ]; then diff -q "$f" /etc/systemd/system/$b >/dev/null || echo "DRIFT $b"; else echo "NICHT-INSTALLIERT $b"; fi; done
ls -la /etc/new-signal-system
nice -n19 ionice -c3 find / -xdev -type f -newermt 2026-10-12 \( -name '*.py' -o -name '*.sh' -o -name '*.md' -o -name '*.yaml' -o -name '*.json' -o -name '*.patch' \) -not -path '*/.venv/*' -not -path '/proc/*' -not -path '/usr/*' -not -path '/var/lib/new-signal-system/parquet/*' -not -path '/var/lib/new-signal-system/spool/*' -not -path '/opt/new-signal-system/.git/*' 2>/dev/null | head -200
git -C /opt/new-signal-system remote -v | sed -E 's#//[^@/]*@#//***@#'
ls -la /root/.ssh /root/.git-credentials /root/.config/gh 2>&1 | awk '{print $1, $5, $9}'
```
**E2 – Ergebnis (L3, Originalscreenshots des Owners, Host `new-signal-system`, 22.10. 20:20:36 UTC; ausgewertet):**
1. **Bundle-Hash:** Host `SHA256SUMS`: Bundle `f0924e0c466e923bf80b7321bc2cb57f10450136e4775c3efb37cbc4187ca6ea`, `dirty-perp` `cef119b5…945c`, `dirty-step7` `06014aab…9f29`. Dateigrößen: Bundle 815 470 B, perp-Tar 20 480 B, step7-Tar 286 720 B. **Windows-Hashvergleich (Owner, `Get-FileHash`, 22.10. ≈ 20:30 UTC, L3): alle drei Hashes vollständig gleich → Code-Sicherung PASS.** Die drei `CT109_LERNBOT_STEP7_*.patch` und `SHA256SUMS` auf `D:` sind nicht gegen den Host verglichen.
2. **Registry-Schutz: LÜCKE BESTÄTIGT.** Live-DB `/var/lib/new-signal-system/meta.sqlite` 5 812 224 B (20:19), WAL 4 148 872 B (20:20), Besitzer `signalsvc`, Modus 0644. Jüngste Kopien: `/root/backup-2026-10-11/meta-vor-migrate.sqlite` (11.10. 13:26, 2 441 216 B, mit `.sha256`), `/root/meta-2026-10-10.sqlite` und `/root/backup-2026-10-10/meta.sqlite` (je 2 342 912 B). Nichts nach dem 11.10. Weder Backup-Timer (nur `dpkg-db-backup.timer`) noch Cron-Eintrag im Container (`/etc/cron.d`: e2scrub_all, sysstat; `cron.daily`: apt-compat, dpkg, logrotate, man-db, sysstat). Kopien unter `/tmp/pytest-of-root/…` sind synthetische Test-Fixtures, kein Schutz. Proxmox-Ebene UNKNOWN (A2). **Seit 22.10. 20:37 UTC durch R1 geschlossen (§5c).**
3. **Backup-Ordner (nur Namen/Größen):** `backup-2026-10-10` (config.ini 36 728 B, meta.sqlite + shm/wal), `backup-2026-10-11` (meta-vor-migrate, `referenz-*`/`archiv-ref-*` JSONs inkl. Katalog-Referenzen 626–628 KB, gesamt 4,4 MB – Belege zum Archiv-Volllauf vom 11.10.), `backup-2026-10-12` (nur `nftables.conf.vor-ibkr-guard`, 243 B), `backup-code` (Bundle, 2 Tars, Listen, `push.specs`, `SHA256SUMS`; 1,1 MB), `backup-f3-2026-10-14` (`ibkr.env.20261014T071938Z`, 569 B). **`config.ini` (Größe/Name → vermutlich IBC-Konfiguration; Vermutung, nicht gelesen) und die `ibkr.env`-Kopie sind wie `secrets.env.bak` zu behandeln: nie kopieren, nie ausgeben.**
4. **`secrets.env.bak`:** 975 B, Modus 600, root, 01.10. 14:36 (stat, deckt sich mit `01`). In `/etc/new-signal-system`: `secrets.env` 979 B (0600) und **`ibkr.env` 612 B mit Modus 0644 (weltlesbar, Inhalt ungeprüft)** → Rechteprüfung P1 (Änderung wäre Host-Schreibaktion, eigenes GO).
5. **GitHub-Zugang:** Remote ist **SSH** (`git@github.com:Atmosf3ars/new-signal-system.git`, fetch + push), kein Token in der URL. Schlüsseldateien `/root/.ssh/id_ed25519_new_signal_system` (432 B, 0600) und `.pub` (116 B), `config` (198 B), `authorized_keys` (100 B), `known_hosts`. `/root/.git-credentials` und `/root/.config/gh` **existieren nicht** → Personal-Access-Token als Push-Pfad ausgeschlossen (L3). Fingerprint aus E4: siehe unten.
6. **Units:** keine `DRIFT`-Meldung für reguläre Unit-Dateien des Prod-Checkouts (L3). Die zwei Meldungen `NICHT-INSTALLIERT` (`signal-compactor.service.d`, `signal-unit-failed@signal-lernbot-watch.service.service.d`) betreffen **Verzeichnisse**; der Test prüfte nur reguläre Dateien (`-f`) – **kein Beleg für Abwesenheit** (eigener Testfehler).
7. **Host-only-Arbeit (Namen, Liste bei 200 Zeilen vermutlich abgeschnitten):** `/root/run` hat 77 Verzeichnisse (Lernbot-Step7b/8-Skripte und Mutationstests, Preflights, Coin-Scouting, Auswertungen), außerdem `/root/befund-2026-10-06.md` (13 KB), `ergebnis.md` + `.bak`, drei `CT109_LERNBOT_STEP7_*.patch`, `/root/wt` (26 Einträge), `/root/.claude(.json)`, `/root/.bash_history` (14,9 KB, Inhalt nie kopieren). Größter Fund: `/root/run/ct109-D3-build922-2026-10-16/r/` enthält eine komplette **Paper-Harness**-Struktur. **Cloud-Gegenprobe (C/L5): in GitHub-main und im Tip aller 16 `offhost-backup/*`-Branches 0 Dateien unter `src|tests|docs|deploy/paper`; `backup-code` enthält nur Bundle + zwei Dirty-Tars.**

**Auftrag E4 – Inventur Host-only-Arbeit + Schlüssel-Fingerprint (CT109, root, read-only; ausgeführt 22.10. ≈ 20:30 UTC):**
```
date -u; hostname
nice -n19 ionice -c3 du -sxB1 /root/run /root/wt 2>/dev/null
find /root/run -xdev -type f | wc -l
nice -n19 ionice -c3 find /root/run -xdev -type f -size +5M -printf '%s B %p\n' | head -20
nice -n19 ionice -c3 grep -rEIl 'BEGIN [A-Z ]*PRIVATE KEY|AGE-SECRET-KEY|(api|secret|token|passw)[a-z_]*[ ]*[=:][ ]*.[A-Za-z0-9/+_=-]{16,}' /root/run 2>/dev/null | head -40
find /root/run -xdev -type f \( -iname '*.env*' -o -iname '*.key' -o -iname '*.pem' -o -iname '*secret*' -o -iname '*credential*' -o -iname '*.sqlite*' -o -iname '*.db' -o -iname 'config.ini' \) -printf '%s B %p\n' | head -40
ls -la --time-style=long-iso /root/run/ct109-D3-build922-2026-10-16/r/src/paper /root/run/ct109-D3-build922-2026-10-16/r/docs/paper
git -C /opt/new-signal-system log --all --oneline -- src/paper | head -5
ssh-keygen -lf /root/.ssh/id_ed25519_new_signal_system.pub
```
**E4 – Ergebnis (L3, Originalscreenshots des Owners; ausgewertet):**
1. `/root/run` 1 069 891 584 B in 31 484 Dateien; `/root/wt` 57 434 112 B. **Die Masse sind Test-Venvs** (`tmp-ro/…/fv/lib/python3.11/site-packages/…` in `ct109-build921-D1-…` und `ct109-build91-stufeA-…`, u. a. `_duckdb` ≈ 60 MB, `pyarrow`-Bibliotheken) – kein Sicherungswert, nicht löschen (Löschen = GO).
2. **Paper-Harness:** `src/paper` 11 Dateien ≈ 89,6 KB (`machine.py` 25 650 B, `harness.py` 21 615 B, `ledger.py` 10 863 B, `fwguard.py` 7 423 B, `fake_ib.py` 7 329 B …), `docs/paper` 17 Dateien ≈ 247 KB, alle mtime 16.10. 22:37. **`git log --all -- src/paper` leer → nie committet.** Inhalt/Teststand UNKNOWN.
3. Weitere Funde: Lernbot-Ledger-Kopien (`shadow-run2-copy.sqlite` 1 765 376 B; `shadow-live.sqlite` + WAL 3 168 312 B), `config.ini` je 36 733 B (`deploy/ibc/`, Repo-Vorlagenkopien) sowie `ibkr.env.example`/`secrets.env.example` (Vorlagen).
4. **Secret-Zählscan unbrauchbar (eigener Entwurfsfehler):** die ersten 40 Treffer waren nur Fremdbibliotheken in den Venvs; Namenslisten durch `head` abgeschnitten (Broken-pipe-Meldungen harmlos). Keine Aussage über den eigenen Code → E4b.
5. **Host-Schlüssel:** `256 SHA256:D12zzo5vfg+jyi9srviqEIn3qscmwJ8cR9P7SvELPDg deploy-key new-signal-system CT109 (ED25519)`. Der Kommentar ist nur eine Beschriftung; **Owner-Abgleich 22.10. 22:46 Berlin (L1): Deploy-Key mit Read/write** (`02` §7).

**Auftrag E4b – Host-only-Arbeit ohne Test-Venvs (CT109, root, read-only; nur Dateinamen/Größen/Zahlen, NIE Treffer-Inhalte; nicht in den Minuten :05–:10; vorgeschlagen, noch nicht ausgeführt):**
```
date -u
nice -n19 du -sxB1 --exclude=tmp-ro --exclude=fv /root/run
nice -n19 find /root/run \( -name tmp-ro -o -name fv -o -name .git -o -name __pycache__ \) -prune -o -type f -print | wc -l
echo "--- Secret-Muster (nur Dateinamen, eigener Code)"
nice -n19 grep -rIlE '(api[_-]?key|secret|passw(or)?d|BEGIN [A-Z ]*PRIVATE KEY|ibkr.*(user|pass))' /root/run --exclude-dir=tmp-ro --exclude-dir=fv --exclude-dir=.git --exclude-dir=__pycache__ 2>/dev/null | sort | tee /dev/stderr | wc -l
echo "--- sensible Namen"
nice -n19 find /root/run \( -name tmp-ro -o -name fv -o -name .git \) -prune -o -type f \( -iname '*.env' -o -iname '*.pem' -o -iname '*.key' -o -iname 'config.ini' -o -iname '*secret*' -o -iname '*credential*' \) -print 2>/dev/null | sort
echo "--- Ledger-Originale"
nice -n19 find /var/lib /root /opt -xdev \( -name 'shadow*.sqlite' -o -name 'shadow*.db' \) -size +0 -printf '%s %TY-%Tm-%Td %p\n' 2>/dev/null | sort -k2
```
Zweck: Größe und Dateizahl der echten Arbeit ohne Venv-Ballast, Secret-Kandidaten im eigenen Code (nur Namen), Ort der Ledger-Originale. Lesart: Treffer sind Kandidaten, kein Beweis; Muster begrenzt. Ergebnis bestimmt Umfang und Ausschlussliste des Sicherungs-GO für `/root/run`.

**Auftrag A1 – CT109-Shell als root, frühestens 23.10. 03:30 UTC (05:30 Berlin, nach dem Archivlauf), nicht in den Minuten :05–:10:**
```
date -u
df -B1 --output=source,size,used,avail,pcent / /mnt/archiv
journalctl -u signal-archive.service --since "2026-10-23 03:15:00 UTC" --until "2026-10-23 03:40:00 UTC" --no-pager | tail -25
nice -n19 ionice -c3 du -sxB1 /var/lib/new-signal-system /var/lib/new-signal-system/parquet /var/lib/new-signal-system/spool
```
Zweck: dritter Kapazitätspunkt, Archivlauf 23.10. (Kandidaten/kopiert/Fehler/`sealed`-Zahl), Aufteilung Parquet/Spool. Kein Registry-, kein Seal-Zugriff. **Korrektur 23.10.:** `--since/--until` jetzt mit Suffix `UTC` (Zeitzone von CT109 UNKNOWN, `01` §5.19). **Auswertungsregeln (vorab):** Archivlauf = PASS (Job) nur bei `copied` = Kandidatenzahl und 0 Fehlern; Wachstumsrate nur aus Messpunkten ≥ 20 h Abstand, Parquet und Spool getrennt; Stage-2-Design-Trigger nur bei ≥ 5 Messpunkten und Restlaufzeit bis 85 % < 30 Tage oder Luft < 30 GiB (D2).

**Auftrag A1b (Ersatz für die `du`-Zeile von A1), CT109-Shell als root, nicht in den Minuten :05–:10:**
```
date -u
nice -n19 ionice -c3 du -xB1 --max-depth=1 /var/lib/new-signal-system
nice -n19 ionice -c3 du -xB1 --max-depth=1 /var/lib/new-signal-system/parquet
```
Zweck: Aufteilung Parquet/Spool und Größe je Venue (nur Größen, keine Inhalte). **Auswertungsregeln (vorab):** Summe der Ebene-1-Zeilen muss auf ±1 % zur Gesamtzahl 32 471 126 016 B (23.10. 08:53 UTC) passen, sonst Lesart UNKNOWN; Messpunkt zählt für die Rate nur bei ≥ 20 h Abstand zu einem früheren Punkt. Originalausgabe zurückgeben.

**Auftrag A4 (ausgeführt 23.10. 09:38 UTC, Ergebnis `01` Changelog) – CT109-Shell als root (nur lesen, nicht in den Minuten :05–:10):**
```
date -u
python3 --version
python3 -c "import numpy,sqlite3;print('numpy',numpy.__version__,'sqlite',sqlite3.sqlite_version)"
pip3 --version
free -m
curl -sS -m 10 -o /dev/null -w "kraken_time_http=%{http_code}\n" https://api.kraken.com/0/public/Time
curl -sS -m 10 -o /dev/null -w "futures_tickers_http=%{http_code}\n" https://futures.kraken.com/derivatives/api/v3/tickers
```
Zweck: Läuft der Runner (Python ≥ 3.11, numpy, sqlite) ohne Zusatzinstallation auf CT109, und erreicht CT109 die beiden öffentlichen Endpunkte (je ein GET, kein Schlüssel)? **Auswertungsregeln (vorab):** `ModuleNotFoundError numpy` heißt: Installation nötig, das wäre ein eigener Owner-GO (Host-Schreibaktion); HTTP-Code 200 je Endpunkt = erreichbar, alles andere = Datenpfad BLOCKED bis zur Klärung. Originalausgabe zurückgeben.

**Auftrag A5 (ausgeführt 23.10. 09:40 UTC, Ergebnis `01` Changelog) – CT109-Shell als root (nur lesen, nicht in den Minuten :05–:10):**
```
date -u
apt-cache policy python3-numpy | head -6
apt-get -s install --no-install-recommends --no-upgrade python3-numpy | grep -E "^(Inst|Remv|Conf)|upgraded|newly installed"
df -B1 --output=source,avail /
```
Zweck: Welche Paketversion und welche Zusatzpakete würde `apt` für numpy ziehen, ohne dass etwas installiert, aktualisiert oder entfernt wird (`-s` = Simulation, schreibt nichts)? **Auswertungsregeln (vorab):** Voraussetzung für einen GO-Entwurf: Simulation zeigt **0 `Remv`**, **0 aktualisierte** Bestandspakete, nur neue Pakete (erwartet ≈ 5–10, ≈ 30–40 MB), numpy-Kandidat ≥ 1.24. Zeigt `apt-cache policy` keinen Kandidaten oder ist der Index veraltet, ist `apt-get update` ein zusätzlicher Schritt im GO. Originalausgabe zurückgeben.

**`GO NUMPY` (Schablone `02` §3; erteilt und ausgeführt 23.10. 09:42 UTC, Ergebnis `01` Changelog, Verbrauch `02` §2):**
1. **Befehl** (CT109, root, Arbeitsverzeichnis egal, nicht in den Minuten :05–:10; Block mit Zeilenumbrüchen):
```
date -u
nice -n19 ionice -c3 apt-get install -y --no-install-recommends --no-upgrade python3-numpy
python3 -c "import numpy; print('numpy', numpy.__version__)"
dpkg -l python3-numpy libblas3 liblapack3 libgfortran5 | tail -4
```
   Befehl-Hash (SHA-256 des Blocks, Zeilenende LF): `017acd18babb0b454aa47cafd507a3576a99f1d81067547b2a8e1325fb3d25d0`.
2. **Zweck:** `numpy` 1.24.2 aus dem Debian-Hauptarchiv für den Paper-Runner (Auftrag A5, Simulation: 4 neue Pakete `libblas3`, `libgfortran5`, `liblapack3`, `python3-numpy`, 0 Updates, 0 Entfernungen). **Nicht Zweck:** kein `pip`, keine Aktualisierung der 74 offenen Bestandspakete, kein Dienstneustart, kein Zugriff auf Registry, Siegel, Parquet oder Spool, kein Runner-Deploy.
3. **Risiken:** Last gering (≈ 30–40 MB Download, `nice`/`ionice`). Datenrisiko: keins erkennbar, die Pakete sind neu, bestehende Dateien werden nicht überschrieben (Simulation: 0 `Remv`, 0 upgraded). Restrisiko: ein anderes Programm hängt von den neuen Bibliotheken nicht ab, die Dienste laufen unberührt weiter (nicht gemessen). Kosten: keine.
4. **Rollback (ungetestet):** `apt-get remove -y python3-numpy` (die drei Bibliotheken bleiben harmlos liegen; `apt-get autoremove` wird **nicht** ausgeführt).
5. **Abbruch:** jede Fehlermeldung von `apt-get`, jede Aufforderung zur Bestätigung außer `-y`, jede Zeile `Remv` oder `upgraded` > 0 in der Ausgabe: nichts weiter ausführen, Originalausgabe zurückgeben.
6. **Nachweis:** `numpy 1.24.2` in der Ausgabe von `python3 -c …` und `dpkg -l` zeigt `ii` für alle vier Pakete.
7. **Satz von Andi:** `GO NUMPY – 017acd18`. Gilt nur für diesen Block, einmalig.

**Auftrag A2 – Proxmox-Host (nur falls Andi Zugang hat):** `pct config 109 | grep -E "rootfs|mp0|backup"`; `cat /etc/pve/jobs.cfg 2>/dev/null`; `pvesm status`; `ls -la <Backup-Storage>/dump | tail`; `lvs -o lv_name,lv_size,data_percent,lv_time pve`. Zweck: Existiert irgendeine Sicherung der CT109-Root-LV (also der versiegelten Rohdaten **und** der Registry)? Ergebnis `JA/NEIN/UNKNOWN`.

**Auftrag A3 – CT109, Incident-114-Positivkontrolle:** `stat -c '%n|%a|%u:%g|ctime=%z|mtime=%y'` auf `…/parquet/venue=kraken/date=2026-10-06` bis `…-10-18`; `journalctl -u signal-compactor.service --since "2026-10-19 00:05" --until "2026-10-19 00:10" --no-pager`; `getfacl -p` auf das 12.10.-Verzeichnis **ohne** `2>/dev/null`. Kein Registry-Lesen (WAL-Nebenwirkung → eigene Isolationsentscheidung).

**Auftrag B – Dateninventur (CT109):** `systemctl list-units 'signal-*' ibgateway.service --all --no-pager --plain`; `ls /var/lib/new-signal-system/parquet`; `nice -n19 ionice -c3 du -sxB1 /var/lib/new-signal-system/parquet/venue=*`; `systemctl is-active signal-ibkr ibgateway`. Zweck: Welche Feeds laufen, was belegen sie, läuft IBKR (44,50 USD/Monat)?

**Auftrag C – Lab (GitHub, Andis PC, PowerShell mit `gh`; ausgegeben 23.10.):**
```
gh variable list -R Atmosf3ars/ct109-agentic-lab
gh workflow list -R Atmosf3ars/ct109-agentic-lab --all
gh run list -R Atmosf3ars/ct109-agentic-lab -L 20 --json databaseId,workflowName,event,status,conclusion,createdAt,updatedAt
gh pr list -R Atmosf3ars/ct109-agentic-lab --state all -L 30 --json number,title,state,isDraft,author,updatedAt
```
Zweck: Läuft die Automatik, wie oft, mit welchen Ergebnissen; keine Secrets, keine Variablenwerte mit Schlüsselcharakter in den Chat kopieren (bei Zweifel Wert durch `***` ersetzen). **Auswertungsregeln (vorab):** „Automatik läuft“ nur bei `CT109_AGENTS_ENABLED=true` **und** mindestens einem Lauf mit `conclusion=success` in den letzten 48 h; Kosten sind nur als Anzahl Läufe belegbar (Abrechnung nicht lesbar, Preis UNKNOWN); Codex-Verbindung gilt nur als belegt, wenn ein Review/Kommentar eines Codex-Kontos an einem PR existiert (sonst UNKNOWN); offene Draft-PRs #8/#10/#14 werden nicht gemergt. Ergebnis fließt in `lab_draft/CHANGES_LAB_REPO.md` Punkte 8–10.

**Auftrag D – Windows PowerShell (nur Metadaten):** `Get-ChildItem D:\CT109-Backup -Recurse -File | Select FullName,Length,LastWriteTime`; `Test-Path "$env:USERPROFILE\CT109-Keys\ct109-age-key.txt"` (nur Existenz, **Inhalt nie ausgeben**). Zweck: Existiert das V169-Systembackup (31 482 185 159 B), wo liegt der age-Schlüssel. (Hash-Zusatz für die Code-Sicherung: erledigt, siehe E2 Ergebnis 1.)

**Von mir bereits erledigt (Stufe C, `01` §3):** statische Reader-Pfad-Inventur für Stage 2 – Ergebnis: es gibt keinen Fallback.

### 5b. GO CODE-SICHERUNG – Paket (Schritte 1, 2A, 2B abgeschlossen; Schablone `02` §3)
**Zweck:** Alle 21 ungepushten Commits + die einzigartigen Dirty-Dateien an zwei weitere Orte bringen. **Nicht Zweck:** Merge, Änderung von `main`, Löschen/Aufräumen von Branches/Worktrees, Dienständerung. **Risiken:** Schritt 1 legt nur neue Dateien (<10 MiB) auf dem Root-LV an; Schritt 2A schreibt neue Branches in ein privates Repo ohne CI; kein Secret-Treffer (E3, Heuristik). **Rollback:** Schritt 1 `rm -r /root/backup-code` (nur dieses Verzeichnis); Schritt 2A Branches `offhost-backup/*` löschen. **Abbruch:** `git bundle verify` ≠ OK; Tar-Dateizahl ≠ erwartet; Push-Fehler.

**Schritt 1 – lokal auf CT109 (`GO CODE-SICHERUNG SCHRITT 1`, ausgeführt):**
```
date -u; mkdir -p /root/backup-code && cd /root/backup-code
git -C /opt/new-signal-system bundle create /root/backup-code/nss-all-2026-10-22.bundle --all
git bundle verify /root/backup-code/nss-all-2026-10-22.bundle
git -C /root/wt/lernbot-step7-2026-10-17 status --short | awk '{print $2}' > step7.list
git -C /root/wt/perp-l2-2026-10-19 status --short | awk '{print $2}' > perp.list
tar -cf dirty-step7-2026-10-22.tar -C /root/wt/lernbot-step7-2026-10-17 -T step7.list
tar -cf dirty-perp-2026-10-22.tar -C /root/wt/perp-l2-2026-10-19 -T perp.list
tar -tf dirty-step7-2026-10-22.tar | wc -l; tar -tf dirty-perp-2026-10-22.tar | wc -l
sha256sum *.bundle *.tar > SHA256SUMS; cat SHA256SUMS; ls -la
rm -rf /tmp/nss-bundle-test && git clone -q nss-all-2026-10-22.bundle /tmp/nss-bundle-test
for h in 889b52c 66b4b0b bcdfb4a 10cf18c 9d29b94 9b4d2e4 39d8b66 b972a4f 86767dd 5fe3f19 071b4dc 4c2e7c7 0ef0274 05924e6 6ffb329 7f07cfe 57f1e86 8f99537 92a66b7 11bbbb0 eb1f5f0; do git -C /tmp/nss-bundle-test cat-file -e $h^{commit} && echo ok || echo FEHLT $h; done | sort | uniq -c
rm -rf /tmp/nss-bundle-test
```
Erwartet: `verify` okay; Tar-Zähler 20 und 2 (`.claude/` bewusst nicht gesichert); `21 ok`.

**Schritt 2A – GitHub (`GO CODE-SICHERUNG SCHRITT 2A`, ausgeführt 20:03 UTC):**
```
cd /opt/new-signal-system
for b in $(git for-each-ref --format='%(refname)' refs/heads); do [ -n "$(git rev-list --max-count=1 $b --not --remotes)" ] && echo "$b:refs/heads/offhost-backup/${b#refs/heads/}"; done > /root/backup-code/push.specs
cat /root/backup-code/push.specs
git push origin $(cat /root/backup-code/push.specs)
```
Nachweis von mir: Fetch + `cat-file` aller 21 Hashes (L5, erbracht).

**Schritt 2B – Windows `D:` (nicht GO-pflichtig, ausgeführt):** Bundle und beide Tars nach `D:\CT109-Backup\code-2026-10-22\`; `Get-FileHash` gegen `SHA256SUMS` des Hosts: **alle drei vollständig gleich (L3).**
**Nachweis insgesamt:** Schritt 1 (L3), 2A (L5), 2B (Hash gleich, L3) – **Code-Verlustlücke geschlossen.** Nicht erbracht: Restore auf Windows (`git bundle verify`/Clone, L8) – optional.

**E1 – Ergebnis (22.10. 19:41:47 UTC, L3, ausgewertet):** 21 ungepushte Commits (alle auch nicht auf GitHub, L5), Stash leer, 23 Dirty-Dateien (20 `lernbot-step7` auf detached HEAD `880223b`, 2 `perp-l2`, 1 `/opt/new-signal-system`), Repo 8,40 MiB lose. Details und Hash-Liste: `01` §1.

**Auftrag E1b – Namen der 23 Dirty-Dateien (ausgeführt):**
```
date -u
for w in /opt/new-signal-system /root/wt/lernbot-step7-2026-10-17 /root/wt/perp-l2-2026-10-19; do echo "== $w"; git -C "$w" status --short; git -C "$w" status --short | awk '{print $2}' | while read f; do stat -c '%s B  %y  %n' "$w/$f" 2>/dev/null; done; done
```
**Auftrag E3 – Secret-Zählscan der 21 Commits + Dirty-Dateien (ausgeführt; gibt nur Anzahl je Muster und Dateinamen aus, NIE die Treffer):**
```
cd /opt/new-signal-system
git log --branches --not --remotes -p 2>/dev/null | grep -Ec 'BEGIN [A-Z ]*PRIVATE KEY|AGE-SECRET-KEY|(api|secret|token|passw)[a-z_]*[ ]*[=:][ ]*["'"'"'][A-Za-z0-9/+_=-]{16,}'
git log --branches --not --remotes --name-only --pretty=format: | sort -u | grep -Ei '\.(env|key|pem|p12|sqlite|db|age)$|secret|credential|token'
for w in /root/wt/lernbot-step7-2026-10-17 /root/wt/perp-l2-2026-10-19 /opt/new-signal-system; do echo "== $w"; (cd "$w"; git status --short | awk '{print $2}' | xargs -r grep -EIl 'BEGIN [A-Z ]*PRIVATE KEY|AGE-SECRET-KEY|(api|secret|token|passw)[a-z_]*[ ]*[=:][ ]*["'"'"'][A-Za-z0-9/+_=-]{16,}'); done
```
Lesart: Zahl `0` und leere Listen = heuristisch sauber (kein Beweis; Muster begrenzt). Treffer → Dateiname melden, Inhalt nie in den Chat.
**E1b/E3 – Ergebnis (22.10. 19:47 UTC, L3, ausgewertet):** Dirty-Dateien benannt (`01` §1, Zeile „Dirty-Arbeit“); E3: 0 Secret-Treffer in Diff und Dirty-Dateien, keine verdächtigen Dateinamen (Heuristik, kein Beweis; `.claude/` ungeprüft). GitHub: kein Workflow im Repo (kein CI-Lauf durch Pushes), Repo privat (L5).
**Auftrag E1c – Hashabgleich der Dirty-Dateien gegen den GitHub-Stand (ausgeführt):**
```
cd /root/wt/lernbot-step7-2026-10-17
for f in $(git status --short | awk '{print $2}'); do h=$(git hash-object "$f"); g=$(git rev-parse -q --verify 4db7110:"$f" 2>/dev/null); [ "$h" = "$g" ] && echo "GLEICH $f" || echo "ANDERS/NEU $f"; done
ls -la /opt/new-signal-system/.claude; grep -rEIl 'BEGIN [A-Z ]*PRIVATE KEY|AGE-SECRET-KEY|(api|secret|token|passw)[a-z_]*[ ]*[=:][ ]*["'"'"'][A-Za-z0-9/+_=-]{16,}' /opt/new-signal-system/.claude
git -C /opt/new-signal-system remote -v | sed 's#//[^@/]*@#//***@#'
```
(Die `remote -v`-Ausgabe aus E1c wurde damals nicht dokumentiert; E2 hat sie nachgeliefert: SSH-Remote.)

### 5c. GO REGISTRY-SICHERUNG (R1) – **ERTEILT und AUSGEFÜHRT 22.10. 20:37 UTC, PASS** (Schablone `02` §3)
1. **Befehl (CT109, root):**
```
date -u; hostname
D=$(date -u +%Y%m%dT%H%M%SZ)
install -d -o signalsvc -g signalsvc -m 0700 /var/backups/ct109-meta
runuser -u signalsvc -- python3 -c 'import sqlite3,sys; s=sqlite3.connect("file:/var/lib/new-signal-system/meta.sqlite?mode=ro",uri=True); d=sqlite3.connect(sys.argv[1]); s.backup(d); d.close(); s.close()' /var/backups/ct109-meta/meta-$D.sqlite
runuser -u signalsvc -- python3 -c 'import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); print(c.execute("pragma integrity_check").fetchall()); c.close()' /var/backups/ct109-meta/meta-$D.sqlite
sha256sum /var/backups/ct109-meta/meta-$D.sqlite
ls -la /var/backups/ct109-meta /var/lib/new-signal-system | head -30
```
2. **Zweck:** konsistente Kopie der aktuellen `meta.sqlite` per SQLite-Online-Backup-API, als DB-Besitzer `signalsvc`, Quelle nur lesend. **Nicht Zweck:** Registry-Schreiben, Entsiegeln, Löschen, Dienständerung.
3. **Risiken:** kurze Lesetransaktion auf der Live-DB (≈ 5,8 MB); WAL-Nebenwirkungen (Incident 114) vermieden (kein Root-Zugriff auf die DB, Besitzer `signalsvc`, `mode=ro`); ≈ 6 MB zusätzlich auf der Root-LV; die Kopie auf der LV schützt nur vor logischem Fehler – der Schutz vor LV-Verlust entsteht durch die Kopie nach `D:`.
4. **Rollback:** `rm -r /var/backups/ct109-meta` (nur dieses neue Verzeichnis; nicht benötigt).
5. **Abbruch:** Python-Fehler; `integrity_check` ≠ `[('ok',)]`; Kopie < 5 MB; Besitzer/Modus von `meta.sqlite*` verändert.
6. **GO-Satz:** `GO REGISTRY-SICHERUNG – R1` (Andi, 22.10. 22:37 Berlin / 20:37 UTC).
7. **Ergebnis (L3, Originalscreenshot des Owners):** Host `new-signal-system`; `[('ok',)]`; Kopie `/var/backups/ct109-meta/meta-20261022T203753Z.sqlite`, 5 812 224 B (gleich groß wie `meta.sqlite`), Besitzer `signalsvc`, Modus 0644 im Verzeichnis 0700 (`drwx------`); **SHA-256 `069f6a1dbe634de0f3640c1d39bde378b18877ea14a8cb7a8ede83de04f2bdeb`**. Original unverändert: `meta.sqlite` `signalsvc` 0644, `-wal` 4 148 872 B (wie E2), `-shm` 32 768 B (Zeitstempel 20:34/20:37 = Live-Betrieb). Keine Fehlermeldung sichtbar (die `date -u`-Zeile ist im Screenshot abgeschnitten; Zeit aus dem Dateinamen).
8. **Kopie nach `D:` (Owner-Angabe, 22.10. ≈ 22:39 Berlin, L1):** SHA-256-Vergleich Windows ↔ Host: „passt“. Originalausgabe der Windows-Hashprüfung liegt dem Einsatzleiter nicht vor (daher L1, nicht L3).
9. **Grenzen:** Kein Restore (Öffnen auf anderer Maschine) und kein Zeilenabgleich gegen das Original erbracht. Keine tägliche Sicherung; Registry wächst weiter.
10. **Folge (nicht erteilt):** **GO R2** = täglicher Timer (nach Archivlauf, nicht in :05–:10) mit derselben Methode, Rotation (z. B. 14 Stück), Kopie nach `D:` weiterhin manuell. Entwurf folgt als eigene Host-Schreibaktion mit vollständiger Schablone.

### 5i. GO G2 – Gateway wieder starten und Collector anschließen (**erteilt und ausgeführt 23.10. 15:51–15:53 Berlin, Ergebnis OK, `02`/`01`**; ursprünglicher ENTWURF 23.10. ≈ 15:52 Berlin; Schablone `02` §3; Anlass: G1 endete mit gestopptem Gateway)
**Befund G1 (Andis Screenshots 13:43–13:49 UTC, L3):** Schritt 1 lief 13:43:05, Schritt 2 wurde versehentlich im selben Einfügen ausgeführt und startete `signal-ibkr` deshalb korrekt **nicht** (Log noch ohne „Ergebnis“). **IBC-Log: `Login dialog … LOGGED_OUT` 13:43:09, `Login has completed` 13:43:12; `ibgateway` active, Port 4002 `LISTEN` (13:47:52).** `first-login.sh` meldete trotzdem **`Ergebnis: TIMEOUT`**, **stoppte das Gateway** (`GESTOPPT`, Exit 1) und beendete sich vor meinem `kill` (13:48:51); danach `ibgateway` und `signal-ibkr` `inactive`. **Ursache der Fehlerkennung UNKNOWN** (Skript prüft `tail -n +<Zeilenzahl vor dem Start>` der Tagesdatei; warum „Login has completed“ nicht gefunden wurde, nicht geklärt). IBKR-Kollektoren stehen seit 13:43 UTC (geplante Lücke, Marker 10 min). Der Login selbst war erfolgreich (kein Lockout-Risiko durch den ersten Versuch).
1. **Befehl (CT109, root; nicht in den Minuten :05–:10):** SHA-256 (LF, ein Zeilenumbruch am Ende) `f59286537a3cac130a3a38ff84ad84cea3af22ab9ee98431048865afb8a3da73`.
```
date -u; hostname
echo "vorher:"; systemctl is-active ibgateway signal-ibkr
if systemctl is-active --quiet ibgateway; then
  echo "ABBRUCH: ibgateway laeuft bereits, nichts getan"
else
  touch /var/lib/new-signal-system/planned
  L=/var/log/ibgateway/ibc-$(cat /opt/ibc/version)_GATEWAY-1050_$(LC_ALL=C date +%A).txt
  T0=$(date -u '+%Y-%m-%d %H:%M:%S')
  systemctl start ibgateway.service
  R=TIMEOUT
  for i in $(seq 24); do
    sleep 5
    F=$(grep -aE 'Cold restart after|Login Error dialog encountered|Too many failed login' "$L" 2>/dev/null | tail -1 | cut -c1-19)
    if [ -n "$F" ] && [[ "$F" > "$T0" ]]; then R=FEHLER; break; fi
    X=$(grep -a 'Login has completed' "$L" 2>/dev/null | tail -1 | cut -c1-19)
    if [ -n "$X" ] && [[ "$X" > "$T0" ]] && ss -ltn | grep -q ':4002'; then R=OK; break; fi
  done
  echo "Ergebnis: $R"
  if [ "$R" = OK ]; then
    systemctl start signal-ibkr
    sleep 75
    date -u; systemctl is-active ibgateway signal-ibkr
    cd /opt/new-signal-system && nice -n19 scripts/status-report --since "5 min ago"
  elif [ "$R" = FEHLER ]; then
    systemctl stop ibgateway.service; systemctl reset-failed ibgateway.service
    echo "GESTOPPT wegen Login-Fehler, signal-ibkr NICHT gestartet"
  else
    echo "TIMEOUT: Gateway bleibt UNVERAENDERT laufen, signal-ibkr NICHT gestartet, bitte Ausgabe an Claude"
    systemctl is-active ibgateway; ss -ltn | grep 4002
  fi
fi
```
2. **Zweck:** Gateway wie vor G1 wieder betriebsbereit machen und `signal-ibkr` anschließen. Die Erfolgsprüfung läuft **nicht** über `first-login.sh`, sondern über `Login has completed` mit Zeitstempel nach dem Start **und** Port 4002. **Nicht Zweck:** Config, Code, Abos, Löschen; Ursache des Skriptfehlers beheben.
3. **Risiken:** Zweiter Login binnen Minuten (der erste war erfolgreich; bei `FEHLER` stoppt der Block das Gateway sofort, kein weiterer Versuch). Bei `TIMEOUT` (120 s) bleibt das Gateway **unverändert laufen**, `signal-ibkr` wird nicht gestartet, Mensch entscheidet. Depth/tbt bleiben bis zum Start des Collectors aus; Datenlücke seit 13:43 UTC (geplant/markiert, Marker 10 min, danach `own:process` bzw. ungeplant möglich). Keine Wirkung auf den kritischen Pfad.
4. **Sicherung/Rollback:** Nichts zu sichern; Rollback = `systemctl stop signal-ibkr ibgateway`. **Getestet:** nur Shell-Logik mit Attrappen (OK, Login-Fehler, Timeout, Gateway läuft bereits); nicht auf CT109.
5. **Abbruchkriterien:** `ABBRUCH`, `Ergebnis: FEHLER`, `Ergebnis: TIMEOUT`, `ibgateway` nicht `active` nach dem Start, tbt-Lücken nach dem Start länger als 3 min offen.
6. **Nachweis:** `Ergebnis: OK`, `active active`, Status-Report ohne offene `*:tbt`-Lücke (oder mit frischen, geschlossenen Lücken).
7. **Satz von Andi:** `GO G2 – f5928653` (oder „GO“ als Antwort auf diesen einzigen offenen GO-Text).

### 5h. GO G1 – Gateway-Neustart wegen tbt-Ausfall (ENTWURF 23.10. ≈ 15:45 Berlin, **nicht erteilt**; Schablone `02` §3)
**Grundlage:** Auftrag B2 (§5g), Bericht von Claude Code 13:39 UTC (L2, Screenshot): `ibgateway` und `signal-ibkr` laufen seit 19.10. 09:43:17, `NRestarts=0`; offene Lücken 1685–1687 (`NVDA/INTC/TSLA:tbt`, `stale`, Beginn 13:30:00); Depth läuft (Spool wächst sekundengenau, keine Depth-Lücken); **kein einziger Fehlercode seit 13:00**; Neu-Abos #1–#3 um 13:31, 13:33, 13:37 (reqId 19–27) ohne Wirkung. **16.10. identisches Bild** (Alarm 13:31:00, sieben Neu-Abos bis 14:15, keine tbt-Fehlercodes); dort stoppte Andi `signal-ibkr` 14:18 (**ohne Wirkung**), der **Gateway-Neustart ≈ 14:50 stellte tbt wieder her** (Quelle: Memory-Eintrag laut Claude Code, L1; Andi 23.10.: „nur Neustart vom Gateway half, glaube ich“). Ursache beider Fälle UNKNOWN. Beide Tage hatten vor dem Handelsbeginn einen US-Farm-Break (16.10. 12:46/12:52, heute 04:17 und 11:09:28) mit proaktiven Neu-Abos; ob tbt danach vor 13:30 lief, ist **nicht gemessen** (`check_fresh` prüft erst ab Handelsbeginn).
1. **Befehl (CT109, root, nicht in den Minuten :05–:10; zwei Schritte, Schritt 2 erst nach „Ergebnis: OK“ im Log; Block als Ganzes gehasht):** SHA-256 (LF, ein Zeilenumbruch am Ende) `b36516ff40a0b91810d2750ad0131c1fe3a77f0eaa742b887fa37facb62a8f41`.
```
# --- SCHRITT 1 (CT109, root; nicht in den Minuten :05 bis :10) ---
date -u; hostname
if cd /opt/new-signal-system && systemctl cat signal-ingestion.service > /dev/null 2>&1; then
  echo "vorher:"; systemctl is-active ibgateway signal-ibkr
  touch /var/lib/new-signal-system/planned
  systemctl stop signal-ibkr
  systemctl stop ibgateway
  echo "nach Stopp:"; systemctl is-active ibgateway signal-ibkr
  nohup bash scripts/ibkr-first-login.sh > /tmp/first-login.log 2>&1 &
  sleep 45
  cat /tmp/first-login.log
else
  echo "ABBRUCH: Verzeichnis oder signal-ingestion.service fehlt, nichts gestoppt"
fi
# --- SCHRITT 2 (erst wenn im Log "Ergebnis: OK" steht) ---
cat /tmp/first-login.log
if grep -q "Ergebnis: OK" /tmp/first-login.log; then
  systemctl start signal-ibkr
  sleep 75
  date -u; systemctl is-active ibgateway signal-ibkr
  cd /opt/new-signal-system && nice -n19 scripts/status-report --since "5 min ago"
else
  echo "signal-ibkr NICHT gestartet: Login nicht OK"
fi
```
2. **Zweck:** `signal-ibkr` geplant stoppen (Marker `planned`), `ibgateway` stoppen und über `scripts/ibkr-first-login.sh` neu anmelden (Paper, bisher ohne Zweitfaktor), danach `signal-ibkr` starten. Ziel: tbt-Lieferung für NVDA/INTC/TSLA wieder herstellen. **Nicht Zweck:** Ursache beheben, Konfiguration (`/opt/ibc/config.ini`, `secrets.env`, `ibkr.env`) oder Code ändern, Git, Abos ändern, Löschen.
3. **Risiken:** Depth und tbt fallen für ca. 2–4 Minuten aus (als `planned=1`-Lücken erfasst). Ein fehlgeschlagener Login zählt gegen die Kontosperre; das Skript stoppt das Gateway beim ersten Fehler, **kein zweiter Versuch ohne Rücksprache**. Bleibt das Gateway dann gestoppt, schweigen alle IBKR-Kollektoren, bis ein Mensch eingreift (Aktien-Spur, nicht der kritische Pfad). `first-login.sh` deaktiviert `signal-ingestion` (Altlast, laut Skript); der Vorlauf bricht ab, falls die Unit unbekannt ist. Auch nach dem Neustart kann tbt tot bleiben (dann ist „Gateway-Zustand“ als Ursache widerlegt). Daten des Tages sind versiegelt (IBKR ab 12.10.) und werden nicht angefasst.
4. **Sicherung/Rollback:** Nichts zu sichern außer dem Journal (bleibt in `journald`; B2-Bericht ist in `01`/`04` festgehalten). Rollback = derselbe Ablauf (kein Zustand geändert). **Getestet:** nur Shell-Logik in der Sandbox mit Attrappen (OK-Pfad, Guard-Pfad, Login-Fehler-Pfad: kein Start des Collectors bei Fehler); **nicht getestet:** reale Ausführung des Blocks; der Ablauf entspricht `RUNBOOK.md` (Eingriff am Gateway, 05.10. gemessen).
5. **Abbruchkriterien:** Ausgabe `ABBRUCH`; im Log `FEHLER`, `TIMEOUT` oder `GESTOPPT`; `Ergebnis` nicht `OK`; `ibgateway` nicht `active` nach Schritt 2; keine Lücken 1685–1687 geschlossen und weiter keine tbt-Zeilen 3 min nach dem Start (dann kein zweiter Neustart, Meldung an mich).
6. **Nachweis (Originalausgabe von Andi):** `Ergebnis: OK`, danach `active active` und der Status-Report mit geschlossenen Lücken 1685–1687 (oder neuen, kurzen, geplanten Lücken) und ohne offene `*:tbt`-Lücke.
7. **Satz von Andi:** `GO G1 – b36516ff`.

### 5g. Auftrag B2 – IBKR-tbt-Ausfall 23.10. (lesend, als Claude-Code-Prompt auf CT109; ausgegeben 23.10. ≈ 15:40 Berlin, Ausgabe **offen**)
Anlass: HA-Alarme 15:31/15:33 Berlin (`01`, 13:36 UTC). Ersetzt den kurzen Bash-Block aus der Chat-Antwort 15:36 Berlin. Datenzugriff nur Metadaten (IBKR-Tage ab 12.10. versiegelt, `RUNBOOK.md` Datensiegel).
```
AUFTRAG B2 – IBKR-tbt-Ausfall 23.10.2026 (nur lesen, danach STOPP)

REGELN (gelten für alles unten):
- Nur lesen. Kein Neustart, kein start/stop/reload/enable von Units, kein sed/Schreiben in /etc oder /opt, kein git commit/merge/checkout, keine Datei anlegen außer einer Notizdatei unter /tmp, keine Orders, keine neuen API-Abos, kein Gateway-Login.
- Keine Dateiinhalte von Spool, Parquet oder SQLite lesen (Preise, Ticks, Bücher). Von Datendateien nur Name, Größe, mtime (ls -l --time-style=full-iso, stat). IBKR-Tage ab 12.10. sind versiegelt; kein Analysepfad, kein scripts/analysis-run, kein collector.measure.
- Kein IBC-Log, kein secrets.env, keine ibkr.env außer den Zeilen IBKR_DEPTH= und IBKR_TICKS=. Keine Kontonummern, URLs oder Zugangsdaten ausgeben.
- Nicht in den Minuten :05 bis :10 jeder Stunde (UTC) laufen lassen.

AUFGABE:
1. date -u, systemctl show signal-ibkr ibgateway (ActiveState, MainPID, NRestarts, ActiveEnterTimestamp). scripts/status-report --since "60 min ago" (Aufruf aus /opt/new-signal-system).
2. Zeitlinie aus journalctl -u signal-ibkr ab 2026-10-23 13:00 UTC: Sessionstarts/-enden, tbt-Abos (reqId, Symbol, Uhrzeit), fresh/re-subscribed (Zeiten, Zähler), jeder Error-/Warning-Code (insbesondere 2103–2108, 2119, 2157, 2158, 1100–1102, 321, 322, 10089, 10167, 10189, 10190, 10197, tbt_limit, tbt_deferred), disconnect. Zeilen auf 220 Zeichen kürzen.
3. Spool-Aktivität nur per mtime/Größe: für NVDA, INTC, TSLA (Kanäle tbt und depth, soweit aus dem Dateinamen erkennbar) letzte Änderung der heutigen Dateien. Ergebnis in Worten: fließen Depth bzw. tbt-Zeilen seit 13:30 UTC ja/nein/unklar?
4. Dasselbe Muster am 16.10. (ca. 12:30–15:00 UTC), falls im Journal noch vorhanden: gleiche Codes und Reihenfolge ja/nein.
5. Code lesen (src/collector/ibkr.py: check_fresh, stale, resubscribe, on_error, Fehlerfilter, reqId-Vergabe, Cancel vor Neu-Abo): Welche Fehler werden nicht protokolliert? Wird vor jedem Neu-Abo gecancelt? Können reqIds doppelt vergeben werden?
6. Matrix je Hypothese: (a) Error-Handler verschluckt Ablehnungen, (b) Zombie-Abos/Limit (tbt_limit, 10190), (c) doppelte reqId (322), (d) Sitzungskonflikt (10197), (e) Verlust der tbt-Abos nach Farm-Reconnect, (f) Gateway-interner tbt-Zustand hängt, (g) serverseitig kein tbt. Je Hypothese: Beleg dafür, Beleg dagegen, Kennzeichnung [gemessen] / [Code] / [Annahme] / [unklar].

AUSGABE: Fakten zuerst, dann Matrix, dann „welche eine lesende Messung trennt die verbleibenden Hypothesen am besten“. Keine Änderungsvorschläge ohne Begründung, keine Umsetzung. Danach STOPP.
```

### 5f. GO H1 – Sicherung der Host-only-Arbeit (ENTWURF 23.10. ≈ 15:20 Berlin, **erteilt 15:22 Berlin laut Andi, Satz `GO H1 – 8aa8844`**; Schablone `02` §3)
**Grundlage E4b (Andi, 23.10. 13:17 UTC, L3, Screenshots):** `/root/run` ohne `tmp-ro`/`fv`: **134 549 504 B (≈ 128 MiB), 7 504 Dateien** (ohne `.git`, `__pycache__`). Secret-Muster-Zähler: **369 Dateien**; die Namensliste fehlt, weil `tee /dev/stderr` in Andis Terminal „Permission denied“ meldete (Fehler meines Auftrags). Der Zähler zeigt nur Kandidaten (breites Muster, u. a. „secret“, „password“), kein Beweis. Sensible Dateinamen: nur `config.ini` und `secrets.env.example` (in Repo-Kopien unter `deploy/ibc/`, `deploy/`), dazu sehr viele `opt/ibc/config.ini` in Test-Verzeichnissen `tmp-paper/test_*` (Test-Artefakte); keine `*.env`, `*.pem`, `*.key` unter `/root/run`. Ledger: `shadow-live.sqlite` 4 096 B (2×, 17.10.), `shadow-run2-copy.sqlite` 1 765 376 B (19.10., `/root/run`), **Original `/var/lib/private/lernbot/shadow.sqlite` 1 765 376 B (19.10.)**. Gleiche Größe wie die Kopie, Inhaltsgleichheit nicht geprüft.
1. **Befehl (CT109, root, Arbeitsverzeichnis egal; nicht in den Minuten :05–:10; beim Einfügen aus dem Chat auf Zeilenumbrüche achten, `PYEOF` steht auf eigener Zeile):** SHA-256 des Blocks (Datei mit LF-Zeilenenden und einem Zeilenumbruch am Ende) `8aa8844a020a3d67babea82216e3529e1b462125949771b0eae22644c7fafcb2`.
```
date -u; hostname; id -un
nice -n19 ionice -c3 python3 -I - <<'PYEOF'
import fnmatch, hashlib, os, re, shutil, sqlite3, stat, sys, tarfile, time
DST = "/var/backups/ct109-hostwork"
ROOTS = ["/root/run", "/root/wt"]
TOPDIR = "/root"
LEDGER = "/var/lib/private/lernbot/shadow.sqlite"
PRUNE = {"tmp-ro", "fv", "tmp-paper", ".git", "__pycache__", ".pytest_cache", "node_modules"}
BADNAME = ("*.env", "*.env.*", "*.pem", "*.key", "config.ini", "*secret*", "*credential*", "ibkr.env*")
TOPNAME = ("*.md", "*.patch", "*.bak")
CAP = 50 * 1024 * 1024
SECRET = re.compile(rb"BEGIN [A-Z ]*PRIVATE KEY|AGE-SECRET-KEY|(?:api|secret|token|passw)[a-z_]*[ ]*[=:][ ]*.[A-Za-z0-9/+_=-]{16,}", re.I)
os.umask(0o077)
os.makedirs(DST, mode=0o700, exist_ok=True)
if shutil.disk_usage(DST).free < 500 * 1024 * 1024:
    print("ABBRUCH: weniger als 500 MB frei"); sys.exit(2)
stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
inc, exc, skipped = [], [], 0
def bad(n):
    n = n.lower()
    return any(fnmatch.fnmatch(n, p) for p in BADNAME)
def consider(p):
    global skipped
    st = os.lstat(p)
    if not stat.S_ISREG(st.st_mode):
        skipped += 1
        return
    if bad(os.path.basename(p)):
        exc.append(("name", p, st.st_size)); return
    if st.st_size > CAP:
        exc.append(("size", p, st.st_size)); return
    try:
        data = open(p, "rb").read()
    except OSError as e:
        exc.append(("unreadable", p, st.st_size)); return
    if SECRET.search(data):
        exc.append(("secretscan", p, st.st_size)); return
    inc.append((p, st.st_size, hashlib.sha256(data).hexdigest()))
for r in ROOTS:
    for d, ds, fs in os.walk(r):
        ds[:] = sorted(x for x in ds if x not in PRUNE and not os.path.ismount(os.path.join(d, x)))
        for f in sorted(fs):
            consider(os.path.join(d, f))
for f in sorted(os.listdir(TOPDIR)):
    p = os.path.join(TOPDIR, f)
    if any(fnmatch.fnmatch(f.lower(), t) for t in TOPNAME) and os.path.isfile(p):
        consider(p)
tar_path = os.path.join(DST, "hostwork-%s.tar.gz" % stamp)
tmp = tar_path + ".part"
with tarfile.open(tmp, "w:gz") as t:
    for p, size, h in inc:
        t.add(p, arcname=p.lstrip("/"), recursive=False)
with tarfile.open(tmp, "r:gz") as t:
    n = len(t.getnames())
if n != len(inc):
    os.remove(tmp); print("ABBRUCH: Tar-Eintraege", n, "erwartet", len(inc)); sys.exit(3)
os.rename(tmp, tar_path)
th = hashlib.sha256(open(tar_path, "rb").read()).hexdigest()
open(tar_path + ".sha256", "w").write("%s  %s\n" % (th, os.path.basename(tar_path)))
with open(os.path.join(DST, "MANIFEST-%s.tsv" % stamp), "w") as m:
    for p, size, h in inc:
        m.write("%d\t%s\t%s\n" % (size, h, p))
with open(os.path.join(DST, "EXCLUDED-%s.tsv" % stamp), "w") as m:
    for why, p, size in exc:
        m.write("%s\t%d\t%s\n" % (why, size, p))
print("OK tar", tar_path, os.path.getsize(tar_path), "B sha256", th)
print("eingeschlossen", len(inc), "Dateien,", sum(x[1] for x in inc), "B roh; uebersprungen (keine regulaere Datei)", skipped)
for why in ("name", "size", "unreadable", "secretscan"):
    print("ausgeschlossen", why, sum(1 for e in exc if e[0] == why))
for why, p, size in exc:
    if why in ("secretscan", "size", "unreadable"):
        print("  AUSGESCHLOSSEN", why, size, p)
try:
    s = sqlite3.connect("file:%s?mode=ro" % LEDGER, uri=True)
    out = os.path.join(DST, "lernbot-shadow-%s.sqlite" % stamp)
    d = sqlite3.connect(out)
    s.backup(d); d.close(); s.close()
    c = sqlite3.connect(out); res = c.execute("pragma integrity_check").fetchall(); c.close()
    oh = hashlib.sha256(open(out, "rb").read()).hexdigest()
    open(out + ".sha256", "w").write("%s  %s\n" % (oh, os.path.basename(out)))
    print("Ledger-Kopie", out, os.path.getsize(out), "B integrity", res, "sha256", oh)
except Exception as e:
    print("Ledger-Kopie FEHLGESCHLAGEN:", type(e).__name__, str(e)[:200])
PYEOF
echo "exit=$?"
cd /var/backups/ct109-hostwork && ls -la --time-style=long-iso && sha256sum -c "$(ls -t hostwork-*.tar.gz.sha256 | head -1)"
```
2. **Zweck:** Eine Tar-Sicherung der Host-only-Arbeit (Paper-Harness `r/src|tests|docs|deploy/paper`, Lernbot-Skripte, Auswertungen, `/root/wt`, `/root/*.md|*.patch|*.bak`) plus eine konsistente Kopie des Lernbot-Ledgers, abgelegt neu unter `/var/backups/ct109-hostwork/` (Rechte 0700/0600). Danach kopiert Andi die Dateien von Hand nach `D:` und vergleicht Hashes (kein GitHub-Push vom Host). **Ausgeschlossen:** Verzeichnisse `tmp-ro`, `fv`, `tmp-paper`, `.git`, `__pycache__`, `.pytest_cache`, `node_modules`; Namen `*.env`, `*.env.*`, `*.pem`, `*.key`, `config.ini`, `*secret*`, `*credential*`, `ibkr.env*`; jede Datei, in der das strenge Secret-Muster (Schlüsselblock oder `api|secret|token|passw…` = Literal ab 16 Zeichen, ohne Groß/Klein) trifft; Dateien über 50 MB. Nicht angefasst: `.bash_history`, `/root/.claude*`, `/root/*.txt`, Datenverzeichnisse, Registry, Siegel. **Nicht Zweck:** Löschen, Verschieben oder Ändern irgendeiner Quelldatei, Entsiegeln, Registry-Schreiben, Dienststart, Git-Operationen.
3. **Risiken:** Last gering (≈ 128 MiB lesen, `nice 19`/`ionice idle`); Platz auf der Root-LV: Abbruch bei < 500 MB frei. Secrets: Das Secret-Muster ist heuristisch; ein Treffer schließt die Datei aus und wird nur mit Namen ausgegeben, ein Nichttreffer ist kein Beweis. Das Tar bleibt 0600 root auf dem Host, bis Andi es auf `D:` kopiert. `.git` fehlt bewusst (mögliche Remote-URLs/Tokens); die Historie liegt auf GitHub, der Paper-Harness hatte nie einen Commit (E4). Ledger-Kopie: Lernbot-Dienst lief laut Order B nicht (nicht in der Dienstliste, Schluss aus Fehlen); Lesen mit `mode=ro` kann bei WAL-Dateien scheitern, dann steht `FEHLGESCHLAGEN` in der Ausgabe und die Tar-Sicherung bleibt gültig.
4. **Sicherung/Rollback:** Es wird nichts verändert außer dem neuen Verzeichnis `/var/backups/ct109-hostwork/`. Rollback = dieses Verzeichnis entfernen (Löschen ist ein eigenes GO, Rest stört nicht). **Getestet in der Sandbox** (23.10. 13:20 UTC) gegen einen künstlichen Baum mit `tmp-paper`, `tmp-ro/fv`, `.git`, `config.ini`, `secrets.env.example`, `secrets.env.bak` (Top-Level), Datei mit Token-Literal (2 Varianten), Symlink, Binärdatei, `.bash_history`, SQLite-Ledger: alle Ausschlüsse griffen, Tar-Eintragszahl = Manifest, `sha256sum -c` OK, Ledger-`integrity_check` ok. **Nicht getestet:** Lauf auf CT109 (Python 3.11.2 dort, Sandbox 3.13), Verhalten bei WAL-Ledger.
5. **Abbruchkriterien:** Ausgabe `ABBRUCH` (Platz, Tar-Eintragszahl), Exit ≠ 0, `sha256sum -c` nicht OK, Tar kleiner als 100 KB (Harness allein ≈ 340 KB roh), oder eine geänderte Quelldatei (dieser Befehl schreibt nur nach `ct109-hostwork`).
6. **Nachweis nach Ausführung (Andi gibt die Originalausgabe zurück):** Zeile `OK tar … B sha256 …`, Zähler `eingeschlossen`/`ausgeschlossen name|size|unreadable|secretscan`, die Liste `AUSGESCHLOSSEN secretscan …` (nur Namen), Zeile `Ledger-Kopie … integrity [('ok',)]`, `exit=0`, `sha256sum -c … OK`. Danach: Entscheid, ob ausgeschlossene Treffer Fehlalarme sind (Namen ansehen, Inhalt nie ausgeben); Kopie nach `D:` und Hashvergleich durch Andi.
7. **Satz von Andi:** `GO H1 – 8aa8844a`. Gilt nur für diesen Block.

### 5e. GO R2 – tägliche Registry-Sicherung (ENTWURF 23.10. 15:05 Berlin, **nicht erteilt**; Schablone `02` §3)
1. **Befehl (CT109, root, Arbeitsverzeichnis egal; beim Einfügen aus dem Chat auf Zeilenumbrüche achten, die Heredocs `PYEOF`/`UNITEOF` müssen auf eigener Zeile stehen):** SHA-256 des Blocks (Datei mit LF-Zeilenenden und einem Zeilenumbruch am Ende) `78d7808ad653dfb39850e824c8d2b7d4e4ac481d55524276b440fd17cb2af0f1`.
```
date -u; hostname
cat > /usr/local/sbin/ct109-meta-backup.py <<'PYEOF'
#!/usr/bin/python3
import glob, hashlib, os, sqlite3, sys, time
SRC = "file:/var/lib/new-signal-system/meta.sqlite?mode=ro"
DST = "/var/backups/ct109-meta"
KEEP = 14
stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
out = os.path.join(DST, "meta-%s.sqlite" % stamp)
tmp = out + ".part"
s = sqlite3.connect(SRC, uri=True)
t = sqlite3.connect(tmp)
s.backup(t)
t.close()
s.close()
c = sqlite3.connect(tmp)
res = c.execute("pragma integrity_check").fetchall()
c.close()
if res != [("ok",)] or os.path.getsize(tmp) < 5000000:
    os.remove(tmp)
    print("ABBRUCH", res)
    sys.exit(2)
os.rename(tmp, out)
h = hashlib.sha256(open(out, "rb").read()).hexdigest()
open(out + ".sha256", "w").write("%s  %s\n" % (h, os.path.basename(out)))
for f in sorted(glob.glob(os.path.join(DST, "meta-*.sqlite")))[:-KEEP]:
    os.remove(f)
    if os.path.exists(f + ".sha256"):
        os.remove(f + ".sha256")
print("OK", out, h)
PYEOF
chmod 0755 /usr/local/sbin/ct109-meta-backup.py
cat > /etc/systemd/system/ct109-meta-backup.service <<'UNITEOF'
[Unit]
Description=CT109 registry backup (SQLite online backup, read-only source, keeps 14)
[Service]
Type=oneshot
User=signalsvc
Group=signalsvc
Nice=19
IOSchedulingClass=idle
ExecStart=/usr/bin/python3 /usr/local/sbin/ct109-meta-backup.py
UNITEOF
cat > /etc/systemd/system/ct109-meta-backup.timer <<'UNITEOF'
[Unit]
Description=CT109 registry backup daily 04:27 UTC (outside compactor minutes 05-10)
[Timer]
OnCalendar=*-*-* 04:27:00 UTC
Persistent=false
AccuracySec=1s
[Install]
WantedBy=timers.target
UNITEOF
systemd-analyze verify /etc/systemd/system/ct109-meta-backup.service /etc/systemd/system/ct109-meta-backup.timer
systemctl daemon-reload
systemctl enable --now ct109-meta-backup.timer
systemctl start ct109-meta-backup.service
systemctl status ct109-meta-backup.service --no-pager | head -12
systemctl list-timers ct109-meta-backup.timer --no-pager
ls -la /var/backups/ct109-meta
sha256sum /usr/local/sbin/ct109-meta-backup.py /etc/systemd/system/ct109-meta-backup.service /etc/systemd/system/ct109-meta-backup.timer
```
2. **Zweck:** täglich (04:27 UTC, außerhalb der Compactor-Minuten 05–10 und des Archivlaufs 03:20) eine konsistente Kopie der `meta.sqlite` per SQLite-Online-Backup (Quelle `mode=ro`, Besitzer `signalsvc`, wie R1), Integritätsprüfung, SHA-256-Datei je Kopie, Rotation auf 14 Kopien; erste Kopie sofort. **Nicht Zweck:** Registry-Schreiben, Entsiegeln, Dienständerung an bestehenden Units, Kopie nach `D:` (bleibt manuell), Restore-Test.
3. **Risiken:** kurze Lesetransaktion auf der Live-DB (≈ 6 MB, Dauer Sekunden), `Nice=19` und `IOSchedulingClass=idle`; Platz ≈ 14 × 6 MB = 84 MB (wächst mit der Registry) auf der Root-LV; die Rotation löscht **nur** Dateien `meta-*.sqlite` (und deren `.sha256`) in `/var/backups/ct109-meta`, also ältere eigene Sicherungskopien (auch die R1-Kopie vom 22.10. fällt nach 14 Tagen heraus, ihre Kopie auf `D:` bleibt); kein Alarm bei Fehlschlag (Lücke: `OnFailure` bewusst nicht gesetzt, weil die bestehende Alarmvorlage nicht gelesen ist; Ersatz: tägliche Sichtkontrolle `ls -la /var/backups/ct109-meta`). Skript in der Sandbox gegen eine WAL-Testdatenbank geprüft (Kopie, Integrität, Hash, Rotation auf 14: Ergebnis wie erwartet, C/L6), nicht gegen die echte Registry und nicht auf CT109.
4. **Rollback (ungetestet):** `systemctl disable --now ct109-meta-backup.timer`; `rm /etc/systemd/system/ct109-meta-backup.service /etc/systemd/system/ct109-meta-backup.timer /usr/local/sbin/ct109-meta-backup.py`; `systemctl daemon-reload`. Die Kopien bleiben liegen.
5. **Abbruch:** jede Fehlermeldung von `systemd-analyze verify`; Ausgabe `ABBRUCH`; `Active:` nicht `inactive (dead)` mit `status=0/SUCCESS` für den Einmallauf; neue Kopie < 5 MB oder fehlt; Besitzer/Modus von `meta.sqlite*` verändert. Dann nichts weiter ausführen, Originalausgabe zurückgeben.
6. **Nachweis:** `OK /var/backups/ct109-meta/meta-<UTC>.sqlite <SHA-256>`, `Active: inactive (dead)` ohne Fehler, `list-timers` zeigt den nächsten Lauf 04:27 UTC, die Kopie und `.sha256` im Verzeichnis (Besitzer `signalsvc`), Hashes der drei neuen Dateien. Danach Kopie nach `D:` wie bei R1 (manuell, Hashvergleich).
7. **Satz von Andi:** `GO R2 – 78d7808a` (gilt nur für diesen Block, einmalig).

### 5d. D7 – Kraken-OHLCVT-Download (Andi, Windows PowerShell; Stand 23.10.)
**Quelle (L1, Support-Artikel 360047124832, WebFetch 23.10.):** fünf Teile `Kraken_OHLCVT_Full.zip.part00` bis `part04` (je ≈ 2 GB) unter `https://assets.kraken.com/marketing/institutions/`, Prüfsummen der Teile in `OHLCVT_Full_PARTS_SHA256SUMS.txt` (selber Ordner), erwarteter SHA-256 des zusammengesetzten ZIPs `bc273e9027470b07d790a7fa4df9bb43f0dfc527c20c6ecae48402e123e7b1c7`. Daten laut Artikel bis 30.06.2026 (gemessen: bis 30.09.2026, `01` §5.22). **Die Links nicht im Browser öffnen** (Hinweis der Seite), sondern mit `curl.exe` laden. Platzbedarf: Teile plus zusammengesetztes ZIP, also etwa das Doppelte der Gesamtgröße (mindestens 25 GB frei auf `D:`; sonst anderes Laufwerk und Pfad ersetzen).
**Regeln:** Datei **nicht entpacken, nicht öffnen, nicht in Excel laden**, keine Teile löschen. Rückmeldung an den Chat: nur die Ausgabe der Schritte 3 und 5 (Dateinamen, Bytes, OK/ABWEICHUNG, ZIP-Hash und ZIP-Größe). Fehler 416 von `curl` bei einem bereits vollständigen Teil ist harmlos.
Block 1 (als Block einfügen, die Zeilenumbrüche sind wichtig):
```
Get-PSDrive D | Select-Object Used, Free
New-Item -ItemType Directory -Force -Path D:\CT109-Data\kraken-ohlcvt | Out-Null
Set-Location D:\CT109-Data\kraken-ohlcvt
$base = "https://assets.kraken.com/marketing/institutions"
foreach ($n in "00","01","02","03","04") {
  curl.exe -L --fail -C - -o "Kraken_OHLCVT_Full.zip.part$n" "$base/Kraken_OHLCVT_Full.zip.part$n"
}
curl.exe -L --fail -o OHLCVT_Full_PARTS_SHA256SUMS.txt "$base/OHLCVT_Full_PARTS_SHA256SUMS.txt"
```
Block 2 (Schritt 3: Teile gegen die Kraken-Prüfsummen; erwartet fünfmal OK):
```
Set-Location D:\CT109-Data\kraken-ohlcvt
$sums = Get-Content .\OHLCVT_Full_PARTS_SHA256SUMS.txt
foreach ($f in Get-ChildItem .\Kraken_OHLCVT_Full.zip.part0*) {
  $h = (Get-FileHash $f.FullName -Algorithm SHA256).Hash.ToLower()
  $ok = [bool]($sums | Where-Object { $_.ToLower().Contains($h) -and $_.Contains($f.Name) })
  "{0}  {1} B  {2}" -f $f.Name, $f.Length, $(if ($ok) { "OK" } else { "ABWEICHUNG" })
}
```
Block 3 (nur wenn alle fünf OK; Schritt 4 Zusammenfügen, Schritt 5 Hash und Größe, dauert einige Minuten):
```
Set-Location D:\CT109-Data\kraken-ohlcvt
cmd /c copy /b Kraken_OHLCVT_Full.zip.part00+Kraken_OHLCVT_Full.zip.part01+Kraken_OHLCVT_Full.zip.part02+Kraken_OHLCVT_Full.zip.part03+Kraken_OHLCVT_Full.zip.part04 Kraken_OHLCVT_Full.zip
$z = Get-FileHash .\Kraken_OHLCVT_Full.zip -Algorithm SHA256
"{0}  {1} B" -f $z.Hash.ToLower(), (Get-Item .\Kraken_OHLCVT_Full.zip).Length
"gleich Kraken-Wert: " + ($z.Hash.ToLower() -eq "bc273e9027470b07d790a7fa4df9bb43f0dfc527c20c6ecae48402e123e7b1c7")
```
**Auswertung (vorab):** PASS nur bei fünfmal OK **und** `gleich Kraken-Wert: True`; sonst BLOCKED und Fallback nach `02` D10 (Trigger Sa 24.10. 10:00 UTC). Der Hash vergleicht nur mit dem Herstellerwert (L1 der Seite); er belegt Unversehrtheit des Downloads, nicht die Datenqualität (die prüft die Q-Prüfung am Sa).
**Ergebnis 23.10. ≈ 08:17 UTC: PASS** (fünfmal OK, ZIP 9 546 553 626 B, Hash gleich Kraken-Wert).
**Danach:** das Paket `CT109_BAU_lf1_v0.1.1_2026-10-23.zip` (SHA-256 `00efc5b64839a56deafb104a5fdbf9743a44647295c02fc32e221c5faa6c24da`; v0.1.0 ist ersetzt; **seit 23.10. ≈ 12:05 UTC gilt v0.5.0, SHA-256 `795abc1ff0cb2ed1cb9defa8075a472c433b8b4d9c3bb685a5d5ab7ebf75b4f8` [**auf dem PC bestanden: 170 Tests OK, Code-Hash `46239174…e2dd`, `feed-check ok`, 23.10. ≈ 12:17 UTC**; enthält `paper-eval`, Schattenmodus, `feed-check`, `deploy/DEPLOY.md`; v0.4.2 `56ab9786…fe84` war auf dem PC bestanden: 144 Tests OK, Code-Hash `3e708d6a…7726`, 23.10. ≈ 11:00 UTC, jetzt ersetzt; v0.4.1 ersetzt: Windows-Lauf 21 Aufräumfehler durch offene SQLite-Handles, in v0.4.2 behoben; v0.2.0 `7c0a4ca4…addf` ist auf dem PC getestet; v0.4.2 enthält `confirm`, `epoch-q`, Runner, Statusseite]; danach Auftrag E-Q: `epoch-q` auf BTC, nur Zähler, Rückgabe `out\q_epochs.json`**) nach `D:\CT109-Bau\` legen, Hash prüfen, `README_RUN.md` im Paket Abschnitt 0–1 ausführen (Tests, Selbstprüfung). Gate-Ablauf erst nach meinem Signal am Sa 24.10.

### 5j. Auftrag B3 – Periodizität der tbt-Ausfälle (Stand 23.10., Prompt folgt in der nächsten Runde)
**Frage (Andi, 23.10.):** Ist der Ausfall ein wöchentlicher IBKR-Prozess (beide Male Freitag, 16.10. und 23.10.)? **Status:** Annahme, nicht belegt (2 Datenpunkte; keine Quelle für einen Freitags-Prozess gefunden).
**Messung (nur lesend, Journal seit 14.10., keine Inhalte/Secrets):** je Tag (UTC) Anzahl US-Farm-Abbrüche (2103/2104/2119) vor 13:30 UTC, Zeitpunkte; Anzahl „ohne Daten“-Alarme/stale-Lücken je Titel; Startzeiten von `ibgateway`/`signal-ibkr`.
**Auswertung vorab:** Freitagsprozess gestützt nur, wenn Mo–Do keine tbt-Lücke bei vergleichbaren Farm-Abbrüchen vor Open und beide Freitage gleich beginnen; Laufzeit-Hypothese gestützt nur, wenn Ausfälle mit Laufzeit >4 Tage zusammenfallen (am 16.10. Gateway-Startzeit prüfen); sonst UNKNOWN. Weiterer Datenpunkt: Fr 30.10.

**Prompt B3 (Stand 23.10. 16:05 Berlin, Claude Code auf CT109, nur lesend):**
```
AUFTRAG B3 – Periodizität der IBKR-tbt-Ausfälle seit 14.10.2026 (nur lesen, danach STOPP)

REGELN (wie B2):
- Nur lesen. Kein start/stop/restart/reload/enable von Units, kein Schreiben in /etc oder /opt, kein git commit/checkout, nur eine Notizdatei unter /tmp, keine Orders, keine neuen API-Abos, kein Gateway-Login.
- Keine Inhalte von Spool/Parquet/SQLite lesen; von Datendateien nur Name, Größe, mtime. IBKR-Tage ab 12.10. sind versiegelt; kein Analysepfad, kein scripts/analysis-run, kein collector.measure.
- Kein IBC-Log, kein secrets.env, keine ibkr.env. Keine Konten, URLs, Zugangsdaten ausgeben.
- Nicht in den Minuten :05 bis :10 jeder Stunde (UTC) laufen lassen.

AUFGABE (Zeitraum 2026-10-14 00:00 UTC bis jetzt; falls das Journal kürzer reicht: sagen, ab wann es reicht):
1. date -u; journalctl --disk-usage; ältester Journal-Eintrag von signal-ibkr und ibgateway.
2. Tabelle je Handelstag (UTC, Mo–Fr; Wochenende nur als Zeile "keine Handelstage"): 
   a) Startzeit(en) von ibgateway und signal-ibkr (journalctl-Startmeldungen, ActiveEnter) und daraus die Gateway-Laufzeit um 13:30 UTC in Stunden;
   b) Zahl und Uhrzeiten der Meldungen 2103/2104/2119 (US-Farm) zwischen 00:00 und 13:30 UTC, getrennt nach "US-Farm" und anderen Farmen;
   c) Zahl der Meldungen "ohne Daten"/stale/Neu-Abo je Kanal (tbt, depth) und Titel, mit erster und letzter Uhrzeit;
   d) ob am Tag ein Gateway-/Collector-Neustart nötig war (ja/nein, Uhrzeit).
3. Für jeden Tag mit tbt-"ohne Daten": Beginnzeit relativ zu 13:30 UTC und Zeit seit dem letzten US-Farm-Abbruch davor; für jeden Tag OHNE tbt-Ausfall: gab es davor ebenfalls einen US-Farm-Abbruch (ja/nein, wann)?
4. Gleiche Frage für die Zeit nach dem Neustart 23.10. ~13:52 UTC bis jetzt (nur Befund, nicht werten).
5. Kennzeichne jede Zeile [gemessen] / [unklar]. Keine Hypothese als belegt ausgeben.

AUSGABE: Tabelle, danach vier Sätze: (i) Treten Farm-Abbrüche vor Open auch an Tagen ohne Ausfall auf? (ii) Fallen Ausfälle mit Gateway-Laufzeit >4 Tage zusammen? (iii) Beginnen alle Ausfälle exakt bei 13:30 UTC? (iv) Welche Hypothese (Freitagsprozess / Laufzeit / hängender Abo-Zustand nach Farm-Abbruch) wird dadurch gestützt, welche geschwächt, welche bleibt offen. Keine Änderungsvorschläge. Danach STOPP.
```

**B3-Ergebnis (23.10.):** siehe `01` (Zeile ≈ 14:20 UTC). Hypothesen: Freitagsprozess nicht gestützt, Laufzeit geschwächt, „Abo hängt nach US-Abbruch“ offen. **Nächste Messung B4 (nur lesend, Entwurf, noch nicht ausgegeben):** nur Metadaten (Name/Größe/mtime) der tbt- und depth-Spooldateien für NVDA/INTC/TSLA an 16.10., 21.10., 23.10.: letzte Änderung der tbt-Datei vor dem Ausfall relativ zum US-Abbruch (12:46/11:09/16:01) und zu 13:30 UTC. Trennt „tbt starb beim Farm-Abbruch“ von „tbt starb erst bei Open/16:01“. Inhalte der Dateien nicht lesen. **Offene Punkte aus B3:** Claude-Code-Erlaubnisregeln mit `*` (Warnung), Scratch-Dumps im `/tmp` des Hosts, Grund der Gateway-Neustarts 14.10./19.10. Nächster Datenpunkt Fr 30.10. Maßnahmenentwurf (Watchdog: bei tbt-Stale nach N wirkungslosen Neu-Abos geplanter Gateway-Neustart, da nur das half) gehört in Runde 2, nicht vor den Freeze; betrifft den IBKR-Collector, nicht H1/H2.

### 5k. Freeze-Block für So 25.10. (Entwurf, Stand Fr 23.10. ≈ 14:40 UTC; **nicht ausführen vor meinem Signal am Sonntag**)
**ERLEDIGT 23.10. ≈ 18:05 UTC: Freeze ausgeführt, `FREEZE_HASH 93146882…359c`, unabhängig geprüft (Details `01`). Nächster Schritt: Block 3 (Stufe D, einmalig, beschreibend).**
**ERLEDIGT 23.10. ≈ 18:25 UTC: Stufe D gelaufen (`BESCHREIBEND`, `result_hash 898281e9…d30`): H1 Netto +3,85 bp (p 0,40, unter Placebo-q95), H2 Netto −22,15 bp (C7b verletzt). Nächster Schritt: Stufe B (`--stage confirm`), vorgezogen von Mo 26.10. auf Fr 23.10. Abend (Begründung: A ist laut Spec V2.1 kein Filter, Q-Pflicht für E erledigt D16, Code gesperrt, Andi anwesend; Laufzeit Minuten).**
**ERLEDIGT 23.10. ≈ 18:40 UTC: Stufe B gelaufen (`NULLBEFUND` für H1 und H2, `result_hash 9d24018a…f3f6`, Details `01`, Entscheidung D19). Weiter: Runner-Deploy/Schatten (GO-Texte auf v0.6.0 aktualisieren), Report + Runde-2-Liste.**

**AKTUALISIERT 23.10. ≈ 16:30 UTC (v0.6.0 nach QA2, siehe §5p):** Paket **`CT109_BAU_lf1_v0.6.0_2026-10-23.zip`** (SHA-256 `fd110abe8b9107a45127881c05e71378278ffeac3d87a7962442ed7adf1ff355`, `code_hash` `901f6e0a3086184cb55952dbdcda195f03aa0fba2fd8588b14de3be01edbdaa6`) liegt entpackt in `D:\CT109-Bau\lf1_v0.6.0\` (mit Kopie von `out\`, alle 7 Dateien hashgleich zu `lf1\out\`); **Block 0 (Windows-Test, vor jedem Freeze):** `cd D:\CT109-Bau\lf1_v0.6.0`, dann `python -W ignore -m unittest discover -s tests` (erwartet `Ran 201 tests … OK (skipped=2)`, ca. 9 min) und `python -m lf1 selfcheck --spec GATE_SPEC_v1.md` (erwartet `code_hash` wie oben, `spec_check.ok true`); nur bei beidem OK weiter mit Block 1. **Zellzulässigkeit jetzt geprüft [gemessen, Sandbox/VM gegen die echte `gate_result_A.json`]:** `validate_list` → `n=2, n_class_W=2`, `lf1_status ZULAESSIG`, Zelle (BTC, 24 h) Klasse W, auswertbar.
**Geprüft (C/L6, Sandbox):** beide Hypothesen bestehen `validate_hypothesis` (Regeltyp, Parameternamen, Wertebereiche, Rückblick ≤ Grenze, Asset BTC, H = 24); `hypotheses.json` (unverändert) als einzeilige ASCII-Datei ohne Zeilenumbruch am Ende, SHA-256 `4822cf7f1ffc7341a993d83b1262d7b2637edb2ed5ab9c5c8272727c3e590cff`; `BAU_SPEC_S1S3_v2.md` liegt **im ZIP v0.5.0** (SHA-256 `34d6add4f7c4dbbf0dbcab5311c29f3981382d0885da32d8e8c11354c720e068`, auch nach CRLF-Normalisierung gleich). **Nicht geprüft:** Zulässigkeit der Zellen (BTC, 24 h) gegen `out\gate_result_A.json` auf dem PC; das prüft `freeze` selbst und lehnt sonst ab (Exit 4). **Abweichung:** `README_RUN.md` §2b nennt noch `BAU_SPEC_S1S3_v1.md`; maßgeblich ist v2 (Plan, Spec v2). Die README bleibt unverändert, weil sie im ZIP-Hash steckt; der Befehl unten ersetzt sie.
Block 1 (PowerShell, schreibt die Liste und zeigt Hashes; **erwartet** die zwei Hashes oben):
```
cd D:\CT109-Bau\lf1_v0.6.0
$j = '[{"id":"H1","rule":"TS_MOM","params":{"L":24,"side":"both"},"asset":"BTC","H":24},{"id":"H2","rule":"SHOCK_FADE","params":{"w":4,"k":1.5,"N":168},"asset":"BTC","H":24}]'
[IO.File]::WriteAllText("$PWD\hypotheses.json", $j, (New-Object Text.UTF8Encoding($false)))
(Get-FileHash .\hypotheses.json -Algorithm SHA256).Hash.ToLower()
(Get-FileHash .\BAU_SPEC_S1S3_v2.md -Algorithm SHA256).Hash.ToLower()
Test-Path .\out\regime_selection.json, .\out\gate_result_A.json, .\out\freeze.json
```
Erwartet: Hashes gleich den obigen, `True`, `True`, **`False`** (`freeze.json` darf noch nicht existieren).
Block 2 (nur bei Block 1 = erwartet; einmalig; Zeile `FREEZE_HASH` zuerst an den Chat, **vor** Block 3):
```
$Z = "D:\CT109-Data\kraken-ohlcvt\Kraken_OHLCVT_Full.zip"
python -m lf1 freeze --zip $Z --regime out\regime_selection.json --gate out\gate_result_A.json --hyps hypotheses.json --bau-spec BAU_SPEC_S1S3_v2.md --out out
```
Block 3 (erst nach meiner Bestätigung des Freeze-Hashs; Stufe D, einmalig, beschreibend):
```
python -m lf1 backtest --zip $Z --regime out\regime_selection.json --freeze out\freeze.json --stage discovery_A --out out
```
**Abbruch:** jede Abweichung in Block 1; `FREEZE ABGELEHNT` (Meldung unverändert an den Chat, nichts löschen, nichts wiederholen); Python-Fehler. **Nach dem Freeze keine Änderung an `lf1/*.py`** (Code-Hash steckt im Freeze).

### 5l. Auftrag B4 – Deploy-Vorprüfung + tbt-Spool-Zeitpunkte (ausgegeben 23.10. ≈ 14:40 UTC, nur lesend, Ergebnis offen)
```
AUFTRAG B4 – Deploy-Vorprüfung und tbt-Spool-Zeitpunkte (nur lesen, danach STOPP)

REGELN (wie B2/B3):
- Nur lesen. Kein start/stop/restart/reload/enable von Units, kein Schreiben in /etc, /opt, /var/lib, kein git commit/checkout, keine Datei außer EINER Notizdatei unter /tmp (kein b4.py, keine Journal-Dumps; Pipes direkt in die Ausgabe), keine Orders, keine API-Abos, kein Gateway-Login.
- Keine Inhalte von Spool/Parquet/SQLite lesen; von Datendateien nur Name, Größe, mtime (ls -l --time-style=full-iso). IBKR-Tage ab 12.10. sind versiegelt; kein Analysepfad, kein scripts/analysis-run, kein collector.measure.
- Kein IBC-Log, kein secrets.env, keine ibkr.env, kein ibgateway-Journal. Keine Konten, URLs, Tokens, Webhooks ausgeben: bei jeder Textausgabe von Unit-/Skriptdateien vorher mit  sed -E 's#(https?://)[^ ]+#\1<REDACTED>#g; s#(token|key|secret|password|webhook)[^ ]*=[^ ]+#\1=<REDACTED>#Ig'  filtern.
- Nicht in den Minuten :05 bis :10 jeder Stunde (UTC) laufen lassen.

AUFGABE:
1. date -u; df -h / /opt /var/lib; free -m; nproc; uptime; systemctl --version | head -1; python3 -c "import sys,numpy,sqlite3;print(sys.version.split()[0],numpy.__version__,sqlite3.sqlite_version)".
2. Existiert schon etwas für den Runner? ls -ld /opt/ct109-paper /var/lib/ct109-paper /etc/systemd/system/ct109-paper-* 2>&1; getent passwd ct109-paper; ss -tlnH | wc -l (nur die Zahl offener TCP-Listener) .
3. Alarmweg bei Dienstausfall (nur lesen, redigiert): systemctl cat 'signal-unit-failed@.service' | sed-Filter oben; für den dort aufgerufenen Befehl nur ls -l (Name, Größe, mtime) und die Anzahl Zeilen, KEINEN Inhalt; für alle Units signal-*.service: systemctl show -p OnFailure -p Restart -p StartLimitBurst -p StartLimitIntervalUSec je Unit als eine Zeile.
4. tbt-Spool-Zeitpunkte (nur Metadaten): für NVDA, INTC, TSLA an den Tagen 2026-10-16, 2026-10-21, 2026-10-23: Dateinamen der tbt- und depth-Spooldateien mit Größe und mtime (full-iso, UTC), sortiert nach mtime. Einsortierung in Worten: letzte tbt-mtime vor dem Ausfallbeginn (16.10. 13:31, 21.10. 16:01, 23.10. 13:31) und vor dem jeweils letzten US-Farm-Abbruch (16.10. 12:52, 21.10. 16:01:28, 23.10. 11:09) – nur wenn aus Name/mtime ableitbar, sonst [unklar]. Falls die Dateien tageweise ohne laufende mtime geschrieben werden (z. B. erst beim Schließen), das so sagen.
5. Jede Zeile mit [gemessen] oder [unklar] kennzeichnen.

AUSGABE: Fakten zuerst (Abschnitte 1–4), dann drei Sätze: (i) Reicht Platz/Last/Version für den Runner (nur Aussage, ob Werte der Annahmen in DEPLOY.md §3 widersprechen)? (ii) Gibt es einen Alarmweg bei Dienstausfall, und wie wird er ausgelöst (nur Unit-Ebene)? (iii) Was sagen die Spool-mtimes zu „tbt starb beim Farm-Abbruch“ vs. „bei Open“? Keine Änderungsvorschläge. Danach STOPP.
```

### 5m. GO-Textentwurf DEPLOY + SCHATTENBETRIEB (v0.6.0, Stand Fr 23.10. ≈ 18:50 UTC; **GO-Text vollständig, wartet auf Andis Satz**; frühester Termin: sofort, sonst Sa 24.10. abends)
**AUSGEFÜHRT 23.10. 19:02 UTC, Ergebnis siehe `01` (Zeile 19:02–19:05 UTC): alle Nachweise erfüllt; Schattenbetrieb läuft.**
**Voraussetzungen (alle belegt):** (1) QA2 ohne offenen BLOCKER, Windows-Test v0.6.0 bestanden (201 Tests, `code_hash 901f6e0a…daa6`) – `01`; (2) Freeze vorhanden, `FREEZE_HASH 93146882…359c` unabhängig nachgerechnet – `01`; (3) B4/B6 ausgewertet (72 G frei, Python 3.11.2/numpy 1.24.2, Alarmweg geklärt, `04` §5o); (4) `feed-check` läuft **im Befehlsblock selbst** auf CT109 und bricht bei Abweichung ab (in der Sandbox nicht prüfbar: Netzsperre); (5) GO R2 (Registry-Backup) ist **keine** Voraussetzung (Runner berührt Registry/Parquet nicht); bleibt separat angeboten.
**Paket:** `CT109_PAPER_DEPLOY_v0.6.0_2026-10-23.zip`, 51 453 Byte, **SHA-256 `45e1eeb3f1e6cf3508009f3febf19de3db4e1d697a14966218fad038e708356d`**; enthält `lf1/*.py` (unverändert, `code_hash` nachgerechnet = `901f6e0a…daa6`), `freeze.json` (SHA-256 `902a0f90…ffcd`), `runner_config.json` (alle 9 Felder gesetzt, `shadow: true`, `expected_freeze_hash`/`expected_code_hash` gefüllt), fünf Units/Timer, `DEPLOY.md`. Liegt auf Andis PC unter `D:\CT109-Bau\`. Lokal geprüft (Sandbox, Python 3.11.17/numpy 1.24.2): Entpacken + beide Hashprüfungen OK, `selfcheck`-Grep OK, `paper-run` mit dieser Konfiguration startet (keine Verweigerung; ohne Netz in der Sandbox nach 60 s abgebrochen), `paper-status --max-age-s` meldet bei leerer DB `PAPER-STATUS ALARM: keine Kerze fuer BTC`, `systemd-analyze verify` aller 5 Dateien ohne Meldung. **Nicht geprüft:** Gesamtblock auf CT109, `scp` PC→CT109, Live-Kraken-Antworten, `DynamicUser` mit gleichem `User=` in drei Units, `RestrictAddressFamilies`/leeres `CapabilityBoundingSet` im LXC, `systemd-run` im LXC.
1. **Exakter Befehl.** Teil A (Andis PowerShell, schreibt nur `/root/ct109-in` auf CT109; `‹CT109-ADRESSE›` trägt Andi ein; erwarteter Hash der ersten Zeile = Paket-SHA-256):
```
$Z = "D:\CT109-Bau\CT109_PAPER_DEPLOY_v0.6.0_2026-10-23.zip"
(Get-FileHash $Z -Algorithm SHA256).Hash.ToLower()
ssh root@‹CT109-ADRESSE› "mkdir -p /root/ct109-in"
scp $Z root@‹CT109-ADRESSE›:/root/ct109-in/
```
Teil B (CT109, root, bash, als **ein** Block einfügen):
```
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
cd /root/ct109-in
echo "45e1eeb3f1e6cf3508009f3febf19de3db4e1d697a14966218fad038e708356d  CT109_PAPER_DEPLOY_v0.6.0_2026-10-23.zip" | sha256sum -c -
test ! -e /opt/ct109-paper
test ! -e /var/lib/ct109-paper
rm -rf /root/ct109-in/pkg
python3 -m zipfile -e CT109_PAPER_DEPLOY_v0.6.0_2026-10-23.zip pkg
echo "902a0f908f97cc7739d92383d121ecc3a8069d01dd13b663004faa1a42f8ffcd  pkg/freeze.json" | sha256sum -c -
install -d -m 0755 /opt/ct109-paper
cp -r pkg/lf1 /opt/ct109-paper/lf1
install -m 0644 pkg/freeze.json pkg/runner_config.json /opt/ct109-paper/
grep -n '"shadow"' /opt/ct109-paper/runner_config.json
cd /opt/ct109-paper
python3 -m lf1 selfcheck > /root/ct109-in/selfcheck.json
grep -q '"code_hash": "901f6e0a3086184cb55952dbdcda195f03aa0fba2fd8588b14de3be01edbdaa6"' /root/ct109-in/selfcheck.json
python3 -m lf1 feed-check > /root/ct109-in/feed-check.json
grep -E '"ok"|utc_now' /root/ct109-in/feed-check.json
install -m 0644 /root/ct109-in/pkg/deploy/ct109-paper-runner.service /root/ct109-in/pkg/deploy/ct109-paper-status.service /root/ct109-in/pkg/deploy/ct109-paper-status.timer /root/ct109-in/pkg/deploy/ct109-paper-watch.service /root/ct109-in/pkg/deploy/ct109-paper-watch.timer /etc/systemd/system/
systemd-analyze verify /etc/systemd/system/ct109-paper-runner.service /etc/systemd/system/ct109-paper-status.service /etc/systemd/system/ct109-paper-watch.service
systemctl daemon-reload
systemd-run --unit=ct109-alarmtest --property=OnFailure=signal-unit-failed@ct109-alarmtest.service --collect --wait /bin/false || true
sleep 20
journalctl -u signal-unit-failed@ct109-alarmtest.service -n 10 --no-pager
systemctl enable --now ct109-paper-runner.service ct109-paper-status.timer ct109-paper-watch.timer
sleep 90
systemctl is-active ct109-paper-runner.service ct109-paper-status.timer ct109-paper-watch.timer
journalctl -u ct109-paper-runner.service -n 20 --no-pager
python3 -m lf1 paper-status --config /opt/ct109-paper/runner_config.json
```
Befehlsblock-Hash (SHA-256 über Teil A + Teil B, 8 Hex): `db15d060`.
2. **Zweck:** Runner installieren und **24 h im Schattenmodus** (`shadow: true`, nie ein Einstieg) laufen lassen: Feed, Latenz, Lücken, Last, Statusseite, Alarmweg. Enthält einen **absichtlichen Testalarm** (`ct109-alarmtest`, `/bin/false`, `OnFailure` → bestehende Vorlage): **Andi bekommt dafür einen kritischen HA-Alarm „ct109-alarmtest.service failed“ – das ist der Nachweis, kein Notfall.** **Nicht Zweck:** Paper-Wertung (Schatten-DB zählt nicht), Änderung bestehender Dienste/Units/Alerting, Parquet/Registry/IBKR, Orders, Schlüssel, `apt`, offene Ports.
3. **Risiken:** neue Prozesse mit Netzzugriff auf zwei öffentliche Kraken-Ziele (GET, keine Schlüssel); Last (Annahme `DEPLOY.md` §3: < 80 MB, CPUQuota 25 %); `DynamicUser=yes` mit gleichem Namen in drei Units ungetestet (Fehlermodus: Dienst startet nicht, kein Schaden); Testalarm erzeugt eine echte Meldung; ein hängender Runner ohne `failed` wird erst vom stündlichen Watch (Minute 25, Schwelle 7800 s) erkannt, also bis ≈ 2 h 10 min später; ein fehlschlagender Watch alarmiert stündlich neu (kein „wieder OK“).
4. **Rollback (ungetestet):** `DEPLOY.md` §6 (`systemctl disable --now ct109-paper-watch.timer ct109-paper-status.timer ct109-paper-runner.service`, fünf Unit-Dateien löschen, `daemon-reload`, `/opt/ct109-paper` umbenennen); `/var/lib/ct109-paper` bleibt als Beweismaterial; bestehende Dienste werden nicht berührt.
5. **Abbruch (messbar):** jede Zeile des Blocks, die `set -e` auslöst (Hash ≠, `/opt/ct109-paper` oder `/var/lib/ct109-paper` existiert, `selfcheck` ohne den Code-Hash, `feed-check` Exit 7); `systemd-analyze verify` mit Ausgabe; `is-active` ≠ dreimal `active`; Journal zeigt `RUNNER START VERWEIGERT`; **kein HA-Alarm für `ct109-alarmtest` innerhalb von 3 min** (dann Alarmweg nicht belegt → Runner stoppen, Rollback, Meldung an den Chat). Immer: Originalausgabe unverändert an den Chat, nichts wiederholen, nichts löschen.
6. **Nachweis:** `sha256sum -c` zweimal `OK`; `"ok": true` im `feed-check`; `journalctl` des Testalarms (Vorlage lief); HA-Alarm sichtbar; `is-active` dreimal `active`; Journalzeile `RUNNER START … freeze=93146882… code=901f6e0a…`; `paper-status`: `mode shadow`, `errors_24h` 0, Kerze für BTC aus der aktuellen Stunde (der Freeze nutzt nur BTC).
7. **Satz:** `GO DEPLOY – db15d060`

### 5n. GO-Textentwurf PAPER-START (v0.6.0; **ENTWURF**; frühestens 24 h nach dem Schattenstart, bei Deploy Fr 23.10. also Sa 24.10. abends)
**AUSGEFÜHRT 24.10. 20:54:21 UTC (`GO PAPER-START – b1f33a5e`, `02`); Paper-Wertung läuft.** (Vorher: Schattenauswertung bestanden (`01`), GO-Text vorgelegt, Befehlsblock-Hash `b1f33a5e` (SHA-256 `b1f33a5ea06fa2dd…`); Ausführung empfohlen 23:05–23:19 Berlin (nach voller Stunde, vor :20). Danach: Nachweis prüfen, Paper-Start in `01`/`02` protokollieren, Bilanz Mo 02.11. (Paper-Laufzeit dann ≈ 8 Tage; reiner Betriebstest.)
**Voraussetzung (Beleg im Chat vor dem GO-Text):** Auswertung des Schattenbetriebs (`paper-status`, `journalctl`, `errors_24h`, `gap_events`, Last): keine `fetch_error`-Serie, Lücken 0 oder erklärt, jede Stunde eine Kerze, Statusseite aktuell, kein unerklärter Alarm; sonst kein GO-Text.
1. **Befehl (CT109, root, bash, nicht zwischen :20 und :30 starten, wegen des Watch bei :25):**
```
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
systemctl stop ct109-paper-watch.timer ct109-paper-status.timer ct109-paper-runner.service
D=/var/lib/ct109-paper/archiv/schatten-$(date -u +%Y%m%dT%H%M%SZ)
install -d -m 0755 "$D"
mv /var/lib/ct109-paper/runner.sqlite* "$D"/
sed -i 's/"shadow": true/"shadow": false/' /opt/ct109-paper/runner_config.json
grep -n '"shadow": false' /opt/ct109-paper/runner_config.json
systemctl start ct109-paper-runner.service
sleep 60
systemctl start ct109-paper-status.timer ct109-paper-watch.timer
systemctl is-active ct109-paper-runner.service ct109-paper-status.timer ct109-paper-watch.timer
journalctl -u ct109-paper-runner.service -n 10 --no-pager
ls -l "$D"
cd /opt/ct109-paper && python3 -m lf1 paper-status --config /opt/ct109-paper/runner_config.json
```
Befehlsblock-Hash: `‹8 Hex, nach Freigabe des Textes›`.
2. **Zweck:** Wechsel von Schatten auf **Paper** (Einstiege werden simuliert, kein Echtgeld) mit **frischer Datenbank**; Schatten-DB archiviert (`runner.sqlite*` inkl. Sperrdatei). Der Modus steht fest in der DB (Umschalten wird vom Runner verweigert). **Nicht Zweck:** neue Hypothesen, Parameteränderung, Löschen, Eingriff in laufende Signale.
3. **Risiken:** Datenlücke ≈ 1–2 min beim Neustart (eine Stundenkerze wird per Idempotenz nachgeholt; Annahme); Timer sind während des Wechsels gestoppt, damit Watch/Status nicht gegen die leere DB alarmieren; ab Start gilt **kein manuelles Eingreifen** (nur Kill-Schalter, jede Abweichung wird in `01` protokolliert); Spec V2.1: Ergebnis ist Betriebstest, kein Edge-Beleg (beide Hypothesen `NULLBEFUND`).
4. **Rollback (ungetestet):** Runner stoppen, `shadow` zurück auf `true`, archivierte DB zurückkopieren; Paper-Wertung wäre ungültig und beginnt neu.
5. **Abbruch:** `set -e`-Abbruch (Archivierung, `grep` zeigt nicht `"shadow": false`); Runner nicht `active`; `RUNNER START VERWEIGERT`; `ls` zeigt die archivierte DB nicht.
6. **Nachweis:** dreimal `active`, Journalzeile `RUNNER START … mode=paper` (sinngemäß), archivierte DB im `ls`, `paper-status` mit `mode paper`, nach der nächsten vollen Stunde neue Kerze.
7. **Satz:** `GO PAPER-START – ‹8 Hex›`

### 5q. Schattenauswertung (Sa 24.10. ab ≈ 19:05 UTC; **nur lesend**, CT109 root, als ein Block; Skript getestet in der Sandbox gegen leere und synthetische Datenbank)
Zweck: Beleg für die Voraussetzung in §5n. Schreibt nichts (DB wird `mode=ro` geöffnet, nur `date`, `systemctl`, `journalctl`, `df`, `paper-status`). Block-Hash (SHA-256 des Skripts, 8 Hex): `47385869`.
```
set -u
export PYTHONDONTWRITEBYTECODE=1
date -u
cd /opt/ct109-paper
systemctl is-active ct109-paper-runner.service ct109-paper-status.timer ct109-paper-watch.timer
systemctl show ct109-paper-runner.service -p NRestarts -p ActiveEnterTimestamp -p MemoryCurrent -p MemoryPeak -p CPUUsageNSec
systemctl --failed --no-pager --plain | grep -E 'ct109|signal' || echo "keine fehlgeschlagenen Units (ct109/signal)"
journalctl -u ct109-paper-watch.service --since "2026-10-23 19:00" --no-pager | grep -cE "Finished|Succeeded" || true
journalctl -u ct109-paper-watch.service --since "2026-10-23 19:00" --no-pager | grep -iE "fail|alarm" | tail -5 || true
journalctl -u ct109-paper-runner.service --since "2026-10-23 19:00" -p warning --no-pager | tail -20
python3 - <<'PYEOF'
import sqlite3, statistics, json
c = sqlite3.connect("file:/var/lib/ct109-paper/runner.sqlite?mode=ro", uri=True)
q = lambda s, *a: c.execute(s, a).fetchall()
print("mode", q("SELECT v FROM meta WHERE k='mode'"))
for a, n, t0, t1 in q("SELECT asset, COUNT(*), MIN(ts), MAX(ts) FROM bars GROUP BY asset"):
    ts = [r[0] for r in q("SELECT ts FROM bars WHERE asset=? ORDER BY ts", a)]
    miss = [(x, y) for x, y in zip(ts, ts[1:]) if y - x != 3600]
    print("bars", a, "n", n, "erwartet", (t1 - t0) // 3600 + 1, "luecken", len(miss), miss[:5])
lat = [r[0] - r[1] for r in q("SELECT recv_ts, ts FROM bars")]
if lat:
    lat.sort()
    print("bar-Verzug s (recv_ts - ts): min", lat[0], "median", int(statistics.median(lat)), "p95", lat[int(len(lat) * .95) - 1], "max", lat[-1])
print("events", q("SELECT kind, COUNT(*) FROM events GROUP BY kind"))
print("decisions", q("SELECT hyp_id, action, COUNT(*) FROM decisions GROUP BY hyp_id, action"))
print("processed", q("SELECT asset, kind, COUNT(*) FROM processed GROUP BY asset, kind"))
print("positions", q("SELECT COUNT(*) FROM positions"), "trades", q("SELECT COUNT(*) FROM trades"))
PYEOF
python3 -m lf1 paper-status --config /opt/ct109-paper/runner_config.json
df -h / /var/lib | tail -2
```
**Bewertung (vorab festgelegt, damit das Ergebnis die Messlatte nicht verschiebt):** (a) Dienste dreimal `active`, `NRestarts` 0, keine fehlgeschlagene `ct109`/`signal`-Unit; (b) `bars`: Anzahl ≈ erwartet, Lücken 0 (oder jede einzeln erklärbar, z. B. dokumentierter Kraken-Ausfall); (c) Bar-Verzug (`recv_ts − ts`) Median < 60 s, Maximum < `late_s` = 300 s; (d) `events`: höchstens vereinzelt `fetch_error`, **keine** `bar_error`, `bad_candle`, `bar_missing`-Serie; (e) Watch-Läufe ≈ 24, keiner fehlgeschlagen; (f) `paper-status`: `errors_24h` ≈ 0, `age_s` kleiner 3700 (im Mittel der Stunde), `mode shadow`; (g) Last: Speicher unter 80 MB (Annahme `DEPLOY.md`), `df` Platz unverändert (72 G frei bei B4); (h) im Schattenmodus keine Einträge in `trades`/`positions`. Jede Abweichung: kein GO-Text, erst klären. Hinweis zur Erwartung: H1/H2 handeln wenig (≈ 7 Trades/Woche je Hypothese), `decisions` zeigt aber jede Stunde je Hypothese eine Entscheidung (`action` flat/blocked/shadow o. ä.).

### 5r. Forschungsspur Runde 2 (Entwurf, Sa 24.10. 13:00 Berlin; Reserve vor dem 02.11.)
| Schritt | Inhalt | Wer/Was | Bedingung |
|---|---|---|---|
| R2-1 Design | `03` §7 (Korrektur: Krypto-Pooling trägt wegen Korrelation kaum; Aktien-Querschnitt aussichtsreicher) | Einsatzleiter, heute | keine Daten |
| R2-2 Datenquelle | **Recherche erledigt (`03` §7, L1):** Pilot Tiingo Free; Fallback MarketParquet (einmalig 79 USD, nur mit Andis Kauf-GO). Offen: Andi legt kostenloses Tiingo-Konto an, Token nur auf dem PC (Umgebungsvariable), Lizenz/Nutzungsbedingungen von mir zu prüfen | Andi registriert (≈ 10 min), ich prüfe Bedingungen | **kein Kauf ohne Andis GO** |
| R2-3 Spec | **ERLEDIGT 24.10.:** `RUNDE2_SPEC_v1.md`, SHA-256 `09b6ca179575ead1…` (voll in `01`), vor jedem Preisabruf | Einsatzleiter | R2-2 |
| R2-4 Q-Zähler | Universum **erledigt 24.10.** (496, Hash `a38aff55…`); Preisabruf **FERTIG 24.10. 23:22 Berlin (495/496 ok, VYLR Fehler, Manifest-Hash `3e625886…`, `01`)**. Danach `python -m lf2 qcount` (nur Zähler) | Andi führt aus (lesend), ich werte | R2-3 gehasht |
| R2-5 Code | **GEBAUT 24.10. (`lf2` v0.3.0, `01`):** Backtest, Loader, 71 Tests, 68/68 Mutationen; Nachträge N1/N2 (`02` D20/D21); **Zweitprüfung durch Agenten erledigt und eingearbeitet** (Andi gab frei). **Windows-Test v0.3.0 bestanden (24.10. 14:37 UTC, 71 Tests, Code-Hash gleich).** **Volllast-Test synthetisch bestanden (24.10.): `qcount` 18 s, `gate` 17 s, `freeze` <1 s, Stufe D 391 s, Stufe B 1 096 s, 0,51 GB; Nullwelt → NULLBEFUND; Laufzeit D+B in Echtgröße ≈ 25 min (Sandbox, Annahme für Andis PC).** **Offen vor Freeze:** echtes Tiingo-Dateiformat gegen `read_csv` (Q-Zähler-Lauf); optional Nachprüfung des Prüfers an v0.3.0 | Einsatzleiter | R2-3 |
| R2-6 Gate S → Freeze → D → B | **ERLEDIGT 24.10. abends: Gate S (beide P), Freeze `77a6eb44…`, Stufe D und B – beide Hypothesen `NULLBEFUND` (`01`, `03`).** einmalig, hashverkettet; höchstens 2 Hypothesen | Andi führt aus, ich prüfe unabhängig | R2-4, R2-5 |
Zeitrahmen (Rechnung, Annahme): R2-1/2/3 Sa–So, R2-4 Mo, R2-5 Mo–Mi, R2-6 Do–Fr (29./30.10.) → erste Ergebnisse vor der Bilanz am 02.11. möglich, aber **nicht garantiert**; jede Abkürzung bei Spec oder QA ist ausgeschlossen (Doktrin). Der Paper-Betrieb von H1/H2 läuft davon unabhängig.

### 5s. Runde 3 – Phase 0 bis Freeze (Entwurf 25.10. ≈ 00:45 Berlin; Basis `03` §8, `02` D28–D30; nichts davon liest Ergebnisdaten)
| Schritt | Inhalt | Wer | Termin |
|---|---|---|---|
| P0-1 Futures-Zugang | **ERLEDIGT 25.10. 00:26 (Andi im Chat, L1): Kraken Futures sind für sein Konto freigeschaltet.** (Handelsumfang/Hebel nicht geprüft; ESMA-Grenzen offen) | Andi | erledigt |
| P0-2 Funding-Historie | **ERGEBNIS 25.10. 00:37 (Andis F1-Ausgabe, L2): Kraken stündlich, PF_XBTUSD 8 983 Raten, PF_ETHUSD 8 983, PF_SOLUSD 8 984, jeweils 2025-10-15 08:00Z bis 2026-10-24 22:00Z (≈ 12 Monate, ein Regime-Zyklus); `PF_BTCUSD` = 400, gültiger BTC-Name ist `PF_XBTUSD`.** Folge: Kraken-eigene Historie reicht für FUND_CROWD nicht als Discovery (wenige Episoden); sie wird **unabhängiges Bestätigungsfenster**, Discovery auf Binance-Funding (mehrjährig, Proxy-Annahme deklariert) → P0-14 | ich / Andi | Teil erledigt |
| P0-3 Nutzungsbedingungen | FINRA Reg SHO, SEC EDGAR (Rate-/User-Agent-Regeln), Tiingo-Lizenz-Vermerk | ich | Mo 26.10. |
| P0-4 Power-Tabelle | je Kandidat aus `03` §8.6: erwartete Netto-Kante, σ, n, MDE, Klasse (HINWEIS oder prüfbar) | ich | Di 27.10. |
| P0-5 Ticker-Reihe | Qualität/Beginn der vorhandenen BTC/ETH-Futures-Ticker (funding_rate, premium, OI) in der Meta-DB; läuft im nächsten (einzigen) lesenden Claude-Code-Auftrag mit Retention-Stufe-2-Vorarbeit | ich bestelle, Andi führt aus | frühestens Di 27.10., nicht :05–:10 |
| P0-7 Kapital & Verlustdeckel | **ERLEDIGT 25.10. 00:19:** Gesamtkapital 10 000 EUR (Andi); Verlustdeckel nach **D34** (Experiment ≤ 3 000 EUR, Lebenszeit-Deckel 1 000 EUR, Position ≤ 100 EUR Worst-Case, Aktien-Mindestticket ≈ 1 000 EUR). Andi kann senken. | Andi / ich | erledigt |
| P0-8 Runde-3-Spec | neue Spec nach D31 (Register, Zustandsvariable, Operationscharakteristik, Zeitversatz-Placebo, Kalibrierung ≥ 200 Nullwelten, Kosteneichung) – vor Freeze, vor jedem Datenzugriff gehasht | ich | Fr 30.10. |
| P0-9 Paper-Kriterien hashen | Säulen A–D (`03` §8.9) als Datei, SHA-256 in `01`, vor Paper-Start des ersten echten Kandidaten | ich | vor dessen Start (Entwurf bis Bilanz Mo 02.11.) |
| P0-10 Kraken Time & Sales | Andi-PowerShell-Block (kostenloser Hersteller-Download, 14 Teile à ~2 GB, SHA-256-Prüfung wie D7); vorher freien Platz auf `D:` nennen; nur BTC/ETH(/SOL)-USD entpacken; Rohdaten bleiben auf der PC (D:\CT109-Data) | ich liefere, Andi führt aus | ab Mo 26.10. |
| P0-14 Binance-Funding/OI-Historie | **Probe F2 bestanden (25.10. 00:40, L2):** `fapi`-Funding ab 2020-01-01 und Monatsarchiv BTCUSDT (162 Schlüssel) vorhanden. Offen: ETH/OI-Metriken (`metrics`) Existenz, Download F3 mit Prüfsummen; Proxy-Annahme „Funding-Extreme sind marktweit“ wird deklariert und gegen Kraken-12-Monate geprüft | ich liefere, Andi führt aus | F3 heute |
| P0-11 Intraday-Aktien (**Andi 25.10.: Alpaca-Konto „gern“, EDGAR-Header mit seiner E-Mail erlaubt, `D:` hat 800 GB frei**) | Quelle klären: Alpaca Basic (SIP/IEX? Lizenz?) vs. IBKR-Paper-Historie (Tiefe?); Ziel ≥ 2 Regime 1-Min-Bars für Sektor-Leader/-Follower; kein Kauf | ich recherchiere, Andi legt ggf. kostenloses Konto an | Di 27.10. |
| P0-12 Optionen-OI | Preis des Optionen-Datenabos (IBKR/OPRA) und Machbarkeit OI-Mitschnitt prüfen; Entscheidung erst nach Kostenlage | ich | Mi 28.10. |
| P0-13 Ereigniszählung | AFTERSHOCK (Krypto) und SYMPATHY (Aktien): nur Zahl unabhängiger Episoden je Regime, keine Renditen nach dem Ereignis; Ergebnis in die Power-Zeile | ich (Block für Andi) | nach P0-10/11 |
| P0-6 Sleeve-Verbund | Entwurf Haupttest + Zerlegungsregel (`02` D29 Punkt 3) | ich | Fr 30.10. |
| **Freeze Runde 3** | Liste ≤ 6, je Zeile Klasse (prüfbar/HINWEIS), Hash **vor** Datenöffnung; Krypto und Aktien gleichrangig (D24). **Vorschlag der sechs (25.10.):** Krypto AFTERSHOCK, FUND_CROWD, WEEKEND-UMKEHR; Aktien SYMPATHY-REVERSION, INSIDER-CLUSTER (Form 4), 8-K-NACHRICHT/KEINE-NACHRICHT. Zurückgestellt (unter Auflösung): CS_MOM14, RESREV, TAUZIEHEN, FINRA | ich | **Ziel Do 29.10., spätestens Fr 30.10.** (hängt an Downloads, Futures-Zugang, Intraday-Quelle) |
| Paper-Erfolgskriterien (D23) | Mindestzahl Trades, Netto-Erwartung mit LCB95 > 0 **oder** ehrlich als „nicht in Wochen belegbar“ ausgewiesen, zwei Regime, keine Betriebsfehler | ich | Bilanz Mo 02.11. |
Nicht tun: Sonntag-Auftrag SOL-L2 (D30), neue Preis-Hypothesen auf A/E/F ohne Kontaminationsvermerk, Kauf MarketParquet (kein positiver Hinweis), L2-Abo bei IBKR (Tageskerzen brauchen es nicht).

### 5o. B4-Ergebnis und Auftrag B5 (23.10. ≈ 15:10 UTC)
**B4 ausgewertet (Andis Screenshots, Host 14:37:30 UTC, L3):** `/`, `/opt`, `/var/lib` ein Volume, 122 G, 45 G belegt, **72 G frei**; RAM 8192 MB, 6867 MB verfügbar, Swap 1 MB genutzt; 4 Kerne, Load ≈ 0,85; Uptime 4 d 4:54; systemd 252 (252.30-1~deb12u2); Python 3.11.2, numpy 1.24.2, SQLite 3.40.1; **keine Reste** von `/opt/ct109-paper`, `/var/lib/ct109-paper`, `ct109-paper-*`-Units, Benutzer `ct109-paper`; 6 TCP-Listener. **Alarmweg:** `OnFailure=signal-unit-failed@%n.service` bei clock, ibkr, ingestion, kraken, kraken-x, kraken-futures-x, kraken-funding, netprobe, compactor, lernbot, lernbot-watch (Typ oneshot, ruft `.venv/bin/python -m alerting.unit_failed %i`, Skript 33 Zeilen, Inhalt nicht gelesen); er greift erst, wenn die Unit nach StartLimit (5 Starts in 5 min) `failed` ist; `signal-alerting`, `signal-heartbeat`, `signal-ibkr-watch`, `signal-status` ohne OnFailure. **Spool:** je Symbol nur die laufende Stunde als JSONL (NVDA 1,70 GB, INTC 1,76 GB, TSLA 0,39 GB nach 38 min, ≈ 3,9 GB, wächst bis ≈ 6 GB/h); Kompaktierung zu `parquet/…/hour=HH/part-0.parquet`, mtime = Kompaktierzeit, **tbt und depth nicht getrennt** → die Frage „tbt starb beim Farm-Abbruch oder bei Open“ ist aus Metadaten **[unklar]** (nur: Stunde 12 klein, ab Stunde 13 groß). **Nicht ausgeführt/Abweichung:** `DEPLOY.md` liegt nicht auf dem Host (steht im Paket), daher kein Abgleich von §3 am Host; mein Auftrag war hier ungenau. Claude Code fragte nach `/root/ergebnis.md`: Antwort **Nein** (Auftragsregel „keine Datei“ geht vor).
**Bewertung (Einsatzleiter):** (1) Platz, RAM, CPU widersprechen den Annahmen von `DEPLOY.md` §3 **nicht** [gemessen: 72 G frei, 6,9 GB verfügbar; Runner < 80 MB, DB < 15 MB/Jahr bleiben Annahmen]. (2) **Risiko:** fällt die Kompaktierung aus, füllt der Spool die Platte in ≈ 12 h (Rechnung, linear, Annahme); der Runner (SQLite) würde mit voller Platte Schreibfehler bekommen; Plattenalarm unbekannt (B5 Punkt 4). (3) **Lücke:** ein hängender oder still beendeter Runner (kein `failed`) erzeugt über `OnFailure` **keinen** Alarm; dafür braucht es einen Stale-Alarm (siehe Entscheidungsentwurf). (4) **Entscheidungsentwurf (nur nach QA, vor Freeze, weil Codeänderung):** `paper-status` mit `--max-age-s` (Exit 8 bei Kerzenalter über Schwelle oder Datenbankfehler), eigene `ct109-paper-watch.service`/`.timer` (stündlich, außerhalb :05–:10) mit `OnFailure=signal-unit-failed@%n.service`, und `OnFailure` auch am Runner. Voraussetzung: B5 (Verhalten von `unit_failed.py` bei fremdem Unit-Namen, Entprellung).
**Test der Zielumgebung (Sandbox, C/L6):** venv Python 3.11.17 + numpy 1.24.2 (wie CT109 bis auf Patchstand): `selfcheck` `code_hash 46239174…e2dd` gleich, `spec_check.ok true`; 170-Tests-Lauf gestartet, Ergebnis offen.
**Prompt B5 (nur lesend):**
```
AUFTRAG B5 – Alarm-Muster für den Runner (nur lesen, danach STOPP)

REGELN (wie B2–B4, Auftragsregeln gehen jeder Erinnerungsregel vor): Nur lesen. Keine Datei schreiben (auch nicht /tmp, auch nicht /root/ergebnis.md; Ausgabe nur im Terminal). Kein start/stop/restart/reload/enable, kein git commit/checkout, keine Orders, keine Abos, kein Gateway-Login. Keine Inhalte von Spool/Parquet/SQLite, kein IBC-Log, kein secrets.env/ibkr.env, kein ibgateway-Journal. Jede Textausgabe von Skript-/Unit-Dateien vorher filtern mit: sed -E 's#(https?://)[^ ]+#\1<REDACTED>#g; s#(token|key|secret|password|webhook|chat_id|bot)[^ ]*[=:][ ]*[^ ,)]+#\1=<REDACTED>#Ig'. Nicht in den Minuten :05 bis :10 jeder Stunde (UTC) laufen lassen.

AUFGABE:
1. date -u.
2. /opt/new-signal-system/src/alerting/unit_failed.py (33 Zeilen) gefiltert ausgeben. Danach in Worten: Welche Argumente erwartet es (z. B. Unit-Name, ob eine feste Liste bekannter Units geprüft wird), was passiert bei einem unbekannten Unit-Namen wie "ct109-paper-runner.service", wohin geht der Alarm (nur Art: HA/Webhook/Mail, keine Adressen), gibt es eine Entprellung (mehrfacher Alarm je Unit).
3. systemctl cat signal-heartbeat.service signal-ibkr-watch.service gefiltert. In Worten: wie wird dort „Dienst läuft, liefert aber nichts mehr“ erkannt und alarmiert (Intervall, Schwelle, Auslöser).
4. Gibt es einen Plattenplatz-Alarm? Nur Dateinamen: grep -rIl -i -E 'statvfs|disk_usage|shutil.disk|df -' /opt/new-signal-system/src /opt/new-signal-system/scripts 2>/dev/null. Danach eine Zeile: Schwelle und Auslöser, falls aus den Treffern ersichtlich, sonst [unklar].
5. Jede Aussage [gemessen] / [Code] / [unklar].

AUSGABE: Fakten zuerst, dann zwei Sätze: (i) Kann eine neue Unit mit OnFailure=signal-unit-failed@%n.service den bestehenden Alarmweg nutzen, ohne dass Code oder Konfiguration angepasst werden muss? (ii) Welches bestehende Muster (heartbeat/ibkr-watch) eignet sich für „Runner liefert keine neue Kerze mehr“? Keine Änderungsvorschläge. Danach STOPP.
```

**B5 ausgewertet (Andis Screenshots, Host 15:11:56 UTC, L3; Claude Code las nur, schrieb und startete nichts; `ibkr_watch.py`-Rest und `heartbeat.py`-Rest ungelesen):** (1) `unit_failed.py` nimmt genau einen Unit-Namen, **keine Whitelist**, hängt `journalctl -u <unit> -n 5` (letzte 800 Zeichen) an, sendet an den Home-Assistant-Webhook (`level=critical`, URL aus derselben `secrets.env`); fehlt die URL, wird **nur geloggt** („alert suppressed“); HTTP-Fehler wird nicht wiederholt; keine eigene Entprellung (systemd löst `OnFailure` einmal pro Wechsel nach `failed` aus). Ein Name wie `ct109-paper-runner.service` wird ohne Prüfung angenommen. Instanzform der bestehenden Units passt zu `OnFailure=signal-unit-failed@%n.service`. [unklar]: Unit-Namen mit Sonderzeichen; ob `signalsvc` das Journal einer `DynamicUser`-Unit lesen darf (dann Alarm ohne Logzeilen, aber Alarm kommt). (2) `signal-heartbeat.timer` jede Minute (Self-Check aller Units, Ping an healthchecks.io als Dead-Man-Switch, HA-Webhook bei Befund, Wiederholung stündlich, „wieder OK“); `signal-ibkr-watch.timer` alle 5 min, `data_stale()` prüft die neueste mtime der Spooldatei, Alarm bei Alter > 5 min nur im Handelsfenster, Cooldown je Ursache. (3) **Plattenalarm existiert:** `heartbeat.py` `DISK_MAX_PCT` 85 % auf `/` jede Minute, `monitor.py` `STORAGE_CRITICAL_PCT` 85,0 (Code). Bei 122 G sind 85 % ≈ 104 G; belegt 45 G, Spool-Spitze ≈ 6 G/h → mein Risikopunkt „Platte nach ≈ 12 h voll ohne Alarm“ ist **entschärft** (Alarm käme vor Vollauf).
**Entscheidung (Einsatzleiter):** Alarm für den Runner wird **im Paket** gelöst, **ohne** Änderung am bestehenden Alarmcode (`/opt/new-signal-system` bleibt unberührt): (a) `OnFailure=signal-unit-failed@%n.service` an Runner-, Status- und Watch-Unit (nutzt den vorhandenen Weg, Annahme bestätigt durch Code-Lesen, **nicht** durch einen Testalarm); (b) neue Option `paper-status --max-age-s N` (Exit 8, wenn Kerzenalter eines Assets über N s oder die Datenbank nicht lesbar), stündliche `ct109-paper-watch.service/.timer` (Minute 25, außerhalb :05–:10) mit `OnFailure`; Schwelle 7800 s (2 h 10 min wie `STALE_S` der Statusseite); (c) Testalarm als eigener Schritt im GO DEPLOY (ein künstlich fehlschlagender Aufruf, Nachweis = Alarm in HA). Folgen: Codeänderung in `cli.py` → neue Paketversion, neuer Windows-Test, Freeze erst danach; Einarbeitung zusammen mit den QA-Befunden (Agent läuft), nicht vorher, um dessen Prüfstand nicht zu ändern. Offene Unsicherheit: Ein fehlschlagender Watch-Lauf löst stündlich einen neuen Alarm aus, solange der Runner veraltet ist (kein „wieder OK“, Annahme akzeptiert).

### 5p. Zweitprüfung QA2 und Version v0.6.0 (23.10. ≈ 16:35 UTC)
**Befunde (unabhängiger Agent, frischer Kontext, Bericht `/tmp/qa2/QA2_BERICHT.md` in der Sandbox; Kopie nicht im Repo; 3 Befunde von mir nachgestellt und bestätigt: B1, M1, M5):** 1 BLOCKER, 5 MAJOR, 12 MINOR; 38 Mutanten, 31 erkannt, 7 überlebten.
| Befund | Maßnahme in v0.6.0 | Test |
|---|---|---|
| B1 Zukunftskerze lähmt den Runner | `ingest` verwirft `ts > Beginn der aktuellen Stunde` (Ereignis `future_bar`) | ja |
| M1 Freeze-/Code-Bindung nur selbstkonsistent | Pflichtfelder `expected_freeze_hash`, `expected_code_hash` in der Konfiguration (kommen aus dem GO-Text) | ja |
| M2 Betriebsparameter/Modus nirgends festgehalten | Konfiguration strikt (alle Felder Pflicht, unbekannte verweigern), Start-Ereignis mit Konfiguration, Python/numpy-Version, Modus in `meta` fixiert (Wechsel verweigert), `created_utc` | ja |
| M3 kein automatischer Alarm | `OnFailure` an Runner/Status/Watch, `paper-status --max-age-s` (Exit 8), stündliche Watch-Unit, Statusseite atomar und mit KEINE KERZE/ZUKUNFT/Fehler 24 h, beschädigte DB = Exit 6, großzügigeres StartLimit | ja |
| M4 Entscheidungsgrundlage nicht festgehalten | `decisions.close_px`, Ereignis `bar_revised` | ja |
| M5 keine Plausibilitätsprüfung | `candle_problem` (endlich, > 0, High/Low konsistent, Volumen ≥ 0), Ereignis `bad_candle`, Rest läuft weiter | ja |
| m1 Redirect umgehbar, m2 transienter DB-Fehler markiert Kerze, m3 kein Retry bei fehlender Kerze, m4 Einzelinstanz, m5 `created_utc`, m6 Versionen, m7 README/DEPLOY-Fehler, m11 leere Kerzen/Ticker | behoben (Redirect-Sperre, Antwortgröße ≤ 5 MB; transienter Fehler bricht den Zyklus ab; Retry bis Kerze da; flock; Start-Ereignis; README auf Spec v2; Ereignisse `empty_candles`, `ticker_empty`, `bar_missing`) | ja |
| m8 GO-Trennung, m9 Sandbox im LXC, m10 Schatten zählt Einstiege zu hoch, m12 keine Hashkette | dokumentiert (`DEPLOY.md` §8; GO-Texte getrennt; B6 prüft die Sandbox-Direktiven) | – |
| überlebende Mutanten M05, M25, M18, M14, M16, M17, M24 | 6 neue Tests (Kostenkomponenten, Tagesgrenze, `recv_ts`, Einzel-Lücke, Heartbeat, Schlusskurs) | alle 7 erkannt |
**Messung (C/L6, Sandbox):** Suite **201 Tests OK** (170 alt + 31 neu) auf Python 3.13/numpy 2.5; 21 + 7 gezielt eingebaute Fehler (Mutanten) gegen die neuen Tests: **alle erkannt** (bei einem, der Hash-Längenprüfung, erst nach Nachschärfung). Lauf auf Python 3.11.17/numpy 1.24.2 (CT109-Stack) mit dem fertigen ZIP: Ergebnis siehe `01`. **Nicht geprüft:** Live-Antworten von Kraken, systemd/LXC-Verhalten, echte SQLite-Sperrrennen, Windows (Test folgt). **Folge für den Plan:** Code ist ab jetzt gesperrt (jede Änderung an `lf1/*.py` = neues Paket + neuer Windows-Test vor dem Freeze); Sonntag ≈ 19:00 Berlin: Block 0 (Windows-Test), danach Freeze und Stufe D.

## 6. Erfolgskriterien Schutzteil, Stand 29.10. (ersetzen E1–E6 des Owner-Plans, Owner-OK nötig)
- **E1 Code-Schutz:** V142 + Dirty-Arbeit nachweislich offhost und wiederherstellbar – oder präziser Blocker. (**Stand: GitHub PASS L5, Host-Hash PASS L3, Windows-Hash PASS L3**; offen nur optional Windows-Restore.)
- **E2 Daten-Schutz:** Sicherungsstatus der versiegelten Rohdaten geklärt (JA/NEIN) und Entscheid D3; **Registry-Kopie außerhalb des Containers (R1 + Kopie nach `D:`: erledigt 22.10., L3/L1) und tägliche Sicherung (R2) offen**; Host-only-Arbeit (`/root/run`) gesichert oder bewusst verworfen (E4b → GO offen).
- **E3 Kapazität:** Messreihe ≥ 5 Punkte; 30-Tage-Aussage oder BLOCKED; Thin-Pool-Alarm entworfen.
- **E4 Forschung:** Bewegungsbudget-Gate vorregistrierbar beschrieben (`GATE_SPEC_v1.md`, erledigt); sicherer Reader entworfen und synthetisch getestet; SOL = registrierte Hypothesen **oder** dokumentierter Nullbefund/BLOCKED; LF-1-Entwurf.
- **E5 Betrieb:** Lernbot bleibt aus; BTC/ETH-L2 bleibt aus.
- **E6 Doku:** 5 Dateien aktuell (+ Gate-Spec), Tagesabschluss = Änderungslog; erstes Sicherungspaket 23.10. auf `D:` abgelegt und per Hash geprüft (01, 13:14 UTC); **Wissensspeicher `ct109-wissen` als Wahrheit, Sicherungspaket auf `D:`** (`00` §8).
Stop-Regel bleibt: scheitert ein hartes Gate, keine Scope-Ausweitung, sondern Ursache und sichere Alternative.

### 5t. Blöcke T1–T4 (Kraken Time & Sales) und F1 (Funding-Historie) – Andis PowerShell, Stand 25.10. ≈ 00:45 Berlin (P0-2, P0-10; Vorlage D7 §5d; nur Download/Lesen öffentlicher Daten, kein Schlüssel; **ungetestet in der Sandbox, keine PowerShell vorhanden**)
**Quelle (L1, Support-Artikel 360047543791, WebFetch 25.10.):** 14 Teile `Kraken_Trades_Full.zip.part00` bis `part13` (je ≈ 2 GB) unter `https://assets.kraken.com/marketing/institutions/`, Teil-Prüfsummen `Trades_Full_PARTS_SHA256SUMS.txt`, erwarteter SHA-256 des zusammengesetzten ZIPs `5f5affd6c341366cdc5db290beaf281b8e362fd650bc9273aac6defdcaa98018`; Daten je Paar von der ersten Order bis 30.09.2026. CSV-Spalten laut Artikel: `timestamp, price, volume, type (b/s), order_type (l/m), misc, trade_id`; **ob `type` die Taker-Seite ist, steht dort nicht (zu prüfen).** Platz: Teile ≈ 28 GB + zusammengesetztes ZIP ≈ 28 GB. **Regeln:** Links nicht im Browser öffnen, nichts entpacken (außer T4 nur Auflistung), nicht in Excel öffnen, Teile nicht löschen; Rückmeldung an den Chat nur die Ausgabe von T2, T3, T4, F1.
T1 (Download, fortsetzbar):
```
Get-PSDrive D | Select-Object Used, Free
New-Item -ItemType Directory -Force -Path D:\CT109-Data\kraken-trades | Out-Null
Set-Location D:\CT109-Data\kraken-trades
$base = "https://assets.kraken.com/marketing/institutions"
foreach ($n in "00","01","02","03","04","05","06","07","08","09","10","11","12","13") {
  curl.exe -L --fail -C - -o "Kraken_Trades_Full.zip.part$n" "$base/Kraken_Trades_Full.zip.part$n"
}
curl.exe -L --fail -o Trades_Full_PARTS_SHA256SUMS.txt "$base/Trades_Full_PARTS_SHA256SUMS.txt"
```
T2 (Teile gegen Kraken-Prüfsummen; erwartet 14-mal OK):
```
Set-Location D:\CT109-Data\kraken-trades
$sums = Get-Content .\Trades_Full_PARTS_SHA256SUMS.txt
foreach ($f in Get-ChildItem .\Kraken_Trades_Full.zip.part*) {
  $h = (Get-FileHash $f.FullName -Algorithm SHA256).Hash.ToLower()
  $ok = [bool]($sums | Where-Object { $_.ToLower().Contains($h) -and $_.Contains($f.Name) })
  "{0}  {1} B  {2}" -f $f.Name, $f.Length, $(if ($ok) { "OK" } else { "ABWEICHUNG" })
}
```
T3 (nur wenn alle 14 OK; Zusammenfügen und Hash, dauert einige Minuten):
```
Set-Location D:\CT109-Data\kraken-trades
cmd /c copy /b Kraken_Trades_Full.zip.part00+Kraken_Trades_Full.zip.part01+Kraken_Trades_Full.zip.part02+Kraken_Trades_Full.zip.part03+Kraken_Trades_Full.zip.part04+Kraken_Trades_Full.zip.part05+Kraken_Trades_Full.zip.part06+Kraken_Trades_Full.zip.part07+Kraken_Trades_Full.zip.part08+Kraken_Trades_Full.zip.part09+Kraken_Trades_Full.zip.part10+Kraken_Trades_Full.zip.part11+Kraken_Trades_Full.zip.part12+Kraken_Trades_Full.zip.part13 Kraken_Trades_Full.zip
$z = Get-FileHash .\Kraken_Trades_Full.zip -Algorithm SHA256
"{0}  {1} B" -f $z.Hash.ToLower(), (Get-Item .\Kraken_Trades_Full.zip).Length
"gleich Kraken-Wert: " + ($z.Hash.ToLower() -eq "5f5affd6c341366cdc5db290beaf281b8e362fd650bc9273aac6defdcaa98018")
```
T4 (nur Auflistung der Einträge für BTC/ETH/SOL, ohne Entpacken):
```
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead("D:\CT109-Data\kraken-trades\Kraken_Trades_Full.zip")
"Einträge gesamt: " + $zip.Entries.Count
$zip.Entries | Where-Object { $_.Name -match '^(XBT|BTC|ETH|SOL)(USD|EUR)\.csv$' } | Select-Object FullName, Length | Format-Table -AutoSize
$zip.Dispose()
```
F1 (Funding-Historie, öffentlicher GET `…/derivatives/api/v3/historical-funding-rates?symbol=…`, Endpoint laut Kraken-Doku `security: []`; Symbolnamen BTC-Perp unklar → beide probiert):
```
New-Item -ItemType Directory -Force -Path D:\CT109-Data\kraken-funding | Out-Null
foreach ($s in "PF_XBTUSD","PF_BTCUSD","PF_ETHUSD","PF_SOLUSD") {
  try {
    $r = Invoke-RestMethod -Uri "https://futures.kraken.com/derivatives/api/v3/historical-funding-rates?symbol=$s" -TimeoutSec 60
    $r | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 "D:\CT109-Data\kraken-funding\$s.json"
    $n = $r.rates.Count
    $d = ([datetime]$r.rates[1].timestamp - [datetime]$r.rates[0].timestamp).TotalHours
    "{0}: {1} Raten, von {2} bis {3}, Schritt {4} h" -f $s, $n, $r.rates[0].timestamp, $r.rates[$n-1].timestamp, $d
  } catch { "{0}: FEHLER {1}" -f $s, $_.Exception.Message }
}
```
**Auswertung (vorab):** T-Teil PASS nur bei 14-mal OK **und** `gleich Kraken-Wert: True`; T4 muss die Dateien für BTC/ETH/SOL zeigen (sonst Namensmuster anpassen, kein Datenblick). F1: PASS, wenn mindestens ein BTC- und das ETH-Symbol eine Historie liefern; relevant ist die **früheste Zeit** (≥ 2 Regime?) und der **Schritt**. Danach: Entpacken der Ziel-Dateien (eigener Block nach T4-Ausgabe), Ereigniszählung (`02` D33 Punkt 2).

**Stand 25.10. ≈ 00:55:** T1–T4 PASS (ZIP-Hash gleich Kraken-Wert, XBTUSD/ETHUSD/SOLUSD(+EUR) vorhanden). Nächster Block T5: nur die drei USD-CSV entpacken (≈ 11,6 GB) nach `D:\CT109-Data\kraken-trades\csv`, Kopfzeile prüfen, Python-Version abfragen. Harte Regel: Zeilen nach 30.06.2026 23:59:59 UTC werden nie gelesen (Schnitt im Lader, ZIP-Hash = Siegel der Rohdaten). Alpaca F4 PASS (SIP ab 2016 im Basic-Plan, Konto ACTIVE); offen: Nutzungsbedingungen, Delisting-/Survivorship-Abdeckung, Anfangsartefakt 2016-01-01, Rate-Limit-Rechnung (≈ 190 Seiten je Symbol und 10 Jahre 1-Min).

**T6 (25.10. ≈ 01:00):** `agg_trades_v1.py` auf Andis PC für XBTUSD, ETHUSD, SOLUSD; Ausgabe `D:\CT109-Data\kraken-trades\agg\*_1m.csv`, Chat bekommt nur die Zusammenfassungen. PASS: Schnitt erreicht (1), Unordnung klein, Tick-Test zeigt, ob `type`=Taker-Seite (b häufiger auf up-Ticks). Danach: Ereigniszählung AFTERSHOCK/WEEKEND (nur Zählung, keine Nachrenditen), Regime-Einordnung.

**P0-2 Stand 25.10. ≈ 01:10:** Kraken Time & Sales bis 30.06.2026 nutzbar (Minutenaggregate XBT/ETH/SOL, 13 Jahre XBT, 11 ETH, 5 SOL; mehrere Regime ab 2021 sicher). Offene Datenhygiene: ETH-Ausreißer 2015 (Preis 0,15), Spread-/Mikrostruktur-Kalibrierung aus Trades (Kosten richtungsfrei eichen). Nächster Block F3: Binance-Funding-Monatsdateien BTC/ETH/SOL ≤ 2026-06 mit Prüfsummenabgleich (P0-14).

**P0-14 Stand 25.10. ≈ 01:15:** F3 PASS (BTC/ETH 78, SOL 70 Monate, 0 Abweichungen), Daten unter `D:\CT109-Data\binance-funding\<SYMBOL>`. Offen: Open-Interest-Historie (Binance `metrics` nur täglich ab 2020-09, schwer) – nur falls FUND_CROWD sie braucht; Kraken-Funding 12 Monate liegt unter `D:\CT109-Data\kraken-funding`.

**Stand 25.10. ≈ 01:35 (Andi Feierabend):** Phase-0-Daten fertig: Kraken T&S (XBT/ETH/SOL ≤ 30.06.), Binance-Funding (BTC/ETH 78, SOL 70 Monate), Kraken-Funding 12 Monate, SEC Form 3/4/5 82 Quartale, Alpaca-Paper (SIP ab 2016, Lizenz offen). **Morgen (Andi):** Block E2 (liegt im Chat, `code/tools/count_events_v1.py`). **Ich:** Alpaca-Nutzungsbedingungen, Quelle für 8-K-Items (EDGAR-Submissions/Index), Runde-3-Spec (Gerüst nach D31, Power-Zeilen aus E2), Freeze Ziel Do 29.10.

**Stand 25.10. ≈ 02:30:** Runde-3-Spec-Entwurf v0.1 liegt vor (`RUNDE3_SPEC_v0.1_ENTWURF.md`). **Nächste Schritte:** (1) E2 (Andi, morgen) → Schwellen/Power-Zeilen K4/K1/K5, HINWEIS-Deklaration; (2) Agentenberichte `alpaca_edgar_quellen.md` und `effektgroessen_insider_8k.md` einarbeiten (Welle 3b, Quellen, Effektgrößen); (3) E3-Zählung SEC Form 4 (Cluster je Jahr) und 8-K-Zählung (Skript auf Andis PC); (4) C7-Kalibrierung planen (Nullwelten-Code, ein präziser Code-Agent erst nach Spec-Freigabe, D36); (5) Welle 3a Freeze Ziel Do 29.10., Welle 3b spätestens Fr 30.10. bzw. wenn Quellen geklärt; (6) Paper-Säulen A–D hashen vor Paper-Start; (7) Sleeve-Verbund-Entwurf bis Fr 30.10.

**Stand 25.10. ≈ 12:30:** E2/E3 ausgewertet (siehe `01`), **D38** gefasst. Offen bei Andi: F5 (Alpaca delistete Symbole/Artefakt 2016), E2b (K4-Zustände/Streuung, Funding relativ, Wochenende), F6/F7 (Kraken-Paare nach Größe, Kraken-Futures-Instrumente). Bei mir: Spec v0.2 nach E2b, Alpaca-/EDGAR-Agentenbericht einarbeiten, Kalibrierungs-Plan C7.

**Stand 25.10. ≈ 13:00:** D39. **Nächste Blöcke (Andi):** T7 (≈ 38 Alt-USD-CSVs entpacken und zu 1-Min-Aggregaten rechnen, ≈ 16 GB, ca. 25 Min), danach E2c (K4P-Zählung, von mir). **Ich:** E2c-Skript, Spec v0.2, Kalibrierungs-Entwurf C7 (Nullwelten aus blockverschobenen Ereignisuhren), Paper-Säulen A–D für K4 (wenige Episoden/Jahr ⇒ ehrliche Dauer).

**Stand 25.10. ≈ 14:00:** `k4_test_v1.py` fertig (Funktionstest synthetisch). **Reihenfolge nach T7:** (1) E2c-Zählung K4P (Andi-Lauf), (2) Kalibrierlauf C7 für K4 (XBT,ETH) und K4P (nur Zählung/Raten, keine echten Kennzahlen), (3) Spec v0.2 mit Power-Zeile + Operationscharakteristik, (4) Hash/Freeze Ziel Do 29.10.

**Stand 25.10. ≈ 15:00:** E2c-Neulauf (Filter repariert) läuft bei Andi; danach Entscheid, ob K4P als gekettete Replikation tragfähig ist (Abhängigkeit zu BTC/ETH beachten: Markt-Cluster ⇒ effektive unabhängige Zahl < Episodenzahl; Inferenz nur über Wochenblöcke).

**Stand 25.10. ≈ 15:30:** D40 (K4/K4P getrennte Tests). **Läuft/ansteht:** Kalibrierläufe C7 (K4: ≈ 30 Min, K4P: ≈ 1–2 h) bei Andi; danach Spec v0.2 (Operationscharakteristik + Power), Paper-Säulen, Freeze Ziel Do 29.10.

**Stand 25.10. ≈ 16:30:** C7 bestanden (D41). **Bis Freeze (Ziel Do 29.10.):** (1) Paper-Säulen A–D für K4/K4P entwerfen und in die Spec (wenige Episoden/Jahr ⇒ realistische Dauer), (2) Vorwärts-Aggregation Jul–Sep 2026 (Skript mit Fenstergrenzen, einmalig öffnen), (3) Daten-Manifest-Hash der benutzten Aggregate, (4) Seeds/Code-Hash/Spec-Hash festlegen, unabhängige Nachrechnung, (5) Registerzeile. Parallel Forschung Runde 4 (Aktien: Tageskerzen-Quelle Alpaca, Survivorship-Zählung).

**Stand 25.10. ≈ 18:00:** Freeze-Kandidat steht. **Vor Freeze (Do 29.10.):** Andi-Endlektüre (Ausnahme D41), Manifest-Hash der 41 Aggregatdateien (Get-FileHash), Code-Hash, unabhängige Hash-Nachrechnung, GO-Schablone für Registry-Schreiben. **Forschung bis dahin:** Runde-4-Kandidaten (Order-Flow aus vol_b/vol_s, Aktien-Tageskerzen via Alpaca).

**Stand 25.10. ≈ 16:00:** D42 (Krypto-Querschnitt HINWEIS). **Runde-4-Kandidaten mit Power ≥ 0,5 gesucht:** Order-Flow-/Ereignis-Mechanismen mit Kante pro Ereignis deutlich über Kosten (Kryptoschocks sind gezählt); Aktien-Ereignisse (S4/S5 HINWEIS laut Literatur). Offen: lohnende Struktur-/Zwangsflüsse (Index-Rebalancing, Listings, Token-Unlocks, Expiry-Effekte) auf Datenverfügbarkeit prüfen.

**Stand 25.10. ≈ 16:45:** D43 (K6). **Jetzt:** `k6_test_v1.py` (Engine mit Richtung, Stop, Cooldown je Paar; Placebos; C7), Spec Welle 4a (K6) als eigener Freeze-Kandidat; Kalibrierlauf bei Andi (ca. 1–2 h).

**Stand 25.10. ≈ 16:25:** K6 kalibriert (C7 bestanden). **Entscheid offen für mich (Doktrin):** K6 mit 3A gemeinsam am Do 29.10. freezen (Register 5/6/7) – Vorbehalt: Perp-Liquidität/Kosten der dünnen Alts ungeprüft; zuerst Kostencheck (Kraken-Futures-Orderbuch-/Spread-Stichprobe, nur Lesen) und Konzentrationsregel prüfen.

**Entscheid 25.10. ≈ 16:45 (Einsatzleiter, Doktrin): K6-Liquiditätsfilter ex ante** (festgelegt aus Ticker-Momentaufnahme, ohne jede Renditeinfo): Paar nur im K6-Pool, wenn Perp existiert, Median-Spread ≤ 12 bp und 24-h-Volumen ≥ 250 000 USD. Wirkung (ohne XDG): 33 Paare, 8 940 von 13 052 Ereignissen (Roh-Zählung), gewichteter Spread 5,1 bp; ausgeschlossen XDG(vorläufig), ALGO, XTZ, SHIB, ETC, MANA, KAS, FLOW. Folgen: C7-Kalibrierung K6 muss mit gefiltertem Pool neu laufen (σ, Episodenzahl, MDE ändern sich); Pool-Liste wird mit gehasht; Filter ist Spec-Bestandteil, Momentaufnahme 25.10. wird als Beleg abgelegt. Offen: DOGE-Nachmessung (Skript v1.1), Preiswirkung über Level 1 hinaus (eigene L2-Aufzeichnung CT109 prüfen / Paper misst).

**Stand 25.10. ≈ 17:10:** K6 (gefilterter Pool) kalibriert, C7 bestanden, MDE 15,4 bp, Gesamt-Power bei MDE ≈ 65–68 %. **Entscheid:** K6 geht mit 3A in **einen** Freeze (Register-Index 5, 6, 7) am Do 29.10. – Begründung: Welle (BH innerhalb), Plätze vorhanden, Mehrkosten gering. Offene Arbeit bis dahin: Spec-Endfassung 4A, Freeze-Paket (Code-Voll-Hashes `k6_test_v1`/`k4_test_v1`, Manifest, Pool-Datei, Seeds), unabhängige Hash-Neuberechnung, Registry-Zeilen, GO-Schablone (Andi), Forward-Fenster-Skript.

**Stand 25.10. ≈ 17:45:** Freeze-Paket Welle 3 steht als Vorschau (`FREEZE_PAKET_R3_v1.md`). Nächste Schritte: (1) Endlektüre der Specs 3A/3B (Widersprüche, Zahlen), (2) Freeze-Hash neu rechnen, GO-Schablone ausfüllen und Andi vorlegen (Ziel Mo 26.10./spätestens Do 29.10.), (3) nach GO: Registry-Commit, `run_r3_final.ps1`, Ergebnisse als Aggregate dokumentieren, (4) parallel Forschung Runde 4 (Aktien: SYMPATHY, INSIDER, 8-K; Krypto: Funding/Struktur), Paper-Säulen A–D hashen vor Paper-Start, Bilanz lf1 Mo 02.11.

**Stand 25.10. 17:21:** FREEZE R3 erfolgt. Nächster Schritt: gefrorenes `k4_test_v1.py` + `run_r3_final.ps1` auf Andis PC, Hashes prüfen, Andi startet den Lauf (PowerShell, ≈ 1–2 h), Ergebnisse als Aggregate in `01`/`03`, Register-Ergebniszeilen anhängen (je Test, auch Abbrüche). Danach Vorwärtsfenster Jul–Sep 2026 je Test einmal, Paper-Säulen A–D hashen.

**Stand 25.10. ≈ 18:00 – Konsequenzen Welle 3:** Krypto-Ereignis-/Reversions-/Flussfamilie auf 4-h-Horizont mit Taker-Kosten: kein Brutto-Edge (4 Tests + lf1 H1/H2). Krypto-Richtung ändern: (a) strukturelle, nicht-direktionale Erträge mit längerem Horizont (Funding-Carry Spot/Perp, deskriptiv P-K2; Prämie, kein Signal), (b) Wochen-Horizonte (CS_MOM14, Trend) wo Kosten klein sind – beides HINWEIS/Auflösungsproblem prüfen, (c) Maker-Ausführung nur falls ein Brutto-Edge sichtbar wäre (aktuell nicht). Aktien: INSIDER-ALL (5 487 Cluster, 2 704 Symbole, 97 % Kursabdeckung) – Spec/Testbau jetzt, Freeze vor Renditeblick. Paper: lf1 läuft weiter als Betriebstest (Bilanz 02.11.); Vorwärtsfenster Jul–Sep 2026 für K4/K4P/K6 entfällt als Bestätigung (kein Signal), optional als Konsistenzblick später.

**Stand 25.10. ≈ 19:00 – INSIDER-ALL:** Entwurf `RUNDE3C_SPEC_v0.1_ENTWURF_INSIDER.md` + `insider_test_v1.py` fertig (synthetisch getestet). Reihenfolge: (1) Andi: SPY/IWM-Download bestätigen, `insider_test_v1.py count` (nur Zählungen); (2) `calib --sigma <gezählt>` (C7); (3) Freeze-Paket R3C + GO-Satz `GO FREEZE-R3C – <Hash>`; (4) `final` einmalig. Parallel offen: lf1-Bilanz 02.11., D34-Bestätigung, Krypto-Richtung (Funding-Carry, Wochenhorizont), Paper-Säulen A–D hashen, Kraken-Futures-Kontoumfang prüfen.

**Stand 25.10. ≈ 20:30 – INSIDER-ALL geparkt (D47, HINWEIS).** Nächste Richtung: **varianzarmer Funding-Carry** (spot-long + Perp-short, deltaneutral; σ klein, daher Auflösung möglich). Phase 0: Funding-Historie Kraken Futures (Andi-Lauf, da Sandbox-Proxy blockt), Zählung/Streuung zentriert, dann Spec nach D31 mit Nullwelt-SE in der Power-Zeile. Offen weiter: lf1-Bilanz 02.11., D34-Bestätigung, Paper-Säulen A–D, Kraken-Futures-Kontoumfang.

**Stand 25.10. ≈ 21:00:** Carry verworfen (D48). **FUND_XS** Phase 0: (1) Andi `fund_binance_v1.py` (34 Coins, nur Abdeckung); (2) Spot-OHLCVT als Perp-Preis-Proxy (Kraken-Spot-1h vorhanden), Perp-Basis nur Kraken-Funding-Fenster; (3) Spec nach D31 mit Power-Zeile über Nullwelt-SE; Freeze erst danach. Bestätigungsfenster Kraken-Funding Jul–Okt 2026 + Paper.

**Stand 25.10. ≈ 21:00 – Neubewertung (D49):** Keine weiteren Einzel-Ereignis-α-Tests in Tageskerzen. Kandidaten-Richtungen mit hoher Sharpe-Struktur: (1) Maker-/Mikrostruktur auf eigener L2-Aufzeichnung (CT109, Daten wachsen; Mindest-Historie klären), (2) Kalender-/Basis-Strukturen ohne Spot-Gebühr (Kraken-Fixed-Maturity vs. Perp, Gebühren/Marginregeln prüfen), (3) diversifiziertes Portfolio aus den schwachen Signalen nur als Forward-Paper (Beleg im Betrieb). Bilanz lf1 02.11. bleibt.

**Stand 25.10. ≈ 22:00:** Gold-Silber-Freeze-Paket bereit; nach GO-Satz `GO FREEZE-GS – 405f2125` Registerzeile anhängen (`freeze_gs_v1.py --append`), Andi führt `run_gs_final.ps1` aus; danach Ergebnis in 01/02/03 und Registerzeile `result`. Danach 8-K-Nachrichten (Vorbereitung EDGAR-Einlesung).

**Korrektur 25.10. ≈ 21:40:** Die Richtung „Mikrostruktur/Maker auf L2“ (Stand ≈ 21:00) widerspricht D30 (Mikrostruktur trägt nicht; brutto 0,5–2 bp). Wiederaufnahme nur mit neuer Evidenz (Fill-Simulation Time & Sales). Priorität bleibt: 8-K-Zählung, Kalender-Basis prüfen, Forward-Paper-Bündel.

**Stand 25.10. ≈ 21:50:** Phase 0 (a) 8-K-Zählung (Andi: `edgar_8k_count_v1.py download/count`), (b) Basis FM vs. Perp (Binance-Quartale, Kraken-Kontraktliste), Faktor-Residuen-Nullwelt in den Test-Werkzeugen ergänzen (Sektor-ETF-Residuum). Sympathie zurückgestellt.

**Stand 25.10. ≈ 22:10 (D53):** Reihenfolge Phase 0: (1) **CARRY-HOLD** (Spec-Entwurf: Schwellen aus Binance 2019–2023, Test 2024–2026H1 + Kraken; Kraken-Kontoumfang für Short-Perp mit Spot-Sicherheit, Abschlag, Margin prüfen), (2) 8-K-Zählung (Andi), (3) TOM-7 (Tiingo-Altfenster nach Limit-Reset), (4) 13D-Zählung. Werkzeugpflege: sd(z) in alle Kalibrierungen, Vol-Gewichtung und firmen-gematchte Placebos als Option.

**Stand 25.10. ≈ 22:30 (D54):** 8-K: v2-Zählung (Andi) abwarten, dann Power-Zeile je Item mit Episoden; EAR-DRIFT-Nullwelt-SE prüfen. Danach CARRY-HOLD-Spec (D53, Vorrang), TOM-7 (Limit-Reset November), 13D-Zählung.

**Stand 25.10. ≈ 22:50 (D55):** 8-K erledigt (kein Lauf). Jetzt **CARRY-HOLD Phase 0:** Datenlage (Binance 2019–2026 vorhanden, Kraken-Spot-OHLCVT), Anzahl Wochen/Haltephasen, zentrierte Basis-σ, Kosten (Spot 0,40/0,80 % Tier 1 ⇒ Spot-Bein einmal je Phase), Kraken-Kontoumfang (Short-Perp mit Spot-Sicherheit, Margin). Danach TOM-7 (Limit-Reset November), 13D-Zählung.

**Stand 25.10. ≈ 23:05:** CARRY-HOLD Phase 0: Andi führt `basis_probe_v1.py` aus ⇒ σ(Basis-Änderung) und σ(Funding) je Fenster ⇒ Power-Zeile (MDE gegen Erwartung 6–14 bp/Woche). Schwellen für Ein-/Ausstieg erst in der Spec aus dem Trainingsfenster (Discovery), Testfenster bleibt ungeöffnet.

**Stand 25.10. ≈ 23:20 (D56):** CARRY-HOLD: (a) Nullwelt-SE-Tool (Blockbootstrap, sd(z), ≥ 1 200 Welten) für die Primärregel bauen, (b) Spec `RUNDE3E_SPEC_v0.1_ENTWURF_CARRYHOLD` schreiben, (c) Andi prüft Kraken-Futures-Kontoumfang (Short mit Spot-Sicherheit/Multi-Collateral, Margin, Abschlag, ESMA), (d) danach Entscheidung α oder HINWEIS und Freeze-Paket (GO-Satz von Andi nötig).

**Stand 25.10. ≈ 23:40 (D57):** (a) Andi: Transfer-Dialog im Futures-Konto nur ansehen (zulässige Sicherheiten) und Screenshot, nichts bestätigen; (b) Phase 0 CARRY-DATED: Verteilung des annualisierten Aufschlags datierter Kontrakte (Binance-Vision-Lieferkontrakte) als Gelegenheitszählung; (c) CARRY-HOLD-Spec (D56) bleibt Vorrang für den Nachweis im Niedrig-Funding-Regime.

**Stand 26.10. ≈ 00:05:** (1) neue Fassungen `carry_test_v1.py`/`carry_null_v1.py` auf den PC bringen (Hash prüfen), (2) `freeze_carry_v1.py`, `run_carry_final.ps1`, Freeze-Paket, D58 schreiben, (3) GO-Satz von Andi (`GO FREEZE-CARRY – <Hash8>`), (4) Lauf genau einmal. HINWEIS-Klasse, kein α. Danach Kraken-Replikation, datierte Futures (D57), TOM-7 (Limit-Reset November), 13D-Zählung.

**Stand 26.10. ≈ 09:00 (D58):** CARRY-HOLD wartet auf GO (Andi). Parallel ohne GO: Kraken-Replikation vorbereiten (54 Wochen Kraken-Funding, Kraken-Kerzen), Gelegenheitszählung datierter Futures (D57), TOM-7 (Limit-Reset November), 13D-Zählung.

**Stand 26.10. ≈ 08:45 (D59):** Perp-Carry abgeschlossen. Nächste Phase-0-Blöcke: (1) datierte Futures: Gelegenheitszählung (Binance-Lieferkontrakte) und Kraken-Kontraktliste/Laufzeiten, (2) TOM-7 (Tiingo-Altfenster 1993–2015, Limit-Reset November), (3) 13D-Zählung, (4) lf1-Bilanz 02.11. (5) Auswertung 8-K/EAR-DRIFT nur bei neuen Daten.

**Stand 26.10. ≈ 09:05 (D60):** Carry-Thema (Perp D59, datiert D60) abgeschlossen. Offen: TOM-7 (Tiingo-Altfenster 1993–2015, Limit-Reset November), 13D-Zählung, lf1-Bilanz 02.11., D34-Bestätigung, Gesamtlage/Strategiefrage (siehe Antwort an Andi 26.10.).

**Stand 26.10. ≈ 09:35 (D61):** (1) 13D-Zählung auswerten (Andi-Lauf), (2) lf1-Bilanz 02.11. vorbereiten, (3) Paper-Säulen A–D (Hash vor Paper-Start) und Kriterien für ein späteres Bündel schreiben, (4) Kapital-/Skalenfrage mit Andi klären (D34-Revision: was ist das Ziel bei 10 000 EUR?), (5) Beobachtungsliste: TOM-7, EAR-DRIFT, INSIDER-OPP-VS.

**Stand 26.10. ≈ 11:45 (D62):** ORB Phase 0 erledigt, HINWEIS. Optional (Andis Entscheidung): Universum-Erweiterung (Alpaca-Assets active+inactive, Tagesbars) + Intraday-Bars + Spread-Stichprobe, danach Power-Zeile neu. Sonst unverändert: 13D-Auswertung, lf1-Bilanz 02.11., Paper-Säulen A–D, Kapital-/Skalenfrage.

**Stand 26.10. ≈ 12:15 (ORB Schritt 0b):** (1) Andi: `alpaca_universe_v1.py assets` → Zählung; (2) `bars` (≈ 1 h) in `D:\CT109-Data\alpaca-daily-full`; (3) `orb_count_v2.py` auf beide Ordner → Power-Zeile neu; (4) danach Intraday-Tool (5-Min-Bars der Kandidatentage, relatives Volumen der ersten 5 Min, Spread-Stichprobe) und Entwicklungs-/Testfenster festlegen; erst danach Spec/Freeze (eigenes GO).

**Stand 26.10. ≈ 14:10 (ORB 0c):** (1) Andi: `alpaca_intraday_v1.py first` Entwicklungsfenster (≈ 746 k Symbol-Tage, ≈ 2 500 Abrufe ≈ 20 min); (2) Auswertung nur Zählungen/Beträge: relatives Volumen der ersten 5 Min (Paper-Regel: ≥ 100 % gegen Ø der 14 Vortage), Kerzenspanne in % (⇒ Stopabstand ⇒ Kosten in R), Kandidatenzahl je Tag, ADR/ETF-Anteil; (3) zweiter Abruf: Ganztags-5-Min-Bars nur für die ausgewählten Top-K (Entwicklungsfenster) → Regel in der Entwicklung festlegen (K, RV-Schwelle, Ziel/Stop), Spread-Stichprobe; (4) Spec + Power-Zeile + Nullwelten (Zufallsrichtung, Zeitversatz) → Freeze (eigenes GO) → erst dann Testfenster 2020–2026H1 holen und einmal öffnen.

**Stand 26.10. ≈ 15:45 (ORB 0c):** Andi: `alpaca_day5_v1.py` auf die Auswahl `_orb_sel_dev_k60.csv` (≈ 981 Abrufe ≈ 10 min); danach Entwicklungs-Simulation (Brutto-R, Placebos, Kosten) → Regelfestlegung → Spec/Power/Nullwelten → Freeze (GO). Testfenster 2020–2026H1 bleibt gesperrt.

**Stand 26.10. ≈ 18:30 (D63):** ORB abgeschlossen (negativ in Entwicklung). Nächste Optionen: (a) SYMPATHY-REVERSION (Intraday-Daten/Universum jetzt vorhanden; Power-Zeile zuerst), (b) 13D-Auswertung, (c) lf1-Bilanz 02.11., Paper-Säulen A–D, Kapital-/Skalenfrage (offen bei Andi).

**Stand 26.10. ≈ 19:30 (ORB-Freeze-Kandidat):** Wartet auf `GO FREEZE-ORB – 662a156f`. Danach: Registerzeile idx 16; Andi `run_orb_data.ps1` (≈ 2 h), `run_orb_final.ps1`; Ergebnis nur mit zweitem GO registrieren. D63 (Dev negativ) bleibt gültig; der Testlauf ist Andis Auftrag zur unabhängigen Bestätigung.

**Stand 26.10. ≈ 17:30 (ORB gefroren):** Andi: `.\run_orb_data.ps1` (≈ 2 h, Schlüssel als Umgebungsvariablen), dann `.\run_orb_final.ps1`. Ich werte nach Rückmeldung aus; Ergebnisregistrierung nur mit zweitem GO.

**Stand 27.10. ≈ 22:10:** Daten für ORB-Testfenster vollständig. Andi: `.\run_orb_final.ps1` (Minuten). Danach Auswertung und zweites GO für die Ergebnisregistrierung.

**Stand 27.10. ≈ 22:20 (D65):** ORB beendet. Wartet auf `GO REG-ORB – 1f6d8916`. Danach offen: 13D-Auswertung (Andis Output fehlt), SYMPATHY-REVERSION (Power-Zeile), lf1-Bilanz 02.11., Paper-Säulen A–D, Kapital-/Skalenfrage (Andi).

**Stand 27.10. ≈ 22:35:** ORB registriert (idx 17, Kette intakt), Familie abgeschlossen. Offen: 13D-Auswertung (Andis `edgar_13d_out.txt` fehlt), SYMPATHY-REVERSION (Power-Zeile), lf1-Bilanz 02.11., Paper-Säulen A–D, Kapital-/Skalenfrage (D34-Revision nur durch Andi).

**Stand 28.10. ≈ 19:10:** SYMPATHY-Phase-0-Werkzeuge fertig (Dev-Fenster 2016–2019). Andi: Befehlsblock aus dem Chat; danach Power-Zeile → entscheiden: HINWEIS oder prüfbar. Freeze Runde 3 weiterhin nur für die Kandidaten mit Power-Zeile.

**Stand 28.10. ≈ 21:20 (D66):** IBKR beendet; Paper für Aktien später über Alpaca-Paper (Pillar-Plan anpassen, falls je eine Aktien-Hypothese besteht). Keine IBKR-Rate-Limit-/Level-2-Arbeit mehr geplant.

### 5j. GO IBKR-STOP (ENTWURF 28.10. ≈ 21:35 Berlin; Folge von D66)
**Ergebnis 28.10. 20:25 UTC: OK** (siehe `01`/`02`). Danach offen: `ct109-paper-*` lesend prüfen (lf1-Bilanz 02.11.), IBKR-Secrets auf CT109 (ibkr.env, IBC) – Entfernen nur mit eigenem GO, IBKR-Marktdaten-Abos/Konto bei Andi.
Skript `code/ops/ibkr_stop_v1.sh`, SHA256 6c30a297a1c31f6382c7d3e245d6f178e70dfcb87e34e728e9eeb6521a040215. Zweck: IBKR-Collector, Watch-Timer und Gateway stoppen und am Boot-Start hindern. Risiken: Einheitennamen aus Dokumenten abgeleitet (nicht vorhanden ⇒ übersprungen); mögliche Alarme anderer Watcher wegen fehlender IBKR-Daten [A]; Gateway-Login beim Wiederstart nötig. Rollback: `systemctl enable --now ibgateway.service signal-ibkr.service signal-ibkr-watch.timer` (Login/Zweitfaktor ggf. nötig). Abbruch: `signal-kraken`/Ingestion/Compactor nicht mehr active, Kraken-Lücken. Daten und Siegel unberührt; Secrets (ibkr.env, IBC-Konfig) bleiben liegen, Entfernen = eigenes Thema/GO. GO-Satz: `GO IBKR-STOP – 6c30a297`.
