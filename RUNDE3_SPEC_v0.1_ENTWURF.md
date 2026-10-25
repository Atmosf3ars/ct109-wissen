# CT109 – RUNDE-3-SPEZIFIKATION v0.1 (ENTWURF, NICHT FESTGESCHRIEBEN)

**Status:** ENTWURF des Einsatzleiters, Stand So 25.10.2026 ≈ 02:30 Berlin. **Nicht gehasht, nicht gültig**, bis der Freeze-Eintrag in `01_STATUS.md` steht (Ziel Do 29.10., spätestens Fr 30.10.). Bis dahin darf sich alles ändern; **danach nichts mehr** (Änderung nur als v2 vor dem ersten Öffnen der Daten).
**Autor:** Einsatzleiter (Claude), Delegation Andi. **Wissensstand-Offenlegung:** Der Autor kennt die allgemeine Literatur (Funding als Kontraindikator, Liquidationskaskaden, Insider-Käufe, PEAD) und hat die Rohdaten **nicht** auf Renditen ausgewertet. Gesehen wurden nur: Zeilen-/Minutenzähler, Preis-Min/Max, Tick-Test (`01` T6), Funding-/SEC-Dateizähler. **Nachereignis-Renditen wurden nie berechnet.** Die E2-Zählung (Ereignisse je Jahr) steht noch aus und kalibriert nur Schwellen nach der Zählregel §6 (nicht nach Renditen).
**Geltung:** ergänzt `GATE_SPEC_v1`/`RUNDE2_SPEC_v1` (unverändert, bereits gehasht). Gilt für **Welle 3a (Krypto-Ereignisse)** und **Welle 3b (Aktien-Ereignisse)**. Entscheidungen: `02` D28–D37.

## 0 Zweck und Haltung
Runde 3 prüft **sechs vorab festgelegte, ereignisbasierte Mechanismen** mit großem Effekt je Ereignis statt Faktorprämien im Tagesquerschnitt (Auflösungswand `03` §8.1: kleine Kanten sind bei unserer Stichprobe nicht nachweisbar). **Gemessen bleibt gemessen, Annahmen bleiben Annahmen.** Jede Aussage trägt eine Evidenzstufe; kein PASS ohne Beleg; „nicht nachweisbar“ ist nicht „kein Edge“.

## 1 Test-Konto (α-Budget) – ersetzt „BH je Runde“
- **Lebensdauer-Konto (D37):** Alle **bestätigenden Haupttests** des Projekts teilen sich **FWER 0,05** über höchstens **N_max = 20** Tests (Bonferroni-gewichtet): Grundbetrag je Test **α_i = 0,05·w_i/20**, Gewichte `w_i ≥ 0,5`, `Σ w_i ≤ 20`, **vor dem Freeze festgelegt**. Standard `w_i = 1` ⇒ **α_i = 0,0025** (einseitig z = 2,807).
- **Bereits verbraucht (Register-Index 1–4):** lf1 H1 TS_MOM(24), lf1 H2 SHOCK_FADE (Krypto), lf2 R-H1 STR, lf2 R-H2 MOM (Aktien). Alle Nullbefund; sie bleiben im Register, **kein Rückfluss von α**. Verfügbar: 16 Tests. Runde 3 nutzt höchstens 6, Runde 4 höchstens 6, Reserve 4.
- **Kein Rückfluss, keine Wiederverwendung eines Fensters für denselben Test.** Ein Haupttest läuft **genau einmal** auf **allen** Daten ≤ 2026-06-30 23:59:59 UTC (Parameter sind vorab fest, nichts wird gefittet ⇒ kein Discovery/Bestätigungs-Split nötig; das spart Power). Mehr Power gegenüber `D→B` ist die bewusste Entscheidung (D37).
- **Wellen:** Welle 3a (K4, K1, K5) und 3b (S4, S5, S6) sind getrennte Freezes mit eigenem Hash; α_i hängt **nicht** von der Rangfolge ab (Bonferroni), daher kein Reihenfolge-Freiheitsgrad.
- **Hashgekettetes Register** `register/TESTREGISTER.jsonl` (append-only, je Zeile `idx, prev_hash, hyp_id, spec_hash, code_hash, data_manifest_hash, fenster, α_i, ergebnis_hash, utc`), auch **Abbrüche und Nullläufe** und jede Ablation (neue Zeile). Erste Zeilen: die vier Altlast-Tests (Quellen `01`). Schreiben nur durch Einsatzleiter im Freeze/Lauf-Schritt (kein Host-Zugriff).
- **HINWEIS-Klasse (D29):** Hypothesen, deren **erwartete** Netto-Kante unter der Auflösung liegt (§9), werden **vor dem Freeze** als `HINWEIS` deklariert: sie dürfen laufen (ohne α-Verbrauch) und werden **deskriptiv** berichtet; sie können **nie** `BESTAETIGT` werden. Nur Hypothesen mit erwarteter Kante ≥ 1,0 × MDE (Power ≥ 0,5 bei α_i) bekommen ein α_i.

## 2 Daten und Fenster
| Quelle | Inhalt | Fenster Haupttest | Forward (gesperrt) |
|---|---|---|---|
| Kraken Time & Sales (SHA gleich Kraken, `01` T3) | XBT/ETH/SOL-USD, 1-Min-Aggregate (`agg_trades_v1`, Tick-Test: `type` = Aggressor) | XBT 2013-10 … 2026-06-30; ETH 2015-08 …; SOL 2021-06 … | 2026-07-01 … 09-30 (im ZIP, unberührt) |
| Binance-Funding (8 h) | BTC/ETH/SOL-USDT-Perp | 2020-01 … 2026-06 (SOL ab 2020-09) | ab 2026-07 |
| Kraken-Funding (stündlich) | PF_XBTUSD/ETH/SOL | 2025-10-15 … 2026-06-30 (**nur Vergleich der Proxy-Annahme**, kein Test) | ab 2026-07 |
| SEC Form 3/4/5 (bulk) | Insider-Transaktionen | 2006 Q1 … 2026 Q2 | ab 2026 Q3 |
| Alpaca SIP (**Lizenz offen**) | Aktien-1-Min und Tages-Bars | 2016 … 2026-06-30 | ab 2026-07-01 |
| Tiingo EOD | Tageskerzen (Lizenz „Internal Use“, Rohdaten nur auf Andis PC) | nur falls Alpaca ausfällt | – |
| EDGAR 8-K | Items + Annahmezeitpunkt (**Quelle offen**) | 2016 … 2026-06-30 | ab 2026-07 |
- **Hartes Zeitfenster:** Jeder Lader bricht bei `ts ≥ 2026-07-01 00:00 UTC` ab (wie `agg_trades_v1`). **Forward F** (Daten ≥ 2026-07-01 bzw. Q3) wird **erst nach** dem Haupttest einmal je Kandidat geöffnet (§11) und dient als **Konsistenz- und Betriebsprüfung** (Zähler meist klein, kein eigener Power-Anspruch).
- **Haupttest-Fenster Krypto = 2019-01-01 … 2026-06-30 (D38).** Festgelegt **nach Blick auf E2-Zähler, nicht auf Renditen.** Begründung: Das Kostenmodell (Rundreise 16 bp, A-C3) gilt nur für die liquide Ära; die Ereignisrate fiel von ≈ 50–80 Episoden/Jahr (BTC 3 %, 2014–2021) auf 21/20/10/4 (2023–2026), die frühen Jahre sind eine andere Marktstruktur. 2013–2018 laufen nur **deskriptiv** (Vor-Ära, kein α).
- **Kryptoquelle:** Signale und Ausführungspreise aus Kraken-Spot-Minuten (`XBTUSD`, `ETHUSD`), gehandelt wird das Perp (`PF_XBTUSD`, `PF_ETHUSD`). **Annahme A-C1:** Perp-Pfad ≈ Spot-Pfad (Basis ≪ Kostenklasse); nicht gemessen, Kraken-Futures-Kursgeschichte steht nicht zur Verfügung. Unterstützung: Binance-Funding als Proxy (A-C2, §2).
- **Datenhygiene (vor Freeze, nur Zähler):** Fehlticks (Tief/Hoch < 0,7 oder Sprung > 40 % zum Vorschluss) werden verworfen und gezählt (E2); ETH 2015 Preis 0,15 (`01` T6) wird dadurch abgefangen.

## 3 Zustandsvariable (Regime ex ante, D31)
- **Krypto:** `Z_t` = Perzentil der 30-Tage-Realized-Vol (`RV30`, Tagesrenditen BTC, √365) gegen die **eigene Vorgeschichte der letzten 3 Jahre** (nur Information ≤ t−1 Tag). **Zustände:** NIEDRIG (Z < 1/3), MITTEL, HOCH (Z > 2/3).
- **Aktien:** dieselbe Konstruktion auf SPY (√252).
- Jede Hypothese **deklariert ihren erwarteten Zustand** (§7) vorab. Der Zustandskontrast ist ein **Interaktionstest über alle Ereignisse** (Gruppenmittelwert HOCH − NIEDRIG, Cluster-Bootstrap), **kein** Kriterium „Netto > 0 im ruhigsten Fenster“.
- **Komplexe Zustandsvariablen** (Hawkes-n̂, Buch-Verlangsamung) müssen die Referenz `RV30-Perzentil` per ΔAUC/ΔR² schlagen, bevor sie als Filter erlaubt sind; in Runde 3 **nur deskriptiv**.

## 4 Kosten und Ausführung (Annahmen, nicht gemessen)
- **Krypto-Perp (Kraken Futures, Tier 1):** Gebühr Taker 5,0 bp / Maker 2,0 bp je Seite (Herstellerangabe `03` §8.2, L1); **Haupttest rechnet Taker beide Seiten** (10 bp) **plus Slippage 3 bp je Seite** (A-C3) ⇒ **Rundreise 16 bp**. Maker-/Warteschlangenvarianten nur als Sensitivität (Fill-Regel „durchgehandelt, nicht berührt“, T&S-Simulation, 30 % Abschlag auf Fills).
- **Funding (Krypto):** realisiertes Funding als Cashflow: Long zahlt `f`, Short erhält `f` (Binance-Funding als Proxy für Kraken, A-C2); pro-rata auf Haltedauer in 8-h-Schritten.
- **Stop:** hartes Stop-Level; Fill im Stop-Minute zum Stop-Preis **minus** 10 bp Extra-Slippage (A-C4). Lücken (Minuten ohne Handel) füllen **nicht** auf; kein Fill in Minuten ohne Trades.
- **Aktien (IBKR Pro, Ticket ≈ 1 000 EUR, `02` D34):** Gebühr Tiered Mindest 0,35 USD/Order ⇒ bei 11 Aktien ≈ 3,2 bp je Seite; Spread+Slippage 4 bp je Seite (A-S1) ⇒ **Rundreise 15 bp** (Large Cap), Mid Cap 25 bp (A-S2); Short-Leihe 1 bp/Tag auf Notional (A-S3). **Abgleich der Mindestgebühr gegen die reale IBKR-Gebührenseite vor dem Freeze.**
- **Stress:** (C4a) alle Kosten × 1,5; (C4b) Einstieg um **eine zusätzliche Minute** (Krypto) bzw. **einen zusätzlichen Handelstag** (Aktien) verzögert; (C4c) Slippage × 2 in HOCH-Zustand.

## 5 Test-Mechanik (für alle Hypothesen)
1. **Inferenzeinheit = unabhängige Episode**, nicht Ereignis (D33): Ereignisse im Abstand < G (je Hypothese, §7) gehören zur selben Episode; Episoden-Rendite = Mittel der Netto-Renditen ihrer Ereignisse (bei mehreren Assets zusätzlich Mittel über Assets). **Haupt-Statistik:** `m = mean(Episoden-Netto-bp)`.
2. **Inferenz:** Moving-Block-Bootstrap über **Kalenderwochen** der Episoden (Episoden werden nach Wochen geklumpt, Blocklänge 4 Wochen, 10 000 Ziehungen, Seed vorab), einseitiger p-Wert `P(m* ≤ 0)`; zusätzlich `LCB`. **C2:** `p ≤ α_i` und `LCB_{1−2α_i} > 0`.
3. **C1 Power:** `MDE = (z_{1−α_i} + z_{0,8})·σ_ep/√n_ep` aus der **Zählung** (E2 + Streuung aus Annahme σ_ep, nicht aus Renditen) ≤ erwartete Kante (Tabelle §9). Sonst `HINWEIS`.
4. **C3 Placebo:** (a) **Zeitversatz-Placebo:** Ereignisuhren um zufällige Vielfache von 1 Woche (± 4 … 52 Wochen) verschieben, Zustands-Bucket (Z) beibehalten, **dieselbe Handelsregel**; echtes `m` > 97,5-%-Quantil der 2000 Placebo-Mittel. (b) **Uhrzeit-/Vola-gematchtes Placebo** (Krypto): Pseudo-Trigger an Tagen ohne Schock (±48 h) im selben `RV24h`-Dezil, dieselbe Ein-/Ausstiegsregel.
5. **C4 Stress:** C4a, C4b, C4c je `m > 0`.
6. **C5 Konzentration:** die 3 größten Episoden tragen ≤ 40 % des Bruttogewinns (nur wenn `m > 0`); kein Kalenderjahr > 50 % des Gesamtnetto.
7. **C6 Konsistenz (Zwei-Regime-Pflicht):** Vorzeichen von `m` in **beiden Zeithälften** (nach Episodenzahl halbiert) **und** in ≥ 2 Zuständen mit je ≥ 20 Episoden positiv; sonst `NICHT_BEWERTBAR im Zustand`.
8. **C7 Kalibrierung der Gesamtregel (VOR dem Freeze, D31):** gesamte Regel (C1–C6) auf **≥ 200 Nullwelten** aus echten Daten ohne Kausalstruktur (Ereignisuhren blockverschoben + Renditen blockweise zyklisch verschoben): **Fehlpass-Rate ≤ 5 %**; Operationscharakteristik `P(bestanden | wahrer Edge δ)` für δ ∈ {0, ½MDE, MDE, 2MDE} wird **in der Spec** mit Zahl festgehalten. Fehlpass > 5 % ⇒ Regel verschärfen **vor** dem Freeze, nicht danach.
9. **Kategorien:** `BESTAETIGT` (C1–C7 erfüllt), `POSITIV-UNTERPOWERT` (C2…C6 erfüllt, C1 nicht – nur wenn Hypothese **nicht** vorab als HINWEIS deklariert), `HINWEIS-…` (vorab deklariert, deskriptiv), `NULLBEFUND` (nur, wenn C1 erfüllt und `m` nicht signifikant; sonst `NICHT NACHWEISBAR`), `INSUFFICIENT` (zu wenig Episoden; „0 Trades“ ist nie Nullbefund).

## 6 Regel für Schwellen (Zählregel, statt Renditesuche)
Ereignisschwellen (θ, φ, k) werden **aus dem Raster {3 %, 4 %, 5 %} bzw. {3, 5, 8 bp}** gewählt als **kleinster Wert, bei dem E2 ≥ N_min unabhängige Episoden im Gesamtfenster zeigt** (`N_min = 120` Krypto-Schock, `N_min = 80` Funding, Wochenende: Raster {1,0; 1,5; 2,0}σ_W mit N_min = 100). Hält keiner N_min, wird die Hypothese `INSUFFICIENT/HINWEIS` (kein α). **Die Wahl nutzt ausschließlich E2-Zähler.** Danach festgeschrieben.

**Ergebnis der Zählregel (E2/E2b, L2, Andi 25.10. 12:00–12:30):**
- **K4 (θ = 3 %, Einstiegsregel §7 simuliert, ab 2019-01-01):** XBT 337 Einstiege/251 Episoden, ETH 509/369; **vereinigt 409 unabhängige Episoden** (24-h-Cluster; je Jahr 85/75/66/51/37/34/49/12); je Zustand NIEDRIG 151, MITTEL 162, HOCH 111 (alle ≥ 20 ✓). Streuung der 4-h-Rendite (zentriert, ohne Stop, nur Betrag): XBT 268 bp, ETH 337 bp; Mittelwert des Betrags 166/215 bp; je Zustand NIEDRIG 161–212, MITTEL 270–397, HOCH 313–357 bp. ⇒ **α-Test zulässig.**
- **K1 absolut:** BTC ≥ 5 bp nur 32 Episoden (2020/21 geklumpt) ⇒ INSUFFICIENT. **K1r relativ** (≥ max(2 bp, P97,5 der letzten 90 Tage)): positiv BTC 30, ETH 33, SOL 28 Episoden (2022/2025/2026 praktisch leer), negativ BTC 31, ETH 41, SOL 51 ⇒ **N_min 80 verfehlt, HINWEIS** (auch beidseitig gepoolt MDE ≈ 185 bp ≫ erwartete 30–70 bp).
- **K5:** 390 Wochenenden; |R_W| ≥ 1,0σ: 77, ≥ 1,5σ: 45, ≥ 2σ: 27 Ereignisse (je ≈ 50 % Auf/Ab) ⇒ **N_min 100 verfehlt, HINWEIS**.
- **Folge:** Welle 3a hat **genau einen α-Test: K4** (plus gekettete Replikation K4P auf unabhängigen Coins, §7). K1r und K5 laufen deskriptiv.
- **Paper:** BTC/ETH-Schocks seit 2023 nur ≈ 35–50 vereinigte Episoden/Jahr ⇒ Vorwärtsbestätigung dauert Jahre.

## 7 Hypothesen Welle 3a (Krypto; Daten vorhanden)
**Gemeinsam:** Assets XBT und ETH (SOL nur deskriptiv wegen kurzer Historie); Long/Short wie unten; ein Ereignis je Asset und 6 h Abkühlung; Position ≤ 600 EUR (`02` D34); keine Pyramiden.

**K4 AFTERSHOCK-LONG (Mean-Reversion nach Kaskade; erwarteter Zustand HOCH und MITTEL).**
- *Mechanismus:* Zwangsliquidationen/Stop-Kaskaden erzeugen einen unelastischen Verkaufsfluss; nach Ausklingen kehrt ein Teil des Abverkaufs zurück (Abschnitt `03` §8.6).
- *Ereignis:* erste Minute `t = τ`, in der `low_t ≤ (1 − θ)·max(high_{t−14…t})` (θ nach §6, Raster {3, 4, 5 %}).
- *Einstieg:* frühestens `τ + 20 min`; erste Minute `t_e`, in der **kein neues Tief** der letzten 10 Minuten unter dem Tief seit τ liegt; spätestens `τ + 120 min`, sonst **kein Trade** (gezählt). Long **Taker** zum Open der Minute `t_e + 1` (A-C3).
- *Ausstieg:* nach **240 min** (Open), oder Stop bei `−5 %` vom Einstieg (Fill Stop −10 bp).
- *Episode:* Abstand `G = 24 h` zwischen Ereignissen.
- *Erwartung (Annahme, Autorenbericht, nicht gemessen):* Retracement 38–50 % des Abverkaufs ⇒ brutto ≈ 0,4·θ ≈ 120–200 bp bei θ 3–5 %, **netto ≈ 100–180 bp**, Streuung je Episode σ_ep ≈ 300–500 bp [A]. **Vorab-Klasse:** abhängig von n_ep aus E2 (Tabelle §9).
- *Deskriptiv (kein α):* Retracement-Anteil, Anzahl Folgeereignisse ≥ 1 % in 60 min (Aftershock-Intensität), Hawkes-n̂-Proxy.

- *Verwandtschaft (Offenlegung):* lf1 **H2 SHOCK_FADE** (Register-Index 2, **Nullbefund**) testete einen verwandten Mechanismus auf BTC (24-h-Raster, andere Auslöseregel). K4 unterscheidet sich durch Minuten-Auslöser, Wartebedingung und 4-h-Horizont, **zählt aber als eigener Test**; der frühere Nullbefund senkt die Prior-Erwartung (Annahme), nicht das α.
- *Power (E2b, L2/A):* Episoden n = 409, σ_ep ≈ 300 bp (Spanne 270–340) ⇒ SE ≈ 13–17 bp, **MDE (80 %, α_i = 0,0025) ≈ 49–61 bp**. Operationscharakteristik (Normalnäherung, σ 300): Power bei wahrem Netto-Edge 0/25/40/55/75/100 bp = 0/13/46/82/99/≈100 %. Zustandsspezifisch (HOCH n = 111): MDE ≈ 116 bp ⇒ **Zustandskontrast nur deskriptiv**. Erwartete Netto-Kante 100–180 bp stammt aus Autorenberichten und gilt als **zu optimistisch** (E|r| nach Einstieg ≈ 166–215 bp); realistische Prior-Spanne 20–60 bp [A] ⇒ Power des Haupttests 10–85 %, ehrliche Aussage: „nur bei Kante ≳ 50 bp nachweisbar“.
- *K4P (eigener α-Test, D40; Parameter im Entwurf):* dieselbe Regel auf **39 Kraken-USD-Paaren** (SOL + 38; ex-ante-Liste: USD-CSV ≥ 150 MB **und** gleichnamiger handelbarer Kraken-Perp; ohne Stablecoins, Fiat, LUNA, MATIC; XDG = DOGE), Auslöser `θ = max(3 %, 6·σ̂₁₅)` (σ̂₁₅ = trailing 30 Tage, ±15-%-Kappung), Rundreise **26 bp** [A-C5], Episode = 24-h-Cluster über alle Paare, Episodenrendite = Mittel je Paar, dann über Paare. **Zählung (bereinigt):** 764 Episoden, 10 386 Einstiege, Zustände 367/292/180, σ je Einstieg ≈ 411 bp. **Power [L2/A]:** σ_ep 300–400 bp ⇒ SE 11–14 bp, **MDE80 ≈ 40–53 bp** (n = 764); HOCH (n = 180) ≈ 82–109 bp. K4 und K4P sind getrennte Tests mit je α_i = 0,0025 (D40). Abhängigkeit zu K4 offengelegt (218/764 Episoden ±24 h).

**K1 FUND_CROWD (Funding-Extrem → Perp-Short; erwarteter Zustand MITTEL und HOCH). STATUS: INSUFFICIENT bzw. HINWEIS (E2/E2b), läuft nur deskriptiv, kein α.**
- *Mechanismus:* extreme positive Funding-Raten zeigen überfüllte Long-Positionen; Abbau und negative Konvexität; zusätzlich vereinnahmt der Short das Funding.
- *Ereignis:* Binance-Funding-Zeitstempel `s` mit `f_s ≥ φ` (φ nach §6, Raster {3, 5, 8 bp je 8 h}) für BTC bzw. ETH; Ereignisuhr = Funding-Zeit.
- *Einstieg:* Short zum Open der Minute nach `s` (Taker); *Ausstieg:* nach **72 h** (Open) oder Stop `+8 %`.
- *Funding-Cashflow:* Short **erhält** `Σ f` der 9 folgenden Settlements (Binance-Proxy, A-C2).
- *Episode:* Abstand `G = 72 h`.
- *Erwartung (Annahme):* Preiskomponente 0–40 bp [A]; **Funding-Komponente allein bei φ = 5 bp: ≈ 9 × 5 bp = 45 bp** (rechnerisch, aber nur bei erhaltener Rate); Rundreise 16 bp; **netto ≈ 30–70 bp** [A]. σ_ep (72 h) ≈ 400 bp [A] ⇒ **wahrscheinlich HINWEIS-Klasse** (Tabelle §9), außer E2 zeigt ≥ 200 Episoden.
- *Deskriptiv:* Zerlegung Preis vs. Funding; Vergleich mit Kraken-Funding im 12-Monats-Fenster (Proxy-Güte).

**K5 WEEKEND-UMKEHR (Mean-Reversion; erwarteter Zustand NIEDRIG und MITTEL). STATUS: HINWEIS (45–77 Ereignisse < N_min), kein α.**
- *Ereignis:* `R_W` = ln-Rendite XBT von **Fr 21:00 UTC bis So 21:00 UTC**; `σ_W` = Std der letzten 52 `R_W` (ex ante); Ereignis, wenn `|R_W| ≥ k·σ_W` (k nach §6, Raster {1,0; 1,5; 2,0}).
- *Einstieg:* So 21:00 UTC (Open 21:01), **gegen** die Wochenendrichtung (Taker); *Ausstieg:* nach **24 h**, Stop `−4 %`.
- *Placebo:* **Zufallsfenster** – dieselbe Regel für Mo–Do-Fenster gleicher Länge und Folgehaltedauer (C3b).
- *Episode:* je Woche eine Episode (G = 7 Tage).
- *Erwartung (Annahme):* Effekt klein oder 0 (Wochenendliquidität ist dünn, aber systematischer Effekt nicht belegt); **Vorab-Klasse HINWEIS** (Power ≈ 100 Ereignisse; MDE > erwartete Kante).

## 8 Hypothesen Welle 3b (Aktien; Gerüst, Daten- und Quellenklärung offen)
**Gemeinsam:** Alpaca-SIP-Tagesbars bzw. -Minutenbars (Lizenz-Check offen), Ticket ≈ 1 000 EUR, höchstens 1–2 gleichzeitig (D34). Universum: Aktien mit Median-Dollarvolumen der letzten 60 Tage ≥ 20 Mio. USD und Kurs ≥ 5 USD (ex ante je Tag).

**S4 INSIDER-CLUSTER (Long).** Ereignis: am Tag `d` liegt für einen Emittenten die **dritte** unterschiedliche Insider-Person mit Open-Market-Kauf (Code `P`, `D`=0, Form 4, Beziehung Offizier oder Direktor) innerhalb der letzten **14 Kalendertage** vor; Gesamtvolumen ≥ 100 000 USD; **Einreichungsdatum** (`FILING_DATE`) zählt, nicht Transaktionsdatum. Einstieg: Open des **nächsten Handelstags** nach `d`; Ausstieg: nach **21 Handelstagen**. Return gegen SPY-Hedge-Faktor 1 (**marktbereinigt**, Hedge nur als Rechengröße). Episode: Abstand 21 Tage je Emittent; Cluster nach Kalendermonat im Bootstrap. **Vorab-Klasse:** nach E2-analog Zählung (Datei E3) und Effektgrößen-Bericht (`research/effektgroessen_insider_8k.md`).

**S5 8-K-NACHRICHT / KEINE NACHRICHT (Mean-Reversion bzw. Drift).** Ereignis (Entwurf): Tagesrendite (Close-zu-Close, marktbereinigt) `|r| ≥ 4·σ_60` **ohne** 8-K am Tag und Vortag ⇒ **Umkehr** (Gegenposition, Haltedauer 5 Tage); mit 8-K Item 2.02/5.02/1.01 gleicher Größe ⇒ **kein Trade** (Kontrollgruppe). **Offen:** 8-K-Item- und Zeitquelle (`research/alpaca_edgar_quellen.md`), Zeitstempelregel (nach Handelsschluss = nächster Tag).

**Stand 25.10. ≈ 12:30 (Effektgrößen-Bericht `forschung_nacht_2026-10-25/effektgroessen_insider_8k.md`, L1/L2 Zusammenfassungen, Brutto-Zahlen) und E3-Zählung (Insider-Cluster ≥ 3 Personen: 13 116 seit 2006, ≈ 600/Jahr, ohne Liquiditätsfilter):** erwartete Netto-Kante für Large Caps: Insider 0–30 bp [A], 8-K-Standarditems < 40 bp, Sympathie ≈ 0 – alle **unter** der Nachweisgrenze (MDE ≈ 66–90 bp bei n ≈ 150–1 500). **Vorab-Einstufung (D38):** **S4 HINWEIS** (läuft ohne α, deskriptiv; wird α-Test nur, wenn E3 nach Liquiditätsfilter und die σ-Messung eine MDE unter der erwarteten Netto-Kante ergeben, z. B. breiteres Universum), **S5 HINWEIS**, **S6 ENTFÄLLT** (kein Beleg, Curme et al.: Lag-Korrelation 0,01–0,02 und Erosion).

**S6 SYMPATHY-REVERSION (Mean-Reversion Intraday).** Ereignis (Entwurf): idiosynkratischer Sprung eines Sektor-Leaders `≥ 4σ` (σ aus 1-Min-Renditen der letzten 20 Tage, ex ante) in ≤ 15 min bei **ruhigem** Sektor-ETF (|Rendite ETF| < 0,5σ); Einstieg Mitläufer **entgegengesetzt zum Sprung** nach 15 min (Taker); Ausstieg nach 3 h oder Tagesende. Leader-Follower-Zuordnung **vorab fest** nach Sektor-ETF-Mitgliedschaft (Paarwahl-Freiheitsgrad entfällt), **gepoolt**, Cluster nach Tag. **Datenabhängig:** Alpaca-SIP-1-Min (Lizenz, 2016-Artefakt, Survivorship), Rate-Limit-Rechnung (≈ 190 Seiten je Symbol und 10 Jahre).

## 9 Power-Zeilen (Pflicht je Kandidat; Zahlen erst nach E2)
`MDE = 3,649·σ_ep/√n_ep` bei α_i = 0,0025 und Power 0,8 (z = 2,807 + 0,842).

| σ_ep (bp) | n_ep=40 | 80 | 120 | 200 | 400 |
|---|---|---|---|---|---|
| 150 | 87 | 61 | 50 | 39 | 27 |
| 300 | 173 | 122 | 100 | 77 | 55 |
| 500 | 288 | 204 | 167 | 129 | 91 |
Erwartete Netto-Kante (A) je Kandidat: K4 100–180 bp; K1 30–70 bp; K5 ≈ 0–30 bp; S4/S5/S6: laut Bericht (offen). **Regel:** Kante ≥ MDE ⇒ α_i-Test; Kante zwischen ½MDE und MDE ⇒ `POSITIV-UNTERPOWERT möglich`, **HINWEIS** vorab deklarieren; Kante < ½MDE ⇒ nicht aufgenommen.

## 10 Paper und Echtgeld
Säulen A–D (`03` §8.9, `02` D32) werden **vor Paper-Start des jeweiligen Signals** gehasht (nicht nach der Bilanz 02.11.). Echtgeld nur nach `BESTAETIGT` **und** bewährtem vollautomatischem Paper mit zwei Schlüsseln (D27), innerhalb Verlustdeckel D34 (Position ≤ 100 EUR Worst Case; Krypto-Notional ≤ 600 EUR; Aktien-Ticket ≤ 1 500 EUR mit hartem Stop). Der Stop in den Hypothesen oben ist **Teil der Hypothese** (Krypto −5 %/+8 %/−4 %) und deckt D34 (Notional 600 EUR × 5 % = 30 EUR).

## 11 Prozess (Reihenfolge verbindlich, je Welle)
1. Zählungen (E2/E3) → Schwellen (§6) → Power-Zeilen (§9) → HINWEIS-Deklaration.
2. Kalibrierung C7 (≥ 200 Nullwelten), Operationscharakteristik in die Spec.
3. **Freeze:** Spec-Hash, Code-Hash, Daten-Manifest-Hash (Dateihashes der benutzten Rohdaten), Seeds, α_i, Gewichte; Eintrag in `01` und Register; unabhängige Nachrechnung des Hashs durch den Einsatzleiter.
4. Lauf (einmalig, Andis PC, Ausgabe nur Aggregate), Registerzeile.
5. Forward F (einmal je Kandidat), Paper-Entscheidung nach Säulen.
6. **Verboten bis zum Freeze:** jede Statistik mit Vorzeichen auf den Zielgrößen (Nachereignis-Renditen, Backtest, Trefferquote, Faktorprämien).

## 12 Annahmen und offene Punkte
**A-C1** Perp-Pfad ≈ Spot-Pfad. **A-C2** Binance-Funding ≈ Kraken-Funding (Kontrolle: 12-Monats-Fenster). **A-C3** Slippage 3 bp je Seite (Krypto, Taker). **A-C4** Stop-Slippage 10 bp. **A-S1/S2/S3** Aktienkosten 15/25 bp RT, Leihe 1 bp/Tag. **A-E1** erwartete Netto-Kanten laut Autorenberichten (Literatur nicht verifiziert). **Offen:** E2/E3-Zählungen; Alpaca-Nutzungsbedingungen; 8-K-Quelle; Kraken-Futures-Zugangsumfang für Andis Konto (Hebel, ESMA, Short erlaubt?); Gebührenseite IBKR; Register-Dateiformat und Code (nur nach Freigabe der Spec, D36: wenige präzise Code-Agenten); Nullwelt-Kalibrierung (Code); Sleeve-Verbund-Entwurf (D29(3)) bis Fr 30.10.
