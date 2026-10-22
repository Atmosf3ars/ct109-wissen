# ct109-wissen

Wissensspeicher für CT109 („Neues Signalsystem“). Privates Repo, **nur Dokumentation**, kein Code, keine Zugangsdaten, keine Rohdaten.

## Regeln
1. **Git ist die Wahrheit** für `00`–`04`, `GATE_SPEC_v1.md` und `ARCHIV/INDEX.md`. Das Claude-Projekt und das Paket auf `D:` sind Kopien.
2. **Der Host (CT109) hat keinen Zugriff** auf dieses Repo (der Deploy-Key gilt nur für `new-signal-system`).
3. **`GATE_SPEC_v1.md` ist unveränderlich** (SHA-256 `acaed785b2a0e7b5e7fa2f74565e6d1b5250e1ef793a3d5c768d6771d59d5be7`, geschrieben vor jedem Datenblick). Änderungen nur als `GATE_SPEC_v2.md` vor Datenzugriff; die Datei v1 wird nie überschrieben.
4. Keine stillen Streichungen: Änderungen stehen im Änderungslog von `01_STATUS.md`.
5. Keine Secrets, Schlüssel, Passwörter, Kontonummern. Öffentliche Fingerprints und Hashes sind erlaubt.
6. Details zu Evidenzstufen, GO-Verfahren und Übergabe: `00_START_HIER.md` (§3, §4, §8).

## Inhalt
| Pfad | Zweck |
|---|---|
| `GATE_SPEC_v1.md` | eingefrorene Gate-Spezifikation (LF-1 Bewegungsbudget-Gate) |
| `00_START_HIER.md` … `04_PLAN.md` | Regeln, Status, Entscheidungen/GO, Forschung, Plan |
| `ARCHIV/INDEX.md` | Zuordnung alt → neu mit SHA-256 |
