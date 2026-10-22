# CT109 – 03 FORSCHUNG

**Stand:** 22.10.2026. Maßstab bleibt: Netto-Expectancy je Trade in bp nach allen Kosten (und gegen die faire Rate 1/(1+R) je Trade, nie Bucket-Mittel von R, nie Trefferquote gegen 50 %).
**Kernaussage vorweg:** Bisher ist **kein positiver Edge nachgewiesen** (`PROVEN_EDGE=NO`). Nachgewiesen ist, *warum* die bisherigen Ansätze scheitern: Signalgrößen von ~1 bp stehen Kosten von 10–160 bp gegenüber.

## 1. Ergebnisbilanz (alles Stufe L1/L2, soweit nicht anders vermerkt)
| Linie | Ergebnis | Lehre |
|---|---|---|
| Altes Konfluenz-System (CT107, 15m-Scalp) | Expectancy negativ, Bootstrap-CI schließt 0 aus; MFE/MAE: Entry strukturell spät, Stop zu eng; 1h-Trigger reskaliert negativ, unskaliert grenzwertig ohne Bestätigung | Framework-Problem, nicht Parameter. Beendet. |
| C2 (Kraken Spot, Signal) | als Handelssignal **tot**: Signalgröße 1,06 / 1,12 bp gegen 80–160 bp Roundtrip | Spot-Roundtrip 160 bp ist für Mikro-Signale prohibitiv. **Protokollabweichung 17.10.:** 52 nicht registrierte simulierte C2-Trades, Tag kontaminiert. |
| N4 | Struktur (Periodizität) ja, Richtung nein | kein Handelssignal |
| N6 | 1 Ereignis | zu dünn |
| N1 / C1 | nichts | – |
| H-ML-A | Phase 2 gebaut, Ergebnis nicht dokumentiert | Lücke (`01` §5) |
| Lernbot-Placebo (5j-Teilauswertung, Release-Register V166 §87) | 471 geschlossene Placebo-Trades: **Spot 228** (brutto −0,49 bp, netto −160,50 bp), **Futures 243** (brutto −1,30 bp, **netto −11,30 bp**); gesamt netto −19 670,39 USD, Gebühren ≈ 19 455,74 USD. 8 Konto-/Markt-Zellen mit je 47–76 Trades. `PROVEN_EDGE=NO` | Brutto ≈ 0, die Kosten erklären den gesamten Verlust: Zufall verliert genau die Kosten – Placebo bestätigt das Kostenmodell (und liefert keinerlei Aussage über Signale). Canary 5j/24h INCOMPLETE (~16 h 44 min). |
| SOL-O1 | 0 registrierte Hypothesen | `§4` |

## 2. Kostenhürden (Stufe L1, PROJEKTSTAND §10 und SOL-Entwurf)
| Instrument | Roundtrip-Gebühr | Anmerkung |
|---|---|---|
| Kraken Spot Taker | 160 bp (0,80 %/Seite) | Maker-Fills nicht validiert |
| Kraken Futures Taker | 10 bp (0,05 %/Seite, Tier-1) | Gültigkeit für `PF_SOLUSD`/Konto **nicht nachgewiesen** |
| IBKR US-Aktien | ca. 2,3–3,9 bp bei 5 000 USD | IBKR-Marktdaten 44,50 USD/Monat; Tiefe = Teilbuch, kein NYSE |
| Spread + Buchdurchlauf SOL-Futures | Median-Obergrenze ≈ 16 bp inkl. Gebühren | **Rechnung aus Scouting-Hürden, keine Messwerte** |
Funding: nur geloggt, nicht als Kostenposition belegt. Latenz L: Wert unbekannt.

## 3. Methodenrahmen (verbindlich, Quelle: PREREGISTRATION + SOL-Entwurf §7–§10)
- ≤ 8 Hypothesen je Runde, je eine feste Parametermenge, Richtung vorab; BH-FDR bei Bestätigung (q OPEN, Vorschlag 0,05) plus Bonferroni-Gegenprobe.
- Hypothesenliste und Skript-Hash **vor** jeder Datenöffnung fixiert; Bestätigung nur mit neuer Vorregistrierung, unberührten Daten und anderem Regime; einmaliger Lauf.
- Mindestens zwei Marktregime, ex ante operativ definiert (z. B. realisierte Volatilität mit absoluter Schwelle; keine Quantile aus Discovery-Daten).
- Latenz-Zerfallstest Pflicht (PREREGISTRATION §1): d ∈ {0, 250 ms, 1 s, 5 s, L}; zusätzlich Latenzstress 2×L und Slippage +50 %.
- Zehn harte Ablehnungskriterien (SOL-Entwurf §8): Underpowered = Nullbefund, untere 95 %-Grenze ≤ 0, Stresstests, Permutationskontrolle, Konzentration, Datenqualität, Mindesthäufigkeit, Lookahead-Audit, Prozessverstoß.
- Mindeststichprobe ohne Datenbezug (α′ = 0,05/8, β = 0,2): σ = 40 bp, δ_min = 5 bp → ≈ 714 Trades; σ = 20 bp, δ = 2 bp → ≈ 1 116 (SOL-Entwurf §7).

## 4. SOL-O1 – Stand
**Kategorien (PREREGISTRATION-Nachtrag auf GitHub-main, Stufe L5/C; lokal auf Prod noch alter Stand):** S1 = Negativkontrolle/Eichung (keine Handelshypothese), S2 Spot→Perp Lead-Lag, S3 signierter Aggressor-Flow, S4 seltener Spread-/Tiefenschock mit Reversion. Authentizität: Delegation im Chat, laut Nachtrag **nicht authentifiziert**.
**Registrierte Hypothesen: 0.** `SOL_FREEZE=NOT_DONE`.

| Blocker | Stand 22.10. |
|---|---|
| B1 Kategorienquelle | teilweise: Nachtrag auf GitHub-main vorhanden, Prod-Checkout hinkt 3 Doku-Commits nach, Authentizität UNVERIFIED |
| B2 SOL-Futures-Replay/Fill-Werkzeug | BLOCKED (Validator nur BTC/ETH-L2; `lernbot.replay` Spot-only; `perp_fill.py` uncommitted) |
| B3 `analysis-run` nicht isoliert | BLOCKED (`signalsvc` ohne ReadOnlyPaths/ProtectSystem; DuckDB-Temp unter DATA_DIR; PYTHONPATH auf älteren `/opt`-Code) |
| B4 Freeze-Beweiskette | BLOCKED (Owner-Signatur E-KANAL B nicht live; Registry-Zeilen ohne Authentizität, `01` §3.5; Incident 114 offen) |
| B5 Datenfenster/Rollen | **teilweise belegt (L1):** laut E-129/E-130 (Chat 11.10.) Register 105–111; je Venue (`kraken_x`, `kraken_futures_x`) 11.10. disc (Starttag unvollständig), 12.–25.10. disc, ab 26.10. sealed. Registry **nicht gelesen** → UNKNOWN bis Lesebeleg. Bekannte Lücke 19.10. ≈ 09:10–09:43 UTC (Hostausfall). |
| B6 Regimedefinition | OPEN |
| B7 Kosten (SOL-Tier, Latenz L, Funding) | OPEN |

Vorwissen/Kontamination: SOL-Spread- und Buchdurchlauf-Statistiken wurden im Coin-Scouting E-132 (12./13.10.) gesehen; Return-Analysen von SOL sind nicht belegt (zu bestätigen, O10). Datenvolumen: Futures ≈ 193 MiB Parquet/Tag, SOL gesamt ≈ 0,47 GB/Tag (Schätzung).
Im Entwurf (Repo `docs/…SOL_PREREG_DRAFT…`) stehen zudem O1–O12 offene Entscheidungen und R1–R9 Reader-Anforderungen – nicht hier dupliziert.

## 5. Forschungsrichtung – Entscheidung des Einsatzleiters
**Befund:** Die bezahlte, teure Aufzeichnung (L2, hohe Frequenz) bedient Hypothesen, deren Signal 1–2 bp groß ist. Die Kosten liegen bei 10–16 bp (Futures) bzw. 160 bp (Spot). Zusätzlich liefern 2–4 Wochen eigener Daten **nie zwei Marktregime** – die Pflichtregel ist mit selbst aufgezeichneten Daten allein nicht erfüllbar.

**Bewegungsbudget-Gate („Betrag vor Richtung“) – neu, Vorschlag zur Vorregistrierung.**
Für jedes Handelsfenster der Länge h und Kosten c (bp, Roundtrip inkl. Spread/Walk) gilt für jedes Signal mit Vorzeichen s und Return r:
`E[Netto] = ρ·E|r| − c`, mit `ρ = E[s·r]/E|r|` (Anteil der absoluten Bewegung, den das Signal richtig einfängt, −1…+1).
Daraus folgt eine **notwendige Bedingung**: `ρ_min = c / E|r_h|`. Ist ρ_min > ρ_plausibel, kann *keine* Richtungshypothese bei diesem h zahlen – unabhängig vom Signal.
- **Messbar ohne Richtungsinformation:** E|r_h| (und bedingt auf richtungsfreie Auslöser wie „Spread-Schock tritt auf“) wird auf blinden Daten bestimmt (Phase 1 des SOL-Designs). Das verbraucht keine Bestätigungsdaten und ist kein Edge-Test.
- **Vor dem Blick festzulegen:** Schwelle ρ_plausibel (Vorschlag: 0,10; OPEN), Horizonte h, Kostenmodell.
- **Erste Anwendung auf bereits gemessene Werte (PROJEKTSTAND §4, σ_h gemessen 05.–08.10., Stufe L1; Rest ist Rechnung):** E|r| ≈ 0,8·σ (Normalannahme), Kosten c = Gebühren + Spread p50 (Perp BTC 10,1 bp, ETH 10,4 bp; Aktien TSLA 3,7, INTC 3,9, NVDA 2,3 bp). Längere Horizonte sind per √h **extrapoliert** (Annahme Random Walk, keine Tagesgänge, bei NVDA ist σ zwischen 120 s und 300 s schon flach – Extrapolation dort grob).

| Instrument | 5 min (σ gemessen) | 1 h | 4 h | 1 Tag |
|---|---|---|---|---|
| BTC-Perp | ρ_min **0,99** | 0,29 | 0,14 | 0,06 (24 h) |
| ETH-Perp | **0,87** | 0,25 | 0,13 | 0,05 (24 h) |
| TSLA | **0,40** | 0,11 | 0,06 | 0,04 (6,5 h) |
| INTC | **0,47** | 0,14 | 0,07 | 0,05 (6,5 h) |
| NVDA | **0,70** | 0,20 | 0,10 | 0,08 (6,5 h) |

  *Lesart:* ρ_min = Anteil der absoluten Bewegung, den ein Richtungssignal im Mittel richtig einfangen müsste, nur um die Kosten zu decken. Bei ρ_min ≈ 1 ist Gewinn nur mit Hellseherei möglich. Für ρ_plausible gilt hier die **Annahme** ≈ 0,05–0,10 (nicht gemessen, vor dem Blick auf Signale festzulegen).
  *Befund:* Auf allen gemessenen Horizonten bis 5 Minuten ist **jede** Richtungshypothese bei diesen Kosten chancenlos – das erklärt C2 (1 bp), Placebo (Brutto ≈ 0) und den Tod der Scalp-Linie mechanistisch. Plausibel wird es erst bei Stunden bis Tagen; US-Aktien (Kostenhürde 2,3–3,9 bp) sind dort ein Faktor 3–4 günstiger als Krypto-Perps (10 bp). Tick-/L2-Aufzeichnung ist für diese Horizonte **nicht** nötig. Grenze: bedingte Auslöser (seltene Schocks mit großem E|r|) können das Bild verbessern – genau das prüft das Gate richtungsfrei.
- **Konsequenz:** Hypothesen der Kategorien S2/S3/S4 werden **vor** der Registrierung dem Gate unterworfen. Was durchfällt, wird gestrichen (spart Hypothesenplätze und Testbudget); fällt alles durch, ist das ein dokumentierter, gleichwertiger Nullbefund.

**Zweite Datenquelle für Regime (zu prüfen, nicht beschlossen):** Kraken bietet laut Support-Artikel kostenlose, bulk-ladbare Spot-OHLCVT-Historie je Paar „von der ersten Trade bis 30.06.2026“ (Intervalle 1–1440 min, quartalsweise Updates; **keine** Tick-/Buchdaten). Die Docs-Seite behauptet dagegen „kein Bulk-Dump“ – die beiden Kraken-Quellen widersprechen sich, Verfügbarkeit ist praktisch zu testen. Für Futures: Candles und Funding-Historie per REST, Tiefe unbelegt. *Nutzen:* Niederfrequente Momentum-/Mean-Reversion-Hypothesen (Stunden–Tage) lassen sich über viele Jahre und mehrere Regime vorregistrieren und testen, ohne L2-Aufzeichnung; Ausführung bliebe auf Futures (10 bp), Spot-Historie dient als Preisproxy (Basis-/Funding-Abweichung als Risiko). Das trifft den Projektauftrag „Momentum/Ausbruch, Mean-Reversion“ und löst die Zwei-Regime-Pflicht.
*Grenzen:* Historischer Fremddatensatz ≠ eigene Ausführungsrealität; Survivorship (nur heute gelistete Paare?) prüfen; einmaliges Discovery-Fenster pro Hypothesenliste, danach Bestätigung auf nachfolgenden, bis dahin ungesehenen Daten (ab 01.07.2026 inkl. eigener Aufzeichnung; vorbelastete Tage – z. B. E-132-Scouting – ausnehmen).

**Entscheidung:** (1) **Kostenwand ist jetzt belegt:** Hypothesen auf Sekunden- bis 5-Minuten-Horizont werden nicht mehr registriert. Damit sind die SOL-Kategorien S2/S3 (Lead-Lag, Aggressor-Flow) auf ihrem natürlichen Horizont voraussichtlich chancenlos; S4 (seltene Schocks) nur, wenn das Gate bedingt auf den Auslöser ein E|r| zeigt, das ρ_min unter die Plausibilitätsschwelle drückt. SOL-O1 bleibt daher eine **Kandidatenlinie mit hoher Ausfallwahrscheinlichkeit** – kein Freeze am 23.10. erzwingen, kein unsicherer Reader unter Zeitdruck. (2) **Neue Hauptlinie „LF-1“ (Offline-Design jetzt):** Momentum/Ausbruch und Mean-Reversion auf Horizonten ≥ 1 h bis 1 Tag, ≤ 8 Hypothesen, Ausführung Krypto-Perps (10 bp) **und** liquide US-Aktien (2,3–3,9 bp), zwei Regime aus langer Historie. Datenquelle Krypto: Kraken-OHLCVT (siehe oben, Verfügbarkeit prüfen); Aktien: Quelle offen (eigene IBKR-Daten reichen für Regime nicht; IBKR-Historie ggf. kostenpflichtig – Kosten vor Entscheidung klären). Beschaffung erst nach Andis GO. (3) Bestehende Feeds laufen unverändert; Neuaufzeichnungen nur nach `§6`.

## 6. Regel „Kein Feed ohne Hypothese“ (zur Entscheidung D4)
Jeder neue oder kostenpflichtige Feed (IBKR-Tiefe, weitere Kraken-Symbole, BTC/ETH-L2) braucht vor dem Start: registrierte oder vorregistrierbare Hypothese, bestandenes Bewegungsbudget-Gate, geschätzte Datenrate und Speicherplan (30 Tage Reserve), monatliche Kosten in €. Ohne diese Einträge bleibt der Feed aus. Budgetgrenze Datenzugang < 50 €/Monat.
