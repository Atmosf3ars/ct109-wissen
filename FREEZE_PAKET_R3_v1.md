# CT109 – FREEZE-PAKET WELLE 3 (K4, K4P, K6) – Entwurf zur Freigabe

**Stand:** So 25.10.2026 ≈ 17:30 Berlin, Endlektüre erfolgt. Der Hash unten ist der **zur Freigabe vorgelegte Endkandidat**; jede Änderung an einer Datei des Manifests ändert ihn und macht ein neues GO nötig.

## 1 Was gefroren wird
| Reg.-Index | Test | Spec | Pool | α_i |
|---|---|---|---|---|
| 5 | **K4** AFTERSHOCK-LONG | `RUNDE3A_SPEC_v1_FREEZEKANDIDAT.md` | XBT, ETH | 0,0025 |
| 6 | **K4P** AFTERSHOCK-LONG-ALTS | dito | 32 Paare (D45) | 0,0025 |
| 7 | **K6 FLOW** (C und R) | `RUNDE3B_SPEC_v1_FREEZEKANDIDAT.md` | 34 Paare (D44) | 0,0025, je Seite 0,00125 |
Konto danach: 7 von 20 verbraucht (4 Altlast + 3), 13 frei. Altlast-Zeilen 1–4 (lf1 H1/H2, lf2 R-H1/R-H2) stehen mit ihren Freeze-/Ergebnis-Hashes im Register-Entwurf.

## 2 Manifest und Register (Endkandidat 25.10.)
- `register/FREEZE_MANIFEST_R3.txt` (2 Specs, 7 Code-Dateien, 3 Daten-/Pool-Listen, 6 Parameterzeilen). **FREEZE_HASH (Endkandidat) `830bac6d59d10756c6ecd338270e083b4ccf1b74366a126f19eb27c67077a2a2`**, mit `sha256sum`, `openssl` und `node` identisch nachgerechnet (`code/tools/verify_freeze_r3.sh`), alle 12 Dateihashes einzeln identisch [L3, Sandbox].
- Code-Dateien auf Andis PC gegen das Repo (Hash je Datei): **5 von 7 byte-gleich** (`k6_test_v1`, `count_events_v2/v3/v4`, `count_cs_v1`). `k4_test_v1.py` auf dem PC ist die Vorversion `43807483…` (C7-Läufe); das Repo hat `d253f1a6…` – Unterschied nur in `final()`-Ausgabe (Diff geprüft). Die PC-Datei wird **nach dem GO** durch die gefrorene Version ersetzt, `run_r3_final.ps1` prüft vor dem Start alle Code-Hashes und bricht bei Abweichung ab. `agg_trades_v1.py` (nur Aggregation, nicht Teil der Tests) unterscheidet sich nur in Kommentaren, BOM und CRLF (Diff geprüft) [L3]. Trockenläufe `final` (K4, K6) auf synthetischen Daten fehlerfrei [L3].
- `register/TESTREGISTER_ENTWURF.jsonl`: 7 Zeilen, hashgekettet (`entry_hash = SHA256(prev + "\n" + kanonisches JSON)`, Genesis `prev` = 64 Nullen). **Mit dem GO zu `register/TESTREGISTER.jsonl` geworden (25.10. 17:21, plus Freeze-Event-Zeile 8);** Ergebnisse werden später als weitere Zeilen angehängt (auch Abbrüche).

## 3 Offene Punkte vor dem GO
1. ~~Pool-Filter K4P/K6, C7 beider~~ erledigt (D44, D45).
2. ~~Endlektüre der beiden Specs~~ erledigt 25.10. (Widerspruch „kein weiterer Test in dieser Welle“ in 3A behoben, Uhrzeiten bereinigt, Versionshinweis `k4_test_v1` ergänzt).
3. ~~Freeze-Hash~~ Endkandidat siehe §2. **Fehlt nur noch: Andis GO-Satz.**
4. Paper-Säulen A–D werden **nicht** jetzt gehasht, sondern vor Paper-Start separat (Spec 3A §8). Vorwärtsfenster-Skript: erst nach den Haupttests.

## 4 GO-Schablone (wird am Freeze-Tag mit dem endgültigen Hash ausgefüllt)
- **Kurzname:** FREEZE-R3. **GO-Satz:** `GO FREEZE-R3 – 830bac6d`.
- **Zweck:** Hypothesen und Parameter von K4, K4P, K6 verbindlich festschreiben (Doktrin Regel 3), α-Konto belasten, danach einmalig die Haupttests auf den Daten ≤ 2026-06-30 laufen lassen.
- **Exakte Aktion (Einsatzleiter, Repo, kein Host):** `register/FREEZE_MANIFEST_R3.txt` und `register/TESTREGISTER.jsonl` (7 Zeilen) ins Repo `ct109-wissen` committen und pushen; Freeze-Eintrag in `01`/`02`. **Vor dem Lauf (Einsatzleiter, nur Kopieren in den Tools-Ordner):** gefrorenes `k4_test_v1.py` und `run_r3_final.ps1` auf Andis PC legen, Hashes dort prüfen. **Dann (Andi, PowerShell, ein Skript):** `code/tools/run_r3_final.ps1` (SHA256 `05f7c64b23e208b8bfdb851e4f6456d29470e4a659794e6a992b045a8bb30530`; prüft vor dem Start alle sechs Code-Hashes und bricht bei Abweichung ab; startet nicht, wenn `r3_final_k4.txt` schon existiert), das nacheinander `k4_test_v1.py final` (XBT,ETH), `k4_test_v1.py final` (32 Paare) und `k6_test_v1.py final` (34 Paare) mit `--spec-hash <FREEZE_HASH>` ausführt; Ausgabe nur Aggregate.
- **Risiken:** (a) Ein bestätigender Lauf ist unumkehrbar – jedes Fenster wird nur einmal geöffnet. (b) Ergebnis kann ernüchternd sein; die Specs deklarieren: nicht signifikant ⇒ **kein** Nullbefund, Kante unter MDE. (c) Rechenzeit PC ≈ 1–2 h gesamt [A]. (d) Kein Geld, kein Broker, keine Secrets.
- **Rollback:** Vor dem Lauf: Freeze-Commit per `git revert` zurücknehmbar, solange kein `final` gelaufen ist (Register-Zeilen bleiben, mit Vermerk „zurückgezogen vor Öffnung“). Nach dem Lauf: kein Rollback, das Ergebnis zählt.
- **Abbruchkriterien:** (1) Hash-Prüfung auf Andis PC (Code, Manifest) weicht ab ⇒ kein Lauf. (2) Ein `final`-Lauf bricht **vor der ersten Ergebniszeile** ab (z. B. Datei fehlt) ⇒ Wiederholung nur mit unverändertem Code, mit Vermerk; bricht er **nach** Ergebnisausgabe ab, zählt die erste Ausgabe, keine Wiederholung. (3) Jede Codeänderung nach Freeze ⇒ neuer Freeze (v2) vor einem Lauf.
- **Beleg:** `01` Einträge zu D37–D45, C7-Tabellen in Spec 3A §5 und 3B §6, Manifest + dreifach identischer Hash, Pool-Listen mit Ticker-Beleg-Hashes (D44).
