# CT109 – RUNDE-2-SPEZIFIKATION v1 (US-Aktien, Tages-Querschnitt, Track S)

**Status:** FESTGESCHRIEBEN Sa 24.10.2026 (Hash im Änderungslog von `01_STATUS.md`). **Erstellt:** Sa 24.10.2026, ≈ 11:50 UTC, **vor jedem Zugriff auf Aktienpreise** (weder Tiingo noch andere Quelle wurden abgerufen). **Autor:** Einsatzleiter (Claude), Regime „Entscheiden, nicht fragen“ (Andi am 24.10. 12:36 Berlin: „dann los“; Delegation, kein Owner-GO).
**Geltung:** `GATE_SPEC_v1.md` (`acaed785…d5be7`) und `BAU_SPEC_S1S3_v2.md` (`34d6add4…e068`) gelten für Krypto unverändert. Diese Spec gilt **nur für Track S** und ersetzt dort ausdrücklich das, was sie nennt; alles andere folgt sinngemäß den dortigen Regeln (Doktrin, BH-FDR, zwei Regime, Maßstab Netto-Expectancy nach Kosten, Freeze vor Signalauswertung, einmalige Läufe, Hashketten). Nach dem Hash-Eintrag unveränderlich; Änderung nur als `v2` **vor** dem ersten Preisabruf.
**Offenlegung zum Wissensstand:** Der Autor kennt die allgemeine Faktorliteratur (Kurzfrist-Umkehr, Momentum) und weiß, dass beide Effekte nach der Veröffentlichung in Großwerten schwächer wurden. Es wurden **keine** Aktienpreise, Renditen oder Statistiken dieses Universums gesehen. Fenster und Parameter unten sind deshalb **vor** dem Datenblick festgelegt und nicht anpassbar.

## R0 Warum diese Spur (Messung und Ableitung getrennt)
- **Gemessen (Krypto, L3):** H1/H2 auf BTC 24 h: beide `NULLBEFUND` (`01`, 23.10.). Gate A: alle zulässigen Krypto-Zellen Klasse W.
- **Abgeleitet (Rechnung, Annahmen):** Gleichgerichtete Signale über viele korrelierte Coins erhöhen die effektive Fallzahl kaum (`N_eff = K/(1+(K−1)ρ)`); ein marktneutraler Krypto-Querschnitt trägt zwei Kostenbeine bei geringem Spielraum (`03` §7). US-Aktien haben laut Gate-Spec §5 (L1) niedrigere Kosten (c0 2,3–3,9 bp) und viele schwach korrelierte Titel. **Das ist eine Erwartung, kein Befund.**

## R1 Daten und Universum
- **Quelle:** Tiingo End-of-Day, kostenloser Starter-Plan (Herstellerangaben, L1: 50 Anfragen/Stunde, 1000/Tag, 500 verschiedene Symbole/Monat; Lizenz „Internal Use Only“, nur eigene Nutzung, **Daten nicht weitergeben**). Folge: **Rohdaten bleiben ausschließlich auf Andis PC** (nicht in GitHub, nicht im Projekt, nicht in der Cloud-Sitzung); an den Chat gehen nur Aggregate (Zähler, Hashes, Kennzahlen). Der API-Token bleibt auf dem PC (Umgebungsvariable), nie im Chat.
- **Universum (ex ante, regelbasiert):** die zum Abrufzeitpunkt aktuellen Mitglieder des S&P 500 (Liste aus dem Wikipedia-Artikel „List of S&P 500 companies“; die abgerufene Datei wird gehasht und der Hash in `01` eingetragen, **bevor** der erste Preis abgerufen wird), höchstens **495** Aktien (Symbole alphabetisch bis zur Grenze, falls die Liste länger ist) plus Referenz **SPY**; zusammen unter dem Monatslimit 500. Kein Austausch von Symbolen nach dem Datenblick; nicht abrufbare Symbole werden gezählt und bleiben draußen.
- **Zeitraum:** 2005-01-03 bis 2026-06-30 (Daten danach bleiben für Vorwärtsprüfung unberührt).
- **Preise:** `adjOpen` (Entry/Exit), `adjClose` (Signal), `close` und `volume` (Liquidität); Rendite zwischen Handelstagen ohne Lücke; fehlender Tag = Aktie an dem Tag nicht handelbar (nichts wird aufgefüllt).
- **Handelbarkeit (je Tag t, nur Information ≤ t):** Median von `close·volume` der letzten 60 Handelstage ≥ 20 Mio. USD, `close` ≥ 5 USD, mindestens 260 Handelstage Historie. Quintile werden **nur über handelbare Aktien** gebildet; weniger als 100 handelbare Aktien an einem Tag → kein Signal an dem Tag.
- **Bekannte Verzerrungen (offengelegt):** (1) **Survivorship:** nur heutige Mitglieder, Pleiten/Delistings fehlen. (2) **Index-Aufnahme-Look-ahead:** heutige Mitglieder wurden nach früherem Erfolg aufgenommen. Beides begünstigt tendenziell **positive** Ergebnisse (siehe R7).

## R2 Zellen, Horizonte, Gate S
- Horizonte in Handelstagen: **H = 5** und **H = 21**. Rendite `r = 1e4·ln(adjOpen_{t+1+H} / adjOpen_{t+1})` in bp.
- **Gate S (nur Beträge, nie Vorzeichen):** `ρ_min⁺(H) = c_gate / LCB95(E|r_H|)` über alle handelbaren Aktie-Tag-Fenster im **Fenster A** (R3). `LCB95` = 5-%-Quantil aus Moving-Block-Bootstrap über Handelstage (Blocklänge 20 Tage, 2000 Ziehungen, Seed 20261024). `c_gate = 1.25 · 7 bp = 8.75 bp` (Rundreise je Aktie, Median-Kostenklasse R5; Annahme). Klassen und Schwellen wie Gate-Spec §6 (P ≤ 0,05; W ≤ 0,10; sonst X). Ein Horizont in Klasse X ist gesperrt; Klasse-W-Zellen tragen höchstens 2 Hypothesen (Gate-Spec §6), Klasse P bis zur Listenobergrenze 2 (R4: bewusst klein).

## R3 Fenster und Regime (ex ante, nach Kalender)
- **A (Discovery, Gate, Stufe D): 2012-01-03 bis 2019-12-31** (ruhiges Regime; Begründung allgemeine Marktkenntnis, nicht Daten).
- **E (Bestätigung 1): 2005-01-03 bis 2011-12-30** (enthält die Finanzkrise: hohe Volatilität). **F (Bestätigung 2): 2020-01-02 bis 2026-06-30** (enthält 2020 und 2022: hohe/wechselnde Volatilität).
- **Regime-Nachweis (beschreibend, kein Kriterium):** Median von `RV30` (Formel Gate-Spec §3) der SPY-Tagesschlüsse je Fenster wird berichtet; weicht E oder F nicht erkennbar von A ab (Median E/F < 1,15 × Median A), wird das als Einschränkung der Regime-Aussage vermerkt.
- Warm-up: Signale dürfen Preise **vor** Fensterbeginn nutzen (nur Information ≤ t, frühestens ab 2005-01-03); Signale gibt es erst ab dem 253. Handelstag nach 2005-01-03 (Fenster E beginnt dadurch faktisch Anfang 2006). Positionen und Renditen zählen nur **innerhalb** des Fensters; kein Trade über eine Fenstergrenze (Kohorten, die die Grenze überschreiten würden, werden verworfen).

## R4 Hypothesen (festgelegt vor jedem Preisabruf; keine Rastersuche; höchstens 2)
Gemeinsame Mechanik: Signal an Handelstag t mit `adjClose`; Entry zum `adjOpen` t+1; Halten H Tage; **täglich eine neue Kohorte** (1/H des Buchs); je Kohorte Long = Quintil mit dem besten Score, Short = schlechtestes Quintil, gleichgewichtet, dollar-neutral. Tagesrendite des Portfolios `r_d` = Mittel der aktiven Kohorten von `0,5·(R_long − R_short)` in bp je 1 USD Bruttokapital, abzüglich Kosten (R5).
- **R-H1 `STR(L=5, H=5)` – Kategorie Mean-Reversion:** Score = −ln(adjClose_t / adjClose_{t−5}) (Verlierer der letzten 5 Tage long). Mechanismus: Liquiditätsnachfrage und Überreaktion klingen in Tagen ab.
- **R-H2 `MOM(L=231, skip=21, H=21)` – Kategorie Momentum:** Score = ln(adjClose_{t−21} / adjClose_{t−252}) (12-Monats-Rendite ohne den letzten Monat). Mechanismus: Unterreaktion, Informationsdiffusion. Bewusst **Gegenmechanismus** zu R-H1 (andere Richtung, anderer Horizont).
- Keine Order-Flow-Hypothese in dieser Runde (kein Tick-/L2-Datenbestand für Aktien). Eine Änderung von Parametern oder Liste = neuer Freeze und neue Spec-Version.

## R5 Kostenmodell und Ausführung (Annahme A-R1, nicht gemessen)
- Rundreise je Aktie (Gebühr + halber Spread + Slippage), nach Rang im 60-Tage-Median-Dollarvolumen des Tages im Universum: Rang ≤ 100: **4 bp**; Rang 101–300: **7 bp**; Rang > 300: **12 bp**; mit Faktor **1,25** multipliziert. Kosten fallen je Eintritt/Austritt einer Kohortenposition an.
- **Leihekosten:** 1,0 bp je Tag auf den Short-Notional (≈ 2,5 % p. a.; schwer leihbare Titel werden nicht modelliert, Annahme A-R2). Keine Marktwirkung (kleiner Notional, Annahme A-R3). Dividenden stecken in `adjClose/adjOpen`; Short-Dividenden werden nicht gesondert belastet.
- **Stress:** Kosten × 1,5 (C4a) und Verzug: Entry erst `adjOpen` t+2 (C4b).

## R6 Inferenz und Entscheidungsregeln (ersetzen BAU_SPEC v1 §2.5 / v2 V2.3 für Track S)
**Inferenzeinheit = Handelstag** (Zeitreihe `r_d` nach Kosten, nicht „Trades“). Moving-Block-Bootstrap über Tage, Blocklänge 20 (deckt die Überlappung der Kohorten), 5000 Ziehungen, Seed 20261024; einseitiger p-Wert für „Mittel > 0“.
- **C1 Power:** `MDE = 3,3393 · SE_boot ≤ δ_min`, mit `δ_min = 2,0 bp/Tag` Netto (≈ 5 % p. a.; Annahme A-R4: kleinster wirtschaftlich relevanter Netto-Edge). `SE_boot` = Bootstrap-Standardfehler des Mittels in der jeweiligen Menge (A bzw. E∪F).
- **C2 Signifikanz:** Netto-Mittel > 0, `LCB95 > 0` und p unter BH-FDR `q = 0,05` über **m = 2** (Bonferroni-Gegenprobe α = 0,05/2 wird mitgeführt).
- **C3 Placebo:** 1000 Ziehungen, je Tag die Aktien-Scores **innerhalb des Tages zufällig permutiert** (gleiche Kohortenstruktur, gleiche Kosten); Netto-Mittel der Strategie > 95-%-Quantil der Placebo-Mittel.
- **C4 Stress:** C4a und C4b (R5) beide mit Netto-Mittel > 0.
- **C5 Konzentration:** (i) die 10 Aktien mit dem größten Beitrag tragen ≤ 25 % des Bruttogewinns; (ii) kein Kalenderjahr trägt > 40 % des Gesamtnetto (nur geprüft, wenn Gesamtnetto > 0).
- **C7a Epochenkonsistenz:** Netto-Mittel in **E** und in **F** je > 0 (beide). **C7b Regime A:** Netto-Mittel in Stufe D (A) > 0.
- **Stufe D (A):** beschreibend, **kein Filter**; beide Hypothesen gehen unabhängig davon in Stufe B (E ∪ F). C1–C5 in Stufe B gelten auf E ∪ F zusammen; C7a getrennt.
- **Kategorien je Hypothese:** `BESTAETIGT` (C1–C5, C7a, C7b), `POSITIV-UNTERPOWERT` (alles außer C1), `NULLBEFUND` (sonst) – **mit der Einschränkung R7**.

## R7 Survivorship-Regel (ersetzt `BESTAETIGT` für dieses Universum)
Wegen R1 (1)/(2) gilt: Erfüllt eine Hypothese die Bedingungen von `BESTAETIGT` oder `POSITIV-UNTERPOWERT`, wird sie **ausschließlich** als **`HINWEIS-POSITIV (survivorship-behaftet)`** geführt; weder Paper-Betrieb mit Echtgeld noch Bestätigung ist daraus abgeleitet. Folge: Wiederholung auf **survivorship-freien** Daten (Kaufentscheidung nur durch Andi, Abo-/Kosten-GO), erst dann ist `BESTAETIGT` möglich. **Ein `NULLBEFUND` bleibt gültig** (die Verzerrungen begünstigen Positives; ein Negativ trotz Verzerrung ist robust gegenüber diesem Mangel).

## R8 Prozess (Reihenfolge verbindlich)
1. Spec-Hash in `01` eintragen. 2. Universumsliste abrufen, **Dateihash** in `01`. 3. Preise abrufen (Andis PC, Skript-Hash vorab, Dateihashes je Symbol im Manifest). 4. **Q-Zähler** (nur Zähler: Symbole abrufbar/nicht, Delisting-Anzahl, Tage je Symbol, Lücken, Anzahl handelbarer Aktien je Tag). 5. **Gate S** (R2), einmalig, Aggregat. 6. **Freeze** (Hypothesenliste R4, Spec-Hash, Code-Hash des Pakets `lf2`, Daten-Manifest, Seeds). Unabhängige Nachrechnung des Freeze-Hashs durch den Einsatzleiter. 7. **Stufe D**, 8. **Stufe B**, jeweils einmalig. Alles auf Andis PC (Python 3.14/numpy), Ausgabe nur Aggregate. Code liegt in einem **neuen Paket `lf2`** (kein Eingriff in `lf1`, dessen Hash im Krypto-Freeze und im laufenden Runner steckt); `lf2` bekommt Tests (inkl. Mutationen), unabhängige Prüfung und Windows-Test **vor** dem Freeze.
- **Verboten bis zum Freeze:** jede Statistik mit Vorzeichen (Renditen, Faktorprämien, Korrelationen der Richtung, Trefferquote, Backtest).

## R9 Annahmen (nicht gemessen)
**A-R1** Kostenklassen 4/7/12 bp und Faktor 1,25. **A-R2** Leihe 1,0 bp/Tag. **A-R3** keine Marktwirkung. **A-R4** `δ_min` 2,0 bp/Tag. **A-R5** Fensterwahl A/E/F nach Marktkenntnis. **A-R6** Tiingo-Daten sind für Preisreihen brauchbar (Adjustierung, Lücken): Q-Zähler prüft nur Zähler, nicht Richtigkeit. **A-R7** Handelbarkeitsfilter 20 Mio. USD, 5 USD. **A-R8** Blocklänge 20 Tage deckt die Abhängigkeit.

## R10 Vorab-Erwartung (subjektiv, nicht bindend)
`BESTAETIGT` ist wegen R7 ausgeschlossen. P(mindestens ein `HINWEIS-POSITIV`) ≈ 0,25; wahrscheinlichster Ausgang `NULLBEFUND` für beide, insbesondere für `MOM` in E (Finanzkrise: Momentum-Einbruch 2009) und für `STR` in F (abgeschwächter Effekt nach 2000). Gate S: P(Klasse P für H = 5 und H = 21) ≈ 0,9.
