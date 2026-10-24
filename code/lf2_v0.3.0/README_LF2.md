# lf2 v0.3.0 – Aktien-Tagesquerschnitt (RUNDE2_SPEC_v1)

Python 3.14 + numpy (Andis PC). Ordner: `D:\CT109-Bau\lf2_v0.3.0`. Rohdaten bleiben auf dem PC (Lizenz: nur eigene Nutzung);
nach jedem Befehl geht nur die Ausgabe (Zaehler, Hashes, Kennzahlen) an den Chat.

1. Tests: `python -W ignore -m unittest discover -s tests` (alle muessen OK sein), dann `python -m lf2 selfcheck`.
2. (erledigt mit v0.1.0) `universe`, `fetch` -> `D:\CT109-Data\tiingo\universe.json`, `prices\`, `manifest.json` (Abruf ca. 10 h).
3. `python -m lf2 qcount --data D:\CT109-Data\tiingo` – nur Zaehler (Spec R8 Schritt 4), schreibt einmalig `qcount_S.json` (Voraussetzung fuer `gate`).
4. `python -m lf2 gate --data D:\CT109-Data\tiingo` – Gate S, einmalig, schreibt `gate_result_S.json`.
5. `python -m lf2 freeze --data D:\CT109-Data\tiingo --specs specs` – einmalig, schreibt `freeze.json`;
   Ordner `specs` (im Paket enthalten) muss `RUNDE2_SPEC_v1.md`, `GATE_SPEC_v1.md`, `BAU_SPEC_S1S3_v2.md` enthalten (Hash-Waechter).
6. `python -m lf2 backtest --data D:\CT109-Data\tiingo --stage discovery_A` – Stufe D (beschreibend), einmalig (nur nach technischem Fehler mit `--retry`, wird in der Sperre protokolliert).
7. `python -m lf2 backtest --data D:\CT109-Data\tiingo --stage confirm` – Stufe B (E und F), einmalig, braucht Schritt 6.
Alle Schritte verweigern bei Abweichung (Spec-/Code-/Datenhash) und bei vorhandener Sperre/Ergebnisdatei.
Kategorien: nie `BESTAETIGT` (R7), hoechstens `HINWEIS-POSITIV (survivorship-behaftet)`.
Nachtrag N1 (24.10., vor jeder Preisansicht): Blocklaenge des Bootstraps = max(20, 4·H) statt fest 20 (H = 21: 84), weil ueberlappende
Kohorten sonst den Standardfehler zu klein schaetzen (Simulation; Restunterschaetzung ca. 8 %). Strenger, nicht lockerer.
Nachtrag N2: zusaetzlich zum Tages-Placebo (C3) muss ein Spalten-Placebo (C3b: echte Score-Verlaeufe zufaellig anderen Aktien zugeordnet) bestanden werden.
Kostenstress skaliert auch die Leihe. Gate-Ergebnis ist an Daten- und Code-Hash gebunden; Reihenfolge qcount -> gate -> freeze wird erzwungen.
