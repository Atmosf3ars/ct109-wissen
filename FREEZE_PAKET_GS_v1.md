# CT109 – FREEZE-PAKET GOLD-SILBER (GS, HINWEIS-Klasse) – Entwurf zur Freigabe

**Stand:** So 25.10.2026 ≈ 22:00 Berlin. Kein α-Konto-Verbrauch (HINWEIS-Klasse, D50/D51). Jede Änderung an einer Datei des Manifests ändert den Hash und macht ein neues GO nötig.

## 1 Was gefroren wird
| Reg.-Index | Test | Spec | Klasse |
|---|---|---|---|
| 12 | **GS** GOLD-SILBER wochenweise, GS-C (Fortsetzung) und GS-R (Umkehr) | `RUNDE3D_SPEC_v1_GS_FREEZEKANDIDAT.md` | HINWEIS (kein α, kein BESTAETIGT) |
α-Konto bleibt 7/20. Daten: GLD, SLV (Alpaca SIP, adjustment=all) 2016-01-04 … 2026-06-30, Hashes in `register/MANIFEST_GS_DATA_SHA256.txt`.

## 2 Manifest und Register
- `register/FREEZE_MANIFEST_GS.txt` (1 Spec, 2 Code-Dateien, 1 Datenmanifest, 4 Parameterzeilen). **FREEZE_HASH `405f212563447712aec313b8cf659bbc8b29208bd2924b9e33595ebb014f1b0a`** (`code/tools/freeze_gs_v1.py`).
- Registerzeile idx 12 (`kind` frozen, `status` FROZEN-HINWEIS, α_i = null), gekettet an Zeile 11 (`33a85bfd…`); wird erst **nach dem GO** angehängt. Vorschau-`entry_hash` `bbc9686d…`.
- Auf Andis PC bereits geprüft (L2): `gs_test_v1.py` SHA-Kurzform `008b120b…` und `count_gs_v1.py` `1af5deb5…` stimmen mit dem Repo; GLD/SLV-Datei-Hashes wie im Datenmanifest.

## 3 Ergebnis der Kalibrierung (Spec §5)
Fehlpass 0/200 je Seite; MDE80 29,4 bp/Woche ≈ 15,3 % p. a.; Power bei ½MDE ≈ 0–0,5 %, bei MDE 76,5 % (C) / 88,5 % (R). **Erwartung ≲ 5 % p. a. ≪ MDE ⇒ wahrscheinlichstes Ergebnis NICHT NACHWEISBAR (kein Nullbefund).**

## 4 GO-Schablone
- **Kurzname:** FREEZE-GS. **GO-Satz:** `GO FREEZE-GS – 405f2125`.
- **Zweck:** Regeln von GS festschreiben (Regel 3) und einmalig auf GLD/SLV ≤ 2026-06-30 laufen lassen; Andis Frage zu Gold/Silber mit Daten beantworten.
- **Exakte Aktion:** (1) Einsatzleiter: Registerzeile idx 12 an `register/TESTREGISTER.jsonl` anhängen, Manifest und Freeze-Eintrag in `01`/`02` committen und pushen (Repo, kein Host). (2) Andi: `run_gs_final.ps1` (`code/tools/`, SHA-Kurzform siehe 01) in den tools-Ordner legen und ausführen; der Lauf prüft zuerst zwei Code- und zwei Daten-Hashes gegen das Manifest und bricht bei Abweichung ab; Befehl: `cd D:\CT109-Data\kraken-trades\tools; .\run_gs_final.ps1`. Dauer ≈ 1–2 Minuten.
- **Risiken:** (a) Das Fenster wird einmal geöffnet, das Ergebnis zählt. (b) Zwei Seiten ohne Mehrfachtest-Korrektur: nur Hinweis. (c) Kosten (6 bp/Woche) und Leihegebühr sind Annahmen. (d) Kein Geld, kein Broker, keine Order, nur lesende Auswertung lokaler Dateien.
- **Rollback:** Vor dem Lauf: Registerzeile per `git revert` mit Vermerk „zurückgezogen vor Öffnung“. Nach dem Lauf: keiner.
- **Abbruchkriterien:** Hash-Abweichung ⇒ kein Lauf; Abbruch vor der ersten Ergebniszeile ⇒ Wiederholung mit unverändertem Code und Vermerk; nach Ergebnisausgabe zählt die erste Ausgabe.
- **Beleg:** `01` Einträge, D50/D51, Spec §5 (Kalibrierung), Manifest, Datenhashes.
