# CT109 – FREEZE-PAKET WELLE 3 (K4, K4P, K6) – Entwurf zur Freigabe

**Stand:** So 25.10.2026 ≈ 17:45 Berlin. Alles unten ist **Vorschau**, bis der Freeze-Hash am Freeze-Tag neu gerechnet und im GO genannt wird. Jede Änderung an einer Datei des Manifests ändert den Hash.

## 1 Was gefroren wird
| Reg.-Index | Test | Spec | Pool | α_i |
|---|---|---|---|---|
| 5 | **K4** AFTERSHOCK-LONG | `RUNDE3A_SPEC_v1_FREEZEKANDIDAT.md` | XBT, ETH | 0,0025 |
| 6 | **K4P** AFTERSHOCK-LONG-ALTS | dito | 32 Paare (D45) | 0,0025 |
| 7 | **K6 FLOW** (C und R) | `RUNDE3B_SPEC_v1_FREEZEKANDIDAT.md` | 34 Paare (D44) | 0,0025, je Seite 0,00125 |
Konto danach: 7 von 20 verbraucht (4 Altlast + 3), 13 frei. Altlast-Zeilen 1–4 (lf1 H1/H2, lf2 R-H1/R-H2) stehen mit ihren Freeze-/Ergebnis-Hashes im Register-Entwurf.

## 2 Manifest und Register (Vorschau 25.10.)
- `register/FREEZE_MANIFEST_R3.txt` (2 Specs, 7 Code-Dateien, 3 Daten-/Pool-Listen, 6 Parameterzeilen). **Vorschau-FREEZE_HASH `789a8a74270fd182f1fee16c77b95222ad5e24121ad726c51dc6371b1d5dd6c0`**, mit `sha256sum`, `openssl` und `node` identisch nachgerechnet (`code/tools/verify_freeze_r3.sh`), alle 12 Dateihashes einzeln identisch [L3, Sandbox].
- Code-Dateien auf Andis PC gegen das Repo geprüft: 6 von 7 byte-gleich. `agg_trades_v1.py` (nur Aggregation, nicht Teil der Tests, Aggregate sind über das Manifest der 41 Dateien gesichert) unterscheidet sich **nur** in drei Kommentaren, BOM und CRLF (Diff geprüft, Programmzeilen identisch) [L3].
- `register/TESTREGISTER_ENTWURF.jsonl`: 7 Zeilen, hashgekettet (`entry_hash = SHA256(prev + "\n" + kanonisches JSON)`, Genesis `prev` = 64 Nullen). Wird mit dem GO zu `register/TESTREGISTER.jsonl`; Ergebnisse werden später als weitere Zeilen angehängt (auch Abbrüche).

## 3 Offene Punkte vor dem GO
1. ~~Pool-Filter K4P/K6, C7 beider~~ erledigt (D44, D45).
2. Letzte Endlektüre der beiden Specs durch den Einsatzleiter (Widersprüche, Verweise, Zahlen) – vor dem Freeze-Tag.
3. Freeze-Hash am Freeze-Tag neu rechnen und im GO nennen.
4. Paper-Säulen A–D werden **nicht** jetzt gehasht, sondern vor Paper-Start separat (Spec 3A §8). Vorwärtsfenster-Skript: erst nach den Haupttests.

## 4 GO-Schablone (wird am Freeze-Tag mit dem endgültigen Hash ausgefüllt)
- **Kurzname:** FREEZE-R3. **GO-Satz:** `GO FREEZE-R3 – <erste 8 Zeichen des FREEZE_HASH>`.
- **Zweck:** Hypothesen und Parameter von K4, K4P, K6 verbindlich festschreiben (Doktrin Regel 3), α-Konto belasten, danach einmalig die Haupttests auf den Daten ≤ 2026-06-30 laufen lassen.
- **Exakte Aktion (Einsatzleiter, Repo, kein Host):** `register/FREEZE_MANIFEST_R3.txt` und `register/TESTREGISTER.jsonl` (7 Zeilen) ins Repo `ct109-wissen` committen und pushen; Freeze-Eintrag in `01`/`02`. **Danach (Andi, PowerShell, ein Skript):** `run_r3_final.ps1` (Hash im GO), das nacheinander `k4_test_v1.py final` (XBT,ETH), `k4_test_v1.py final` (32 Paare) und `k6_test_v1.py final` (34 Paare) mit `--spec-hash <FREEZE_HASH>` ausführt; Ausgabe nur Aggregate.
- **Risiken:** (a) Ein bestätigender Lauf ist unumkehrbar – jedes Fenster wird nur einmal geöffnet. (b) Ergebnis kann ernüchternd sein; die Specs deklarieren: nicht signifikant ⇒ **kein** Nullbefund, Kante unter MDE. (c) Rechenzeit PC ≈ 1–2 h gesamt [A]. (d) Kein Geld, kein Broker, keine Secrets.
- **Rollback:** Vor dem Lauf: Freeze-Commit per `git revert` zurücknehmbar, solange kein `final` gelaufen ist (Register-Zeilen bleiben, mit Vermerk „zurückgezogen vor Öffnung“). Nach dem Lauf: kein Rollback, das Ergebnis zählt.
- **Abbruchkriterien:** (1) Hash-Prüfung auf Andis PC (Code, Manifest) weicht ab ⇒ kein Lauf. (2) Ein `final`-Lauf bricht **vor der ersten Ergebniszeile** ab (z. B. Datei fehlt) ⇒ Wiederholung nur mit unverändertem Code, mit Vermerk; bricht er **nach** Ergebnisausgabe ab, zählt die erste Ausgabe, keine Wiederholung. (3) Jede Codeänderung nach Freeze ⇒ neuer Freeze (v2) vor einem Lauf.
- **Beleg:** `01` Einträge zu D37–D45, C7-Tabellen in Spec 3A §5 und 3B §6, Manifest + dreifach identischer Hash, Pool-Listen mit Ticker-Beleg-Hashes (D44).
