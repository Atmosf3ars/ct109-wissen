# CT109 – 04 PLAN

**Stand:** 23.10.2026 ≈ 09:45 Berlin (nach Übergabeprüfung und Bauspur-Start; Hostbelege weiter vom 22.10.). Der Plan des Owners (`10_TAGE_PLAN`, beschlossen 19.10., Original im ARCHIV) ist **Arbeitsplanung, kein GO**. Dieses Dokument enthält das Review des Einsatzleiters, den daraus folgenden Kurs und die nächsten Read-only-Aufträge.

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
| Sicherung Host-only-Arbeit (`/root/run` u. a.) | **P0 – E4 ausgewertet, E4b folgt, dann Sicherungs-GO** | E4: Masse ist Test-Venv-Ballast, Paper-Harness nie committet (`git log` leer). Secret-Scan war wegen Venv-Rauschen unbrauchbar → E4b (ohne Venvs). Sicherungs-GO danach nach Schablone Schritt 1: Tar der Werte (Harness, Skripte, Doku, Ledger-Kopien, `/root`-md/Patches) ohne `tmp-ro`/`fv`, ohne Secret-/Konfig-Dateien, **Kopie nach `D:` mit Hash (kein GitHub-Push vom Host)**. |
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
| **So 25.10.** | **Vormittags Freeze** der Liste (**höchstens 2**, nur 24/72 h) → Hash. **Nachmittags Discovery Regime A**, einmalig (Windows-Lauf, nur Aggregate zurück). EU-Zeitumstellung: alles UTC | Runner feature-complete (Datenpfad, Placebo, Logging); Äquivalenztest Runner = Backtest | Freeze-Hash bestätigen; Discovery-Befehl ausführen |
| **Mo 26.10.** | **Bestätigung nach Spec v2** (unberührte Vorhistorie), BH-FDR → ≤ 1 Kandidat oder Nullbefund | Mutationstests Runner (Doppel-Fill, Kosten=0, Lücken, Reboot, Zeitumstellung); **Zweitprüfung durch einen Claude-Agenten mit frischem Kontext** (kein Codex mehr, `02` D14) | Bestätigungs-Befehl ausführen |
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
**Danach:** das Paket `CT109_BAU_lf1_v0.1.1_2026-10-23.zip` (SHA-256 `00efc5b64839a56deafb104a5fdbf9743a44647295c02fc32e221c5faa6c24da`; v0.1.0 ist ersetzt; **seit 23.10. ≈ 10:15 UTC gilt v0.4.2, SHA-256 `56ab978682ad6ead0fecb42ed0351c5fe7e80c86ca8a29c29961ba7c9a2dfe84` [**v0.4.2 auf dem PC bestanden: 144 Tests OK, Code-Hash `3e708d6a…7726`, 23.10. ≈ 11:00 UTC**; v0.4.1 ersetzt: Windows-Lauf 21 Aufräumfehler durch offene SQLite-Handles, in v0.4.2 behoben; v0.2.0 `7c0a4ca4…addf` ist auf dem PC getestet; v0.4.2 enthält `confirm`, `epoch-q`, Runner, Statusseite]; danach Auftrag E-Q: `epoch-q` auf BTC, nur Zähler, Rückgabe `out\q_epochs.json`**) nach `D:\CT109-Bau\` legen, Hash prüfen, `README_RUN.md` im Paket Abschnitt 0–1 ausführen (Tests, Selbstprüfung). Gate-Ablauf erst nach meinem Signal am Sa 24.10.

## 6. Erfolgskriterien Schutzteil, Stand 29.10. (ersetzen E1–E6 des Owner-Plans, Owner-OK nötig)
- **E1 Code-Schutz:** V142 + Dirty-Arbeit nachweislich offhost und wiederherstellbar – oder präziser Blocker. (**Stand: GitHub PASS L5, Host-Hash PASS L3, Windows-Hash PASS L3**; offen nur optional Windows-Restore.)
- **E2 Daten-Schutz:** Sicherungsstatus der versiegelten Rohdaten geklärt (JA/NEIN) und Entscheid D3; **Registry-Kopie außerhalb des Containers (R1 + Kopie nach `D:`: erledigt 22.10., L3/L1) und tägliche Sicherung (R2) offen**; Host-only-Arbeit (`/root/run`) gesichert oder bewusst verworfen (E4b → GO offen).
- **E3 Kapazität:** Messreihe ≥ 5 Punkte; 30-Tage-Aussage oder BLOCKED; Thin-Pool-Alarm entworfen.
- **E4 Forschung:** Bewegungsbudget-Gate vorregistrierbar beschrieben (`GATE_SPEC_v1.md`, erledigt); sicherer Reader entworfen und synthetisch getestet; SOL = registrierte Hypothesen **oder** dokumentierter Nullbefund/BLOCKED; LF-1-Entwurf.
- **E5 Betrieb:** Lernbot bleibt aus; BTC/ETH-L2 bleibt aus.
- **E6 Doku:** 5 Dateien aktuell (+ Gate-Spec), Tagesabschluss = Änderungslog; **Wissensspeicher `ct109-wissen` als Wahrheit, Sicherungspaket auf `D:`** (`00` §8).
Stop-Regel bleibt: scheitert ein hartes Gate, keine Scope-Ausweitung, sondern Ursache und sichere Alternative.
