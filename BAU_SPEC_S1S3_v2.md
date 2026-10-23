# CT109 – BAU-SPEZIFIKATION S1–S3 v2 (Änderungen gegenüber v1)

**Status:** ENTWURF, nicht gehasht. **Erstellt:** Fr 23.10.2026 ≈ 10:00 UTC, vor jeder Signalauswertung auf realen Daten. Gemessen wurden bisher nur Gate-Größen (`E|r|`, RMS, `n_eff`, Klasse). **Autor:** Einsatzleiter (Claude), Regime „Entscheiden, nicht fragen“.
**Geltung:** `BAU_SPEC_S1S3_v1.md` (SHA-256 `616fa8a1…37b5`) gilt weiter, **soweit v2 nichts ersetzt**. `GATE_SPEC_v1.md` (`acaed785…d5be7`) geht vor. Nach dem Hash-Eintrag unveränderlich; der Freeze nennt den Hash dieser Datei.
**Prüfauftrag an Andi (3 Punkte, dann Hash noch am selben Tag):** (1) §V2.2 Bestätigungsmenge und Kostenfaktor, (2) §V2.5 die zwei vorregistrierten Hypothesen, (3) §V2.3 Ergebniskategorien (insbesondere „POSITIV-UNTERPOWERT“ geht in den Paper-Betrieb, nie in Echtgeld).

## V2.0 Warum v2 (Messung und Ableitung getrennt)
- **Gemessen (Gate A, L3, Andis PC 23.10.):** Alle zulässigen Zellen sind Klasse W (BTC/ETH/SOL × 24 h/72 h), keine P-Zelle. Hypothesen in Klasse-W-Zellen sind auf **2** gedeckelt (Gate-Spec §6). `n_eff` in A: 269 (24 h), 89 (72 h).
- **Abgeleitet (aus den Gate-Werten, RMS als Näherung für σ_trade, `z₁₋α′ + z₁₋β = 3.3393`):** `N_min` für C1 ≈ BTC 24 h 2642, BTC 72 h 3994, ETH 24 h 5060, ETH 72 h 7799, SOL 24 h 3002, SOL 72 h 5240. Das 270-Tage-Fenster A liefert höchstens 269 bzw. 89 Trades. **C1 ist in A mechanisch unerreichbar.** Discovery auf A kann deshalb nie ein Kandidat nach v1 C1–C7 erzeugen; v1 C7 (Bestätigung in 270-Tage-Fenster B) hat dieselbe Grenze.
- **Folge:** Beweislast liegt auf einer **längeren Vorhistorie** (V2.2) und später auf Vorwärtsdaten. Keine Schwelle wird gesenkt (`δ_min`, `α′`, `β`, Kosten bleiben); es ändern sich nur Daten und Reihenfolge.

## V2.1 Rollen der Stufen
- **Stufe D (Discovery, Fenster A, So 25.10. nach Freeze):** liefert Kennzahlen und die Einzelkriterien als **Beschreibung**. Sie ist **kein Filter**: beide eingefrorenen Hypothesen gehen unabhängig vom A-Ergebnis in Stufe B. (Gründe: nur 2 Hypothesen, A kann C1 nicht bestehen, ein Filter auf A wäre ein zusätzlicher Freiheitsgrad.)
- **Stufe B (Bestätigung auf E, Mo 26.10.):** einmaliger Lauf nach V2.2/V2.3, BH-FDR über die eingefrorene Liste (m = 2).
- **Stufe P (Paper vorwärts, ab Do 29.10.):** läuft für die eingefrorene Liste **unabhängig vom Ergebnis der Stufe B**, mit Status-Vermerk je Hypothese. Paper-Betrieb ist **kein statistischer Beleg** (≈ 7 Trades/Woche je 24-h-Hypothese) und dient Betrieb, Kosten-/Fill-Realität und Frühwarnung. Echtgeld bleibt ausgeschlossen (eigenes Gate, nicht Teil dieser Spec).

## V2.2 Bestätigungsmenge E (ersetzt v1 C7: „Regime B“)
- **E** = gesamte Stunden-Historie des Assets **vor** dem Start von Fenster A (`2025-10-04`): Bars von der ersten Kerze der Datei bis `2025-10-03 23:00 UTC`, ohne die Daten ab Fenster A und ohne die gesperrten Daten nach dem Stichtag `2026-06-30`. Kein Trade darf über `2025-10-04 00:00 UTC` hinausreichen. Kerzen aus E wurden bisher nie für Signale benutzt (die Regimewahl nutzte nur BTC-Tagesschlüsse, `window-q B` nur Q-Zähler, Gate nur A).
- **Epochen:** E1 = Start bis `2020-12-31`, E2 = `2021-01-01` bis `2025-10-03`. Fenster B aus der Regimewahl liegt in E und hat keine Sonderrolle mehr.
- **Kostenmodell (Annahme A14, nicht gemessen):** die Gate-Kosten (`c_gate`) beruhen auf heutigen Gebühren und Spreads. Für E1 gilt **Faktor 2.0** auf alle Kosten, für E2 Faktor 1.0. Das ist konservativ (erschwert das Bestehen) und wird so festgeschrieben; eine Lockerung wäre ein neues v3 vor dem Lauf.
- **Q-Pflicht vor Stufe B:** Fehlend-Quote, größte Lücke, erste/letzte Kerze je Asset und Epoche (nur Zähler, `window-q` für E1/E2). Fehlend-Quote > 5 % in einer Epoche oder > 24 fehlende Stunden in Folge außerhalb dokumentierter Börsenausfälle: Epoche entfällt (E = der Rest), Entscheid und Zähler stehen vor dem Lauf im Protokoll.
- **Warmup:** Vorlauf wie im Backtest (336 Bars), Signale nur auf vorhandenen Kerzen, nichts wird aufgefüllt.

## V2.3 Entscheidungsregeln in Stufe B (ersetzt v1 C7, präzisiert C1–C5)
C1–C5 gelten wie in v1 2.5, aber auf **allen Trades in E** (Kosten nach V2.2), `σ_trade` = RMS der Brutto-Renditen in E. Zusätzlich:
- **C7a Epochenkonsistenz:** Netto-Expectancy in E2 > 0 (Trades der Epoche E2 allein). Berichtet wird zusätzlich je Kalenderjahr (beschreibend, kein Kriterium).
- **C7b Regime A:** Netto-Expectancy in Stufe D (Fenster A) hat dasselbe Vorzeichen (> 0). Beschreibend zu berichten: n, LCB95, Placebo. Kein Signifikanzkriterium (Power).
**Ergebniskategorien je Hypothese (fix ab Hash):**
- `BESTAETIGT`: C1–C5, C7a, C7b alle erfüllt (C2 mit BH-FDR q = 0.05 über m = 2 und LCB95 > 0).
- `POSITIV-UNTERPOWERT`: alles außer C1 erfüllt. Das ist ein **Hinweis, kein Beleg**; Paper-Betrieb ja, Echtgeld nein, Nachprüfung nur mit mehr Daten (Vorwärtsdaten, Runde 2).
- `NULLBEFUND`: sonst. Gilt ausdrücklich auch für „nicht nachweisbar“ (keine Aussage über den Markt).
- Das Ergebnis wird je Hypothese berichtet; „höchstens ein Kandidat“ aus v1 entfällt (m = 2, beide dürfen bestehen).

## V2.4 Power-Prognose (Ableitung, nicht gemessen)
Verfügbare Stunden-Historie vor A (Kalendertage, ohne Lücken): BTC 4381, ETH 3711, SOL 1570; ab `2021-01-01`: 1737 (BTC/ETH), 1570 (SOL). Höchstzahl Trades bei 24 h ≈ Tage; bei 72 h ≈ Tage / 3. Gegenüber `N_min` (V2.0, mit σ aus A; in früheren Jahren war die Volatilität höher, `N_min` also eher größer) heißt das: **nur BTC 24 h hat überhaupt eine Chance auf C1**, und selbst dort ist es knapp. **Erwartung (Ableitung): `POSITIV-UNTERPOWERT` oder `NULLBEFUND` ist wahrscheinlicher als `BESTAETIGT`.** Das ist die bekannte Grenze (v1, Schlussabschnitt), keine Aufweichung.
Folge für die Auswahl: beide Hypothesen liegen in der einzigen Zelle mit Aussicht auf Power (BTC, 24 h); ETH/SOL/72 h bleiben unberührt für Runde 2 (andere Kandidaten, mehr Assets, Vorwärtsdaten).

## V2.5 Vorregistrierte Hypothesen (festgelegt vor jeder Signalauswertung; keine Rastersuche)
Auswahlgrund: Kategorie aus dem Projektauftrag, Mechanismus, BTC/24 h (Power, V2.4), feste konventionelle Parameter, Handelsfrequenz nahe der Obergrenze (ein Trade je 24 h), damit `n` nicht künstlich klein ist.
- **H1 `TS_MOM(L=24, side=both)`, BTC, H = 24:** Zeitreihen-Momentum, Fortsetzung der letzten 24 h über die nächsten 24 h (Informationsdiffusion, Trendfolger-Flow). Kategorie Momentum.
- **H2 `SHOCK_FADE(w=4, k=1.5, N=168)`, BTC, H = 24:** Mean-Reversion nach einer 4-h-Bewegung über 1.5 σ (σ aus den 168 Bars davor): Überschießen durch Liquiditätsnachfrage klingt ab. Kategorie Mean-Reversion. Bewusst **Gegenmechanismus** zu H1.
- Beide Zellen BTC/24 h sind Klasse W (ρ_min⁺ = 0.0977); damit sind beide Klasse-W-Plätze belegt. Eine spätere Änderung der Parameter ist ein neuer Freeze und ein neues v3.
- Aussage zur Datenlage: Für diese Parameter wurde **kein** Signal ausgewertet; keine Statistik über Signale oder Renditen aus E, A oder B liegt vor.

## V2.6 Änderungen S3 (Runner), vor dem Deploy-GO
- (a) **Placebo-Zwilling offline:** ersetzt v1 3.6 „online im Runner“. Der Runner speichert alle Kerzen und Entscheidungen; die Placebo-Auswertung läuft später offline mit derselben Funktion wie im Backtest (feste Seeds, gleiche Trade-Zahl, Richtungen permutiert). Grund: gleicher Code, gleiche Zähler, weniger Zustand im Dauerbetrieb.
- (b) **Fehlende Ausstiegskerze:** der Runner schließt zur nächsten verfügbaren Kerze und markiert `late_exit`; der Backtest verwirft solche Trades. Der Äquivalenztest gilt lückenfrei.
- (c) **Entscheidungsfrist:** eine Kerze gilt nur als Entscheidungsgrundlage, wenn sie bis 300 s nach Stundenbeginn gesehen wurde (sonst Sperre `late`, Eintrag im Log).
- (d) **Statusseite:** statische HTML-Datei, kein Server, kein offener Port, kein Skript; Erzeugung per `paper-status --html`. Jeder Dienst (Timer/Unit) braucht ein eigenes GO.
- (e) **Laufzeit:** Python 3.11.2 und numpy 1.24.2 (Debian), `GO NUMPY` ausgeführt 23.10.

## V2.7 Ablauf und Prüfbarkeit
Sa 24.10.: Andi liest, Hash dieser Datei (LF-normalisiert) wird noch am selben Tag in `01` eingetragen. So 25.10. früh: Freeze (`freeze` mit diesem Spec-Hash, die zwei Hypothesen aus V2.5), danach Stufe D, Q-Pflicht für E. Mo 26.10.: Stufe B. Code: die Bestätigungsstufe `confirm` ist **vor dem Freeze** fertig und geht über den Code-Hash in den Freeze ein (kein Nachbessern nach dem Freeze). Jede Abweichung vom Ablauf = Protokolleintrag, kein stilles Nachziehen.

## V2.8 Neue Annahmen (nicht gemessen)
**A14** Kostenfaktor 2.0 für E1. **A15** Epochengrenze `2021-01-01`. **A16** Schwellen der Q-Pflicht (5 %, 24 h). **A17** `σ_trade` aus A ist eine brauchbare Näherung für die Power-Prognose (V2.0/V2.4).
