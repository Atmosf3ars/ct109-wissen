# CT109 – FREEZE-PAKET ORB (Opening Range Breakout, HINWEIS-Klasse) – Entwurf zur Freigabe

**Stand:** Mo 26.10.2026 ≈ 19:20 Berlin. Auftrag Andi „orb mit 2020 – 2026“. Kein α-Konto-Verbrauch (HINWEIS-Klasse, Spec §5), α-Konto bleibt 7/20. Jede Änderung an einer Datei des Manifests ändert den Hash und macht ein neues GO nötig.

## 1 Was gefroren wird
| Reg.-Index | Test | Spec | Klasse |
|---|---|---|---|
| 16 | **ORB Stocks-in-Play** (Top-20 je Tag nach RV5, Kerzenrichtung 09:30, Stop Gegenende, Ziel 10 R), Testfenster 2020-01-02 … 2026-06-30, Primärkosten 0,70 USD + 5 bp je Seite | `RUNDE3F_SPEC_v1_ORB_FREEZEKANDIDAT.md` | HINWEIS (kein α, kein BESTAETIGT) |

## 2 Manifest und Register
- `register/FREEZE_MANIFEST_ORB.txt` (1 Spec, 12 Code-Dateien, 4 Entwicklungs-Ergebnisdateien, 6 Parameterzeilen). **FREEZE_HASH `662a156fce8a3c432676a21967d8bb9712597daf4cafb2e6db7b70ec576b336d`** (`code/tools/freeze_orb_v1.py`).
- Registerzeile idx 16 (`kind` frozen, `status` FROZEN-HINWEIS, α_i = null), gekettet an Zeile 15 (`5f3dae1e…`); wird erst **nach dem GO** angehängt. Vorschau-`entry_hash` `1ac71a16…`.
- Code-Prüfung: `run_orb_data.ps1` und `run_orb_final.ps1` vergleichen die 5 auf dem PC ausgeführten Dateien (`orb_test_v1.py`, `orb_select_v2.py`, `alpaca_intraday_v1.py`, `alpaca_day5_v1.py`, `alpaca_daily_v1.py`) mit den Manifest-Hashes und brechen bei Abweichung ab.
- Trockenlauf (Entwicklungsfenster, `orb_test_v1.py dry`) reproduziert die Entwicklungs-Simulation exakt (n 19 207, brutto +0,0562 R, Differenz −0,0087 R, 10:30-Placebo +0,1130 R); Auswahl-Tool v2 reproduziert die v1-Auswahl byte-genau.
- **Datenmanifest:** Die Testfenster-Daten existieren noch nicht. `run_orb_final.ps1` schreibt vor dem Lauf `orb_test_data_manifest.txt` (SHA-256 aller Testfenster-Dateien); dessen Hash wird mit dem Ergebnis registriert.

## 3 Erwartung (Spec §1, §5)
Vorbefund Entwicklung negativ (Zufallsrichtung gleich gut, Netto −0,014 … −0,163 R). **Wahrscheinlichstes Ergebnis: NICHT NACHWEISBAR mit negativer Punktschätzung.** Nutzen: unabhängige Widerlegung/Bestätigung in 2020–2026H1 und endgültiger Abschluss der Familie (Paper-Literatur überschneidet sich mit 2020–2023).

## 4 GO-Schablone
- **Kurzname:** FREEZE-ORB. **GO-Satz:** `GO FREEZE-ORB – 662a156f`.
- **Zweck:** Regeln von ORB festschreiben (Regel 3) und das Testfenster 2020–2026H1 **einmal** öffnen.
- **Exakte Aktion:** (1) Einsatzleiter: Registerzeile idx 16 an `register/TESTREGISTER.jsonl` anhängen (`python3 code/tools/freeze_orb_v1.py --append`), `01`/`02` committen und pushen (Repo, kein Host). (2) Andi: `run_orb_data.ps1` (≈ 2 h, mit Wiederaufnahme; Alpaca-Schlüssel als Umgebungsvariablen; ≈ 3 000 Abrufe bei 150/min, Limit 200/min) — lädt Testfenster-Daten, keine Auswertung. (3) Andi: `run_orb_final.ps1` (Minuten) — prüft Code-Hashes, schreibt das Datenmanifest, führt den Test einmal aus. Befehle: `cd D:\CT109-Data\kraken-trades\tools; .\run_orb_data.ps1` und danach `.\run_orb_final.ps1`.
- **Risiken:** (a) Das Testfenster wird einmal geöffnet, das Ergebnis zählt. (b) Slippage 5 bp je Seite ist eine Annahme, keine Quote-Messung. (c) Rate-Limit/Dauer (≈ 2 h Last auf Alpaca-Basic, keine Kosten). (d) Alpaca-AGB für lokale Eigenforschung ungeklärt; Daten bleiben lokal. (e) Erwartung ≤ 0 ⇒ NICHT NACHWEISBAR ist kein Nullbefund im strengen Sinn. (f) Kein Geld, kein Broker, keine Order.
- **Rollback:** Vor dem Datenlauf: Registerzeile per `git revert` mit Vermerk „zurückgezogen vor Öffnung“. Nach dem Lauf: keiner.
- **Abbruchkriterien:** Hash-Abweichung ⇒ kein Lauf; Datenlauf unvollständig (Fehltage > 0) ⇒ Wiederholung desselben Befehls, dann erst `run_orb_final.ps1`; nach Ergebnisausgabe zählt die erste Ausgabe.
- **Beleg:** `03` §8.27–§8.31, D62/D63, Spec, Manifest, `register/results/orb_dev_sim_v*_out.txt`, `orb_first5_out.txt`, `orb_count_v2b_out.txt`.
