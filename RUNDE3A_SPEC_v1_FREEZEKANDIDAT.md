# CT109 – RUNDE-3A-SPEZIFIKATION v1 (FREEZE-KANDIDAT, NICHT GEHASHT)

**Status:** Kandidat des Einsatzleiters, Stand So 25.10.2026 ≈ 18:00 Berlin. Wird erst mit dem Freeze-Eintrag in `01_STATUS.md` (Datum, SHA256) **gültig**; bis dahin nur Änderungen mit Changelog unten. **Nach dem Freeze keine Änderung** (Änderung nur als v2 vor dem ersten Öffnen der Haupttest-Daten). Diese Datei ist **eigenständig**; Herleitung und Alternativen stehen in `RUNDE3_SPEC_v0.1_ENTWURF.md` (v0.2), Entscheidungen in `02` D28–D41. Bei Widerspruch gilt diese Datei.
**Evidenzstufen:** [L1] Herstellerangabe, [L2] von Andi gemessen und im Chat berichtet, [A] Annahme, [R] Recherche/Agent.

## 1 Gegenstand
Zwei bestätigende Haupttests (α-Konto D37, je α_i = 0,0025 einseitig, w = 1; Register-Index 5 und 6):
- **K4 AFTERSHOCK-LONG (XBT, ETH).**
- **K4P AFTERSHOCK-LONG-ALTS (39 Paare).**
Deskriptiv ohne α (HINWEIS): K1r FUND_CROWD, K5 WEEKEND-UMKEHR (Parameter in §9). Kein weiterer Test in dieser Welle. Offenlegung: lf1 H2 SHOCK_FADE (Nullbefund) ist ein verwandter Mechanismus; K4 zählt als eigener Test (D40/D41). Ausnahme von der HINWEIS-Regel: D41 (Prior-Kante 20–60 bp liegt teilweise unter MDE; nicht signifikant ⇒ **kein** Nullbefund).

## 2 Daten und Fenster
- **Quelle:** Kraken Time & Sales, 1-Minuten-Aggregate `agg_trades_v1.py` je Paar (`<NAME>USD_1m.csv`, Spalten minute_utc_epoch, open, high, low, close, vol, vol_b, vol_s, vol_m, n, notional). Die Rohdatei `Kraken_Trades_Full.zip` ist hashverifiziert (`01` T3); das **Manifest** der 41 verwendeten Aggregatdateien (SHA256 je Datei + Gesamt-Hash) wird im Freeze-Eintrag festgehalten.
- **Haupttest-Fenster:** 2019-01-01 00:00 UTC … 2026-06-30 23:59:59 UTC. **Hartes Ende:** jeder Lader verwirft Zeilen mit `ts ≥ 2026-07-01 00:00 UTC` (`count_events_v2.load`).
- **Vorwärtsfenster** 2026-07-01 … 2026-09-30 (im ZIP) bleibt unberührt und unaggregiert bis nach dem Haupttest; wird einmal je Test geöffnet (§8).
- **Datenbereinigung:** Zeile entfernt, wenn `low ≤ 0` oder `low < 0,7·high` oder `low < 0,7·close_prev_roh` oder `high > 1,4·close_prev_roh` (Vergleich mit der unmittelbar vorherigen **Rohzeile**). Entfernte Zeilen je Paar liegen bei 1–50 (längste Serie ≤ 8) [L2].
- **K4-Paare:** XBT, ETH. **K4P-Paare (ex ante, fest):** SOL, XRP, XDG, ADA, LTC, DOT, LINK, XMR, ZEC, XLM, BCH, ATOM, SUI, ALGO, PEPE, AVAX, TAO, FIL, UNI, TRX, AAVE, XTZ, FET, NEAR, SHIB, ETC, DASH, MANA, CRV, ICP, FARTCOIN, INJ, PENGU, ONDO, SEI, TIA, KAS, FLOW, TRUMP (Regel: USD-CSV ≥ 150 MB und gleichnamiger handelbarer Kraken-Perp am 25.10.2026 [L2, F6/F7]; ohne Stablecoins, Fiat, LUNA, MATIC). Paare mit später Historie tragen erst ab ihrem Startdatum und ab 30 Tagen σ₁₅-Vorlauf bei; es wird **nichts nachträglich** hinzugefügt oder entfernt.

## 3 Zustandsvariable
`RV30` = Standardabweichung der Tages-Log-Renditen (letzter Stundenschluss je UTC-Tag) von XBT über 30 Tage, ×√365. Zustandsperzentil `P` = Anteil der `RV30`-Werte der letzten 3 Jahre (1095 Tage, mindestens 365), die unter dem Wert des **Vortags** liegen. Zustand am Tag D: NIEDRIG (P < 1/3), MITTEL, HOCH (P > 2/3), berechnet nur aus Daten ≤ D−1. Gilt für K4 und K4P (Marktzustand über XBT). Kein Ereignis ohne Zustand.

## 4 Handelsregel (identisch für K4 und K4P, außer Auslöser und Kosten)
1. **Auslöser:** erste Minute `τ` (mit `τ ≥ 2019-01-01`), in der `low_τ / max(high der Minuten τ−14 … τ) − 1 ≤ −θ`. **K4:** θ = 3 %. **K4P:** θ = max(3 %, 6·σ̂₁₅), σ̂₁₅ = Wurzel des Mittels der quadrierten 15-Minuten-Log-Renditen (auf ±15 % gekappt) der 30 UTC-Tage **vor** dem laufenden Tag (mind. 20 Tage mit Daten, sonst kein Auslöser).
2. **Sperre:** kein neuer Auslöser vor Ablauf der Sperrzeit (bei Trade: 6 h nach Ausstieg; ohne Einstieg: 1 h nach τ).
3. **Einstieg:** frühestens `τ + 20 min`; erste Minute `t_e`, in der seit dem Tiefstwert nach τ mindestens 10 Minuten **kein neues Tief** entstand; spätestens `τ + 120 min`, sonst kein Trade (gezählt). Long **Taker** zum Open der ersten Minute ≥ `t_e + 60 s` (Toleranz 600 s, sonst kein Trade).
4. **Ausstieg:** Open der ersten Minute ≥ Einstiegszeit + 4 h (Toleranz 600 s); oder **Stop** bei `entry·(1−5 %)`: Fill zum kleineren von Stop und Open der Stop-Minute **abzüglich 10 bp** (A-C4).
5. **Netto-Rendite je Trade (bp):** `ln(Exit/Entry)·10⁴ − Rundreise`. **Rundreise K4:** 2·(5 + 3) = 16 bp; **K4P:** 2·(5 + 8) = 26 bp [A-C3, A-C5]. Funding im 4-h-Fenster wird **nicht** abgezogen (Annahme A-C2: vernachlässigbar, ≤ 1 Settlement); wird im Paper gemessen.
6. **Episode:** Auslöser-Einstiege aller Paare des Tests, sortiert nach Einstiegs-Auslösezeit, bilden eine Episode, solange der Abstand zum vorherigen Einstieg < 24 h bleibt. Episodenrendite = Mittel je Paar, dann Mittel über Paare. Episodenzeit = erster Einstieg; Zustand = Zustand des ersten Einstiegs.
7. **Position (Echtgeld, später):** Notional ≤ 600 EUR je Position (D34). Für Paper/Test ohne Größeneinfluss.

## 5 Hauptstatistik und Kriterien (je Test einzeln)
- **m** = Mittel der Episoden-Netto-bp.
- **C2:** Moving-Block-Bootstrap über **Kalenderwochen** (Wochenindex ab 2019-01-01 UTC, Blocklänge 4, 10 000 Ziehungen, Seed 20261025, ohne Zinseszins): `p = Anteil(m* ≤ 0) ≤ α_i = 0,0025` **und** `Quantil_{α_i}(m*) > 0`.
- **C3 Placebos** (beide müssen unterschritten werden): (a) 2000 Zeitversatz-Läufe (Ereignisuhren um ganze Wochen ±4…±52, Zustand beibehalten, dieselbe Regel): `m > Quantil_{0,975}`; (b) 500 vol-gematchte Pseudo-Auslöser (gleiche Uhrzeit, anderer Tag ohne reale Auslöser ±48 h, gleiches RV24h-Dezil): `m > Quantil_{0,975}`.
- **C4 Stress** (je `m > 0`): (a) Kosten × 1,5; (b) Einstieg 1 Minute später; (c) Slippage × 2 im Zustand HOCH.
- **C5 Konzentration:** die 3 größten Gewinn-Episoden ≤ 40 % des Bruttogewinns; kein Kalenderjahr > 50 % des Gesamtnetto (nur bei m > 0).
- **C6 Konsistenz:** Mittelwert in beiden Zeithälften (nach Episodenzahl halbiert) > 0 **und** in ≥ 2 Zuständen mit je ≥ 20 Episoden > 0.
- **C7 Kalibrierung** (bestanden, `01` 25.10. ≈ 16:30, D41): Fehlpass 0/200 je Test; Gesamtregel-Power bei ½·MDE / MDE / 2·MDE: K4 12 / 70 / 100 % (MDE 51 bp), K4P 15 / 77 / 100 % (MDE 40 bp); Annahme: Nullwelten auf gezählte Streuung skaliert (K4 310 bp, K4P 411 bp je Einstieg).
- **Kategorien:** `BESTAETIGT` (C2 ∧ C3 ∧ C4 ∧ C5 ∧ C6); `NICHT BESTAETIGT` (C2 erfüllt, ein anderes Kriterium verfehlt, mit Angabe); `POSITIV-UNTERPOWERT` (m > 0, C2 verfehlt); `NICHT NACHWEISBAR` (m ≤ 0; **kein Nullbefund**, solange Prior-Kante < MDE). „0 Trades“ ist INSUFFICIENT.
- **Beschreibende Ausgaben ohne Testanspruch:** Mittel je Zustand, je Zeithälfte, je Jahr, Anzahl Einstiege und Episoden, Anteil Trades mit Stop.

## 6 Code und Läufe
- **Code:** `code/tools/k4_test_v1.py` (Modus `final`, Pflichtargument `--spec-hash`), `count_events_v2.py` (Lader), `count_events_v3.py` (σ₁₅-Funktion). Code-Hash (SHA256 der drei Dateien) und Skript-Hash der Ausgabe stehen im Freeze-Eintrag.
- **Lauf:** einmalig je Test auf Andis PC: `python -u k4_test_v1.py final <agg> XBT,ETH --spec-hash <Hash>` und `… final <agg> <39 Paare> --spec-hash <Hash>`; Ausgabe nur Aggregate. Jeder Lauf erzeugt eine Registerzeile (`register/TESTREGISTER.jsonl`), auch Abbrüche.
- **Reihenfolge:** erst Freeze, dann Lauf K4, dann Lauf K4P; kein Zwischenblick, keine Änderung nach Lauf.

## 7 Ehrliche Erwartung (Evidenz)
- Power des Haupttests bei wahrer Netto-Kante 25 / 40 / 60 bp: K4 ≈ 12 / 45 / 80–85 %; K4P ≈ 30 / 75 / 95 % [L2/A, interpoliert].
- Literaturkante 100–180 bp [A, vermutlich optimistisch]; Prior des Einsatzleiters 20–60 bp [A]. Ein negatives oder nicht signifikantes Ergebnis ist **kein** Beleg für Abwesenheit.

## 8 Vorwärtsfenster und Paper
Nach dem Haupttest einmal je Test: Aggregation 2026-07-01 … 2026-09-30 mit demselben Code (Fensterargument), Ausgabe nur Aggregate, Zweck Konsistenz-/Betriebsprüfung (n klein). Paper-Säulen A–D (Spec v0.2 §10) werden **vor Paper-Start** separat gehasht. Echtgeld nur nach `BESTAETIGT` ∧ Paper-Freigabe ∧ zwei Schlüssel (D27) im Deckel D34.

## 9 Deskriptive Hypothesen ohne α (HINWEIS)
- **K1r:** Binance-Funding relativ (positiv: `f ≥ max(2 bp, P97,5 der letzten 270 Settlements)`; negativ gespiegelt), BTC/ETH/SOL; Episoden 72 h; berichtet werden Anzahl und Zerlegung Preis/Funding, kein p-Wert als Testanspruch.
- **K5:** Wochenend-Umkehr XBT (|R_W| ≥ k·σ_W, k ∈ {1,0; 1,5; 2,0}); Anzahl und Mittel, kein Testanspruch.

## 10 Offene Punkte vor dem Freeze
1. Manifest-Hash der 41 Aggregatdateien (Andi, Get-FileHash) und Code-Hash.
2. Unabhängige Nachrechnung des Spec-Hashs durch den Einsatzleiter (anderes Werkzeug).
3. Registerzeilen 5/6 vorbereiten; **GO-Schablone** für den Registry-Schreibakt (Andi).
4. Endlektüre durch Andi (Ausnahme D41 ablehnen oder bestätigen).

## 11 Changelog
- 25.10.2026 ≈ 18:00 Berlin: Kandidat angelegt.
