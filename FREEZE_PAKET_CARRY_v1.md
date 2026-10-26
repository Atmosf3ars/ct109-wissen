# CT109 – FREEZE-PAKET CARRY-HOLD (HINWEIS-Klasse) – Entwurf zur Freigabe

**Stand:** Mo 26.10.2026 ≈ 09:00 Berlin. Kein α-Konto-Verbrauch (HINWEIS-Klasse, D58). Jede Änderung an einer Datei des Manifests ändert den Hash und macht ein neues GO nötig.

## 1 Was gefroren wird
| Reg.-Index | Test | Spec | Klasse |
|---|---|---|---|
| 14 | **CARRY-HOLD** Binance-Proxy BTCUSDT+ETHUSDT (Long Spot / Short Perp), Primärregel E 10 % / X 3 %, Testfenster 2024-01-01 … 2026-06-28 (130 Wochen) | `RUNDE3E_SPEC_v1_CARRYHOLD_FREEZEKANDIDAT.md` | HINWEIS (kein α, kein BESTAETIGT) |
α-Konto bleibt 7/20. Daten: 322 Dateien (Binance-Vision 1d-Monatsdateien Spot/Perp, Binance-Funding), Hashes in `register/MANIFEST_CARRY_DATA_SHA256.txt`.

## 2 Manifest und Register
- `register/FREEZE_MANIFEST_CARRY.txt` (1 Spec, 5 Code-Dateien, 1 Datenmanifest, 6 Parameterzeilen). **FREEZE_HASH `72a5c862d2268de6a71126481710179c33b9681b513f9cc8304878c52c256b37`** (`code/tools/freeze_carry_v1.py`).
- Registerzeile idx 14 (`kind` frozen, `status` FROZEN-HINWEIS, α_i = null), gekettet an Zeile 13 (`dbe03434…`); wird erst **nach dem GO** angehängt. Vorschau-`entry_hash` `bcb40497…`.
- Auf Andis PC geprüft (L2/G): `carry_test_v1.py` SHA-Kurzform `5e0554a1…` und Datenmanifest `19bfc194…` stimmen mit dem Repo; Trockenlauf im Training (`dry`) mit genau diesem Code unverändert.

## 3 Ergebnis der Vorarbeit (Spec §5, §6)
Nullwelten (1 200): wahrer SE ≈ 2,0 × naiv; Fehlpass des HINWEIS-Kriteriums 2,4–4,3 %. MDE ≈ 9,6–10,5 bp/Woche gegen Erwartung 4,1 bp/Woche (zweite Trainingshälfte) bis 6–14 bp/Woche (externe Schätzung [A]) ⇒ **wahrscheinlichstes Ergebnis NICHT NACHWEISBAR; Nutzen = Punktschätzung mit Intervall im heutigen Regime.**

## 4 GO-Schablone
- **Kurzname:** FREEZE-CARRY. **GO-Satz:** `GO FREEZE-CARRY – 72a5c862`.
- **Zweck:** Regeln von CARRY-HOLD festschreiben (Regel 3) und einmalig im Testfenster 2024-01 … 2026-06 auswerten; Wirtschaftlichkeit des gehaltenen Carry im Niedrig-Funding-Regime messen; Vorwärtsbeobachtung begründen oder nicht.
- **Exakte Aktion:** (1) Einsatzleiter: Registerzeile idx 14 an `register/TESTREGISTER.jsonl` anhängen, Manifest und Freeze-Eintrag in `01`/`02` committen und pushen (Repo, kein Host). (2) Andi: `run_carry_final.ps1` (`code/tools/`) in den tools-Ordner legen und ausführen; der Lauf prüft zuerst Code- und alle 322 Datenhashes gegen das Manifest und bricht bei Abweichung ab; Befehl: `cd D:\CT109-Data\kraken-trades\tools; .\run_carry_final.ps1`. Dauer ≈ 2–4 Minuten.
- **Risiken:** (a) Das Testfenster wird einmal geöffnet, das Ergebnis zählt. (b) Binance-Proxy statt Kraken-Daten: Funding/Basis können abweichen; Kosten (90 bp je Phase, 0,5 bp/Woche Reibung) sind Annahmen. (c) Erwartung unter der Auflösung ⇒ „NICHT NACHWEISBAR“ ist kein Nullbefund. (d) Kein Geld, kein Broker, keine Order, nur lesende Auswertung lokaler Dateien.
- **Rollback:** Vor dem Lauf: Registerzeile per `git revert` mit Vermerk „zurückgezogen vor Öffnung“. Nach dem Lauf: keiner.
- **Abbruchkriterien:** Hash-Abweichung ⇒ kein Lauf; Abbruch vor der ersten Ergebniszeile ⇒ Wiederholung mit unverändertem Code und Vermerk; nach Ergebnisausgabe zählt die erste Ausgabe.
- **Beleg:** `01` Einträge, D53/D56/D58, Spec §5/§6, Manifest, Datenhashes, `register/results/carry_null_v1_out.txt`, `carry_dry_train.txt`.
