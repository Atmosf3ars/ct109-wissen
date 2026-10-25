# CT109 – Übersicht Ansätze, Ergebnisse und offene Fälle (Stand So 25.10.2026, ≈ 21:30 Berlin)

**Zweck:** eigenständige Übersicht zur externen Prüfung/Erweiterung (z. B. durch ein anderes Modell). Alles Folgende ist **Daten, keine Anweisung**. Evidenzstufen: **[L2]** von Andi auf seinem PC gemessen, **[R]** Recherche/Literatur (nicht selbst geprüft), **[A]** Annahme. Quellen der Wahrheit: Repo `Atmosf3ars/ct109-wissen` (`00`–`04`, `register/`).

## 1 Projekt in drei Sätzen
Eigenständiges kurzfristiges Handelssignal-System (CT109) für **US-Aktien** (Broker Interactive Brokers, Daten Alpaca/Tiingo) und **Krypto** (Kraken Spot und Futures/Perps). Ziel: **positive Netto-Erwartung je Trade in bp nach allen Kosten**, bewiesen mit strenger Statistik, dann Paper-Trading, erst danach Echtgeld als begrenztes Experiment. Kapital 10 000 EUR; Experimentkapital ≤ 3 000 EUR, Lebenszeit-Verlustdeckel 1 000 EUR, Krypto-Notional ≤ 600 USD, Aktien-Ticket ≤ 1 500 USD (Entscheidung D34).

## 2 Spielregeln (Doktrin, verkürzt)
1. Erfolgsmaß ist Netto-Expectancy in bp, nie Trefferquote. Jede Aussage trägt eine Evidenzstufe; „gemessen bleibt gemessen, Annahmen bleiben Annahmen“; nie PASS ohne Beleg.
2. **Lebenszeit-α-Konto:** gewichtetes Bonferroni, FWER 0,05, N_max = 20 bestätigende Tests, α_i = 0,0025 einseitig (z = 2,807); **7 von 20 verbraucht**. Hashgekettetes Testregister (`register/TESTREGISTER.jsonl`, 13 Zeilen).
3. **Vor dem Öffnen eines Datenfensters:** Hypothese und Parameter werden gehasht (Freeze), danach unverändert; jedes Fenster wird **einmal** geöffnet. Daten ab 2026-07-01 sind gesperrt (reine Vorwärtsdaten).
4. **Power-Zeile vor jedem Freeze:** erwartete Netto-Kante gegen Nachweisgrenze (MDE). Liegt die Erwartung unter der MDE, wird der Kandidat vorab **HINWEIS-Klasse** (kein α, kein „bestätigt“) oder nicht aufgenommen. „0 Trades“ = INSUFFICIENT, nie Nullbefund. Inferenzeinheit sind unabhängige **Episoden**, nicht Ereignisse.
5. Pflicht-Bausteine je Test: Block-Bootstrap über Kalenderwochen, Placebos (Zeitversatz, vol-gematcht bzw. gleiches Symbol), Kostenstress, Konzentrationsprüfung, zwei Zeithälften, ≥ 2 Zustände (ex ante, z. B. RV30-Terzile), **Kalibrierung der Gesamtregel an Nullwelten (Fehlpass ≤ 5 %)**, Survivorship beziffert.
6. Kategorien: BESTAETIGT / NICHT BESTAETIGT / POSITIV-UNTERPOWERT / NICHT NACHWEISBAR (kein Nullbefund bei Kante < MDE) / INSUFFICIENT / HINWEIS.
7. Paper-Trading vollautomatisch ist Pflicht vor Echtgeld; Echtgeld nur mit zwei Schlüsseln (Andi + Einsatzleiter). Orders, Echtgeld, Registry-Schreiben, Secrets, Käufe, Host-Aktionen nur nach förmlichem GO-Satz „GO <Kurzname> – <Hash>“.

## 3 Gemessene Fakten (Basis aller Rechnungen)
- **Kosten Kraken [L2, Andis Konto; Spot-Tier-1 im Juli 2026 von 0,25/0,40 % auf 0,40/0,80 % angehoben [R]]:** Spot Tier 1 **0,40 % Maker / 0,80 % Taker** (Tier 2 ab 2 501 USD: 0,30/0,60; Tier 3: 0,22/0,38); Futures Tier 1 **0,02 % / 0,05 %**. Futures-Spreads im liquiden Pool ≈ 5–8 bp, Top-of-Book-Tiefe in Alts nur ≈ 100–400 USD [L2/A]; Preiswirkung über Level 1 hinaus **ungemessen**.
- **Aktien-Kosten [A/R]:** IBKR Tiered 0,0035 USD/Aktie, Mindestprovision 0,35 USD/Order ⇒ bei 1 500-USD-Tickets ≥ 2,3 bp/Seite, bei 750 USD ≥ 4,7 bp, zuzüglich Börsen-/Regulierungsgebühren und Spread (Prüfung Modell C; unsere frühere Annahme „1–2 bp“ war zu niedrig); Small Caps 25–100 bp Rundreise je Dollarvolumen-Klasse; IBKR-Gebührenseite nicht verifiziert.
- **Daten [L2]:** Kraken Time & Sales (jeder Trade, bis 2026-06-30, 1-Minuten-Aggregate für ~41 Paare 2019–2026), Kraken-Funding nur 2025-10-15 … (API-Deckel ≈ 9 000 Stundenwerte), Binance-Funding 2019–2026-06 für alle 34 Pool-Coins, Alpaca-Tageskerzen (SIP) 2016–2026-06 für ≈ 2 600 Symbole inkl. Delistings, SEC Form 3/4/5 2006–2026 Q2, Tiingo-Tageskerzen (Lizenz „Internal Use“, Tageslimit), eigene L2-Aufzeichnung auf Server CT109 (SOL 14 Tage versiegelt; BTC/ETH Spot-L2 seit 23.09.2026; wächst).
- **Auflösungswand [L2+Rechnung]:** nachweisbar ist bei ~6,5 Jahren Daten nur ein **Netto-Sharpe ≳ 1,3** (SR_MDE = 3,34/√T). Bei geklumpten Ereignissen unterschätzt die analytische MDE die wirksame Nachweisgrenze um ≈ Faktor 3 (Nullwelt-SE 80 bp statt 27 bp bei INSIDER-ALL).

## 4 Getestete Ansätze (alle ohne nachweisbaren Vorteil)
| # | Ansatz | Markt | Ergebnis | Quelle |
|---|---|---|---|---|
| 1 | lf1-H1 TS_MOM (Zeitreihen-Momentum BTC 24 h) | Krypto | Nullbefund (Altlast) | Reg. 1 |
| 2 | lf1-H2 SHOCK_FADE (Schock-Umkehr BTC 24 h) | Krypto | Nullbefund (Altlast) | Reg. 2 |
| 3 | lf2-R-H1 STR(5), H=5 (Kurzfrist-Umkehr, Tages-Querschnitt) | Aktien | nicht nachweisbar, unterpowert, Survivorship | Reg. 3 |
| 4 | lf2-R-H2 MOM (Querschnitts-Momentum) | Aktien | nicht nachweisbar, unterpowert | Reg. 4 |
| 5 | **K4 AFTERSHOCK-LONG** (Long nach Krypto-Kaskade, Retracement; XBT, ETH, 4 h) | Krypto | **407 Episoden, netto −14,1 bp, p 0,94, LCB −38,6** → nicht nachweisbar | Reg. 5/9 |
| 6 | **K4P** (gleiche Regel auf 32 liquiden Alts) | Krypto | 781 Episoden, −29,7 bp, p 1,0 | Reg. 6/10 |
| 7 | **K6 FLOW** (Stunde mit ≥ 20× Median-Notional und |Imbalance| ≥ 0,7; C = Fortsetzung, R = Umkehr; 34 Paare, 4 h) | Krypto | C 2 973 Ep. −24,4 bp; R 2 971 Ep. −30,7 bp → beide nicht nachweisbar | Reg. 7/11 |
| 12 | **GS Gold-Silber** (GLD/SLV wöchentlicher Spread; GS-C Fortsetzung, GS-R Umkehr; HINWEIS-Klasse) | ETF | GS-C netto +6,3 bp/Woche (3,3 % p. a.), p 0,285; GS-R −18,3 bp/Woche; MDE 29,4 bp/Woche | Reg. 12/13 |
**Kernbefund Krypto:** das 4-h-Ereignis-/Umkehr-/Flow-Muster hat **brutto ≈ 0** (nicht nur Kostenproblem). K4/K4P/K6 sind echte, gefrorene α-Tests (D41/D43); Kalibrierung C7 bestanden (Fehlpass 0/200).

## 5 Vorab als HINWEIS-Klasse eingestuft (kein α, nicht oder nur deskriptiv gerechnet)
| Ansatz | Grund | Entscheidung |
|---|---|---|
| **INSIDER-ALL** (Form-4-Käufe-Cluster, ≥ 3 Insider, ganzes US-Universum, Long 28 Tage, Netto-Excess gegen SPY/IWM; n = 3 752, σ 1 658 bp) | Nullwelt-SE 80 bp ⇒ wirksame MDE ≈ 230–290 bp ≫ erwartete Kante 0–150 bp; Hedge-Wechsel (SPY/IWM/Beta/Mix) ändert fast nichts | D47 |
| ~~Spot/Perp-Funding-Carry~~ **REVIDIERT (D53)** | ursprünglich „Spot-Bein 80–160 bp ≫ Funding-Ertrag“ — **Rechenfehler**: Break-even je nach Funding 29–146 Tage; bei langer Haltedauer nicht kostentot ⇒ als **H-A CARRY-HOLD** wieder Kandidat (§6) | D48→D53 |
| **FUND_XS** (Perp-only, nach Funding sortiert, dollar-neutral, wöchentlich) | Streuung 5–6,4 %/Woche ⇒ MDE ≈ 100–118 bp/Woche ≫ erwartet 10–25 bp − Kosten | D49 |
| **CS_MOM14 / RESREV** (Krypto-Querschnitt) | MDE ≈ 118 bp/Woche brutto | D42 |
| Weitere Tages-Aktienkandidaten (Tauziehen Nacht/Tag, FINRA-Short-Volumen, S&P-500-Ereignisse) | erwartet ≈ 1 bp/Tag netto vs. MDE 2,4–4,8 bp/Tag | D29/D38 |
| FUND_CROWD (Funding-Extrem → Gegenposition 72 h), WEEKEND-UMKEHR | ereignisbasiert, geklumpt; Kraken-Funding-Historie nur ≈ 12 Monate; **formal noch nicht entschieden** | `03` §8.6 |

## 6 Offene Fälle (Kandidaten)
1. **8-K-Nachrichten (US-Aktien, EDGAR):** Ereignisse nach Item-Code (1.01 Verträge, 2.02 Ergebnisse, 4.02 Nicht-Verlässlichkeit/Restatement, 5.02 Führungswechsel, 3.01 Delisting-Hinweis …). Plan: EDGAR-Bulk-Einreichungsdaten zählen (nur Anzahl/Streuung, keine Renditen), Power-Zeile mit Nullwelt-SE, dann Freeze oder HINWEIS. **Erwartung:** hohe Einzelstreuung, wahrscheinlich ähnliche Wand wie INSIDER-ALL; aussichtsreicher sind seltene Items mit großem Drift (4.02, 3.01), die aber oft nur Short-seitig und schwer handelbar sind.
2. **SYMPATHY-REVERSION** (idiosynkratischer 4σ-Sprung eines Sektor-Leaders, Mitläufer federt zurück, Fenster 15 min–3 h): braucht Intraday-Aktiendaten (Alpaca/IBKR, Lizenz/Preis klären); Autor-Rechnung σ 80 bp, μ_netto 15 bp, ~260 Ereignisse [A].
3. **Mikrostruktur/Maker-Strategien auf eigener L2-Aufzeichnung (CT109):** theoretisch hohe Sharpe-Struktur (Futures-Maker 2 bp/Seite), **aber 25.10. in D30 bereits verworfen:** OBI/OFI/Mikropreis/Trade-Sign/VPIN haben brutto nur 0,5–2 bp gegen 10–16 bp Taker-Kosten bzw. 4 bp + adverse Selektion beim Maker; eine Binance-Studie [R, arXiv 2602.00776] fand Maker nirgends profitabel. Die Wiederaufnahme am 25.10. abends (D49-Plan) widerspricht dem und **braucht neue Evidenz** (z. B. eigene Fill-Simulation mit Time & Sales, Warteschlange unbekannt). Historie kurz (SOL 14 Tage, BTC/ETH Spot-L2 seit 23.09.).
4. **Kalender-/Basis-Strukturen ohne Spot-Bein** (Kraken Fixed-Maturity-Futures vs. Perp): deterministische Konvergenz, aber Gebühren, Margin und Produktverfügbarkeit **ungeprüft**.
5. **Diversifiziertes Forward-Paper-Bündel** aus schwachen Signalen (GS-C, AFTERSHOCK-Reste, Insider, STR/MOM): Diversifikation hebt die Sharpe; Beleg nur aus dem Betrieb, Kriterien vor Start hashen (Paper-Säulen A–D, Entwurf `RUNDE3_SPEC_v0.1_ENTWURF.md` §10).
6. **Forward-Fenster Juli–Oktober 2026** (gesperrt, bereits vorhanden): Aktien, Kraken-Trades und Funding als unabhängiges Bestätigungsfenster für alles, was HINWEIS-positiv wird (Skript noch zu schreiben).

7. **H-A CARRY-HOLD (Vorrang, D53):** Short PF_XBTUSD/PF_ETHUSD, gleicher Notional Spot als Sicherheit; Ein-/Ausstieg über 7-Tage-Funding mit Schwellen aus Binance 2019–2023 (Test 2024–2026H1 plus Kraken 54 Wochen); Spot-Bein einmal je Haltephase (80–160 bp). Erwartung 6–14 bp/Woche gegen MDE ≈ 4–6 bp/Woche (Binance-Proxy, 340 Wochen) bzw. ≈ 12 bp (nur Kraken) [Rechnung eines externen Prüfers, nachzurechnen]. Risiken: Funding-Zerfall seit 2024, Liquidation/Abschlag/ADL, Börsenrisiko, Steuer (DE) [A]. Live-Ertrag bei 600 USD ≈ 36 USD/Jahr; der Wert liegt im Beleg.
8. **H-B TOM-7** (Turn-of-the-Month S&P 500: Long T−4 … T+3 gegen Placebo zufälliger 7-Tage-Fenster; Erwartung 33–65 bp, MDE ≈ 48 bp [A]; Tiingo-Altfenster 1993–2015 ungeöffnet); **H-C INSIDER-OPP-VS** (opportunistische Insider, vol-skaliert, 2006–2015; MDE ≈ 100–180 bp, wahrscheinlich HINWEIS); **H-D 13D-ERST** (SC 13D-Erstmeldungen, erst zählen); **8-K-Items** (Zählung läuft); **Gegenbeispiel H-E INTRADAY-MOM** (nachweisbar, aber kostentot).

## 7 Beobachtungsliste (ohne Geld, ohne α; Daten fehlen)
Gamma-Pinning/GEX und 0DTE-Gamma (Optionen-Open-Interest je Strike fehlt), TDA/Orderbuch-Topologie und kritische Verlangsamung des Buchs (L3/L2-Tiefe fehlt, viele Freiheitsgrade), DeFi→CeFi/MEV-Lead-Lag (Mempool/Node), Wick-Catcher bei delisteten Token, Kraken-Listing-Lebenszyklus, Token-Unlocks, OI-Fade, Aktien-Perps bei Kraken (PF_AAPLXUSD u. a., nur gesehen, Zugang/Hebel ungeprüft).
**Per Literatur verworfen [R]:** Overnight-Drift, S&P-Indexereignisse, Pre-FOMC-Drift, Earnings-Announcement-Prämie, Vol-Managed-Portfolios, Same-Month-Saisonalität, Januar-Effekt, Hawkes/Entropie-Roh-Signale, Runde Zahlen, GitHub/Google-Trends.

## 7a Archiv aller bewerteten, aber nicht gerechneten Ideen (Quellen: Nachtforschung mit acht Agenten, vier Ideenlisten von Andi; Details `03` §8.3–§8.6)
**Aktien:** K1/K1r zustandsbedingte Residual-Umkehr (Nagel 2012; Kante nur bei hoher Vola, Zustand nach Blick auf Daten gewählt ⇒ kontaminiert, INSUFFICIENT/HINWEIS); K2 Nacht/Tag-Tauziehen (Akbas u. a.; netto ≈ 1 bp/Tag); K3 Low-Vol long-only (Risikoreduktion, kein Gewinn-Anspruch); FINRA-Short-Volumen (Wang/Yan/Zheng JFE 2020; Historie nur ab 08/2018, Nutzungsbedingungen ungeprüft); 8-K-Nachrichten/„keine Nachrichten“ (Chan 2003); SYMPATHY-REVERSION (siehe §6).
**Krypto Struktur/Fluss:** Funding-Extrem als Crowding-Signal (FUND_CROWD/FUND-KONTRA; kein Peer-Review-Beleg für Richtungshandel [R]); Querschnitts-Momentum 14 d (Fieberg 2024: Alphas zerfallen); Volumen-/Trade-Größen-Familie (VOLREV, ABVOL, TRADESIZE; für Coins mit Perps Null vorhergesagt [R]); Token-Unlock-Short (n 70–125 Ereignisse nötig, Kalender extern); Kraken-Listing/Delisting-Lebenszyklus; Stablecoin-Emission; OI-Absturz-Fade (OI-Historie unverifiziert); Wochenend-Umkehr (≈ 680 Wochenenden, Chance ≈ 5 %); Wick-Catcher bei Zwangsverkauf delisteter Token; **Liquidations-Erschöpfung** (≈ K4-Familie, Horizont 3–15 min in der Kostenwand); ML-Bündelung (Ridge/flacher Baum, Vorab-Abbruchregel, erwartet Scheitern).
**Mikrostruktur (D30 verworfen):** OBI/OFI, Mikropreis, Trade-Sign, Spot↔Perp-Lead-Lag (0,5–2 bp brutto), VPIN; VWAP/TWAP-Iceberg-Erkennung (braucht L3, Null „zirkulär“); Transfer-Entropie Fluss→Preis (Schätzer-/Null-Probleme, Mehrfachtest); Latenz-Graph/No-Arbitrage-Schleifen (Infrastruktur-Kante); DeFi→CeFi/MEV-Lead-Lag (Mempool/Node sprengt Budget); Spektralanalyse fremder Algos (Tick-Historie fehlt).
**Optionen/Gamma (Daten fehlen):** Gamma-Pinning/GEX, Gamma-Entzug nach Verfall (Autor ≥ 90 bp je Event bei ≈ 100 Events [A]; Optionen-Open-Interest-Abo, Preis ungeprüft), 0DTE-Gamma-Vakuum; Makro-Attention-Lag/VECM (Intraday-Mehr-Asset-Daten fehlen); Dark-Pool-Shadowing und „Nash-Kollaps“ (Off-Exchange-Prints nicht trennbar, ATS-Daten wöchentlich und verzögert).
**Zustandsvariablen-Kandidaten (kein eigener Trade):** TDA/persistente Homologie, Entropie, Change-Point, **kritische Verlangsamung des Buchs** – dürfen nur antreten, wenn sie in der Kalibrierung eine einfache Referenz (RV30-Perzentil, Volumen-z) schlagen.

## 8 Laufender Betrieb und Termine
- **lf1 (Krypto H1/H2) läuft als Paper-Betriebstest** auf CT109 (kein Edge-Anspruch); **Bilanz 02.11.2026**. Aktien-Paper (lf2) separat vorbereitet.
- Offen: D34-Bestätigung (Verlustdeckel), Kraken-Futures-Kontoumfang (Hebel/Shorts/ESMA-Grenzen), IBKR-Gebührenseite, Tiingo-Limit-Reset (November), Retention Stufe 2 (Mitte November), Alpaca-ToS (nur lokale Forschung, [A]).

## 9 Methodische Schwächen, die wir selbst sehen (bitte besonders prüfen)
1. **Auflösungswand:** fast alle Familien liegen unter der MDE. Gibt es Strukturen mit netto-Sharpe ≳ 1,3 jenseits von Maker/Basis/Diversifikation?
2. **Nullwelt-Konstruktion** (Zeitversatz der Ereignisdaten) erbt Autokorrelation und Marktstruktur; skaliert auf gezählte Streuung. Gibt es bessere Nullwelten (Block-Permutation, Faktorresiduen)?
3. **Kostenannahmen** (Aktien Small-Cap 25–100 bp, Krypto-Slippage jenseits Level 1) sind ungemessen.
4. **Survivorship:** Alpaca enthält viele Delistings, aber Ticker-Wiederverwendung/Umbenennungen können Firmen verwechseln (≈ 108 Insider-Ereignisse ohne Bars, 9 frühe Enden).
5. **Mehrfachtest-Konto** (Bonferroni N = 20) könnte zu streng sein; Alternative: Online-FDR (α-Investing) mit Replikation im Vorwärtsfenster.
6. **Datenfenster werden einmal geöffnet**; Entdeckung erfolgt oft auf Zählungen/Streuungen. Gibt es zusätzliche zulässige Informationen vor dem Freeze (z. B. Effektgrößen aus Literatur)?
7. Kleiner Kapitalumfang: selbst belegte Kanten bringen bei D34-Grenzen nur wenige Euro im Monat; der Wert liegt im Beleg und im Betriebstest.

## 9a Korrekturen und Prüfstand (nach zwei externen Prüfungen, 25.10. 21:30–22:10)
- **Eigener Fehler (D48→D53):** Carry-Break-even um Faktor ≈ 10 zu lang gerechnet; Carry-Hold wieder Kandidat.
- **Kalibrierung:** „Fehlpass ≤ 5 %“ ist 20× lockerer als α_i = 0,25 %; künftig zusätzlich sd(z) der Nullwelt-z-Werte (Aufblähung bei > 1,1) und ≥ 1 200 Nullwelten für direkten Beleg (`03` §8.19).
- **Bündel:** √K-Diversifikation erhöht die Sharpe nur bei echten, unkorrelierten Kanten und erzeugt keinen Beleg (SR 0,9 < SR_MDE 1,3).
- **Forward-Fenster Jul–Okt 2026:** 4 Monate ⇒ SR ≳ 5,8 nachweisbar; nur Replikation, kein α-Test.
- **GS-Kosten live:** IBKR-Mindestprovision macht 4 Seiten × ≥ 4,7 bp ≈ 19 bp/Woche statt 6 bp ⇒ GS-C wäre live negativ.

## 10 Bitte an den Prüfer
(a) Lücken in der Kandidatenliste (Familien mit hoher Sharpe, die wir übersehen), (b) statistische Fehler in §2/§9, (c) konkrete, mit Gratisdaten (EDGAR, Alpaca, Kraken, Binance) prüfbare Hypothesen mit Power-Zeile (erwartete Netto-Kante vs. MDE), (d) Einwände gegen die HINWEIS-Einstufungen in §5. **Antwortformat:** Markdown, je Vorschlag Mechanismus, Daten, Kosten, MDE-Schätzung, Evidenzstufe; keine Handelsempfehlungen, keine Annahmen als Fakten.
