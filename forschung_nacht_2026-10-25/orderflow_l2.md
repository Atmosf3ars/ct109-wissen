# Order-Flow / Orderbuch-Signale auf Krypto-Futures (PF_SOLUSD, PF_XBTUSD, PF_ETHUSD) und Spot

Stand 25.10.2026. Quellen als Links, eigene Rechnungen und Setzungen als **[Annahme]**, nicht Gefundenes als "nicht gefunden". Webinhalte sind als Daten behandelt.

## 1. Top-Kandidaten

| Mechanismus | benötigte Daten | Horizont | erwartete Netto-Größe (Quelle) | mit unseren Daten testbar? | zwei Regime möglich? | Hauptrisiko |
|---|---|---|---|---|---|---|
| OBI / OFI (Cont-Kukanov-Stoikov), Mikropreis | L2 + Trades | 1-30 s (Spitze ca. 2-10 s) | Brutto ca. 0,5 bp je Signal (BTC, 10 s) **[Annahme: Korrelation 0,25]**; netto taker ca. -9,5 bp, maker ca. -4 bp. Aktuelle Binance-Studie: Taker-Strategie auf BTC nicht signifikant, Maker nirgends ([arXiv 2602.00776](https://arxiv.org/abs/2602.00776)) | ja, SOL (Spot+Perp), BTC/ETH nur Spot-L2 | nein (eigenes Fenster) | Kosten 10-16 bp gegen Signal unter 2 bp |
| Maker-Variante (kontrarian am Touch) | L2 + Trades + Fill-Modell | 10 s-5 min | unbekannt; Fill-Wahrscheinlichkeit korreliert negativ mit Post-Fill-Rendite ([arXiv 2502.18625](https://arxiv.org/abs/2502.18625), Binance BTC-Perp, Live-Experiment); Netto nicht angegeben | nur mit Replay-Tool (B2 laut 03 §4 blockiert) | nein | adverse Selektion, Queue-Position nicht beobachtbar |
| Trade-Sign-Persistenz / Fluss-Imbalance | Trades mit Taker-Seite | Minuten-Stunden | Kim/Hansen 2026: Imbalance sagt 4-12 h voraus, Brutto ca. 0,5 bp je Ereignis, "not a profitable strategy" ([arXiv 2607.09426](https://www.alphaxiv.org/abs/2607.09426), Binance, 2021-24) | ja (Trades vorhanden) | Trades-Historie extern (Binance aggTrades) | Brutto zu klein |
| VPIN-artige Maße | Trades (Volumen-Buckets) | Minuten-Stunden | als Richtungssignal schwach: "poor predictor of short run volatility", Kopplung an Handelsintensität ([Andersen/Bondarenko, Kellogg 2014](https://www.kellogg.northwestern.edu/academics-research/research/detail/2014/vpin-and-the-flash-crash/)); Richtung nicht vorhergesagt | ja | nein | Als Richtungssignal ungeeignet; höchstens Zustandsfilter für E\|r\| |
| Lead-Lag Spot→Perp, BTC→Alts | Mid/Trades beider Märkte | 1-120 s | BTC→ADA 16-118 s, im Mittel 57 s, abnehmend, Kosten nicht getestet ([Anderson 2023](https://www.businessperspectives.org/index.php/journals/investment-management-and-financial-innovations/issue-421/a-tick-by-tick-level-measurement-of-the-lead-lag-duration-between-cryptocurrencies-the-case-of-bitcoin-versus-cardano)); Börsen-Lag bis 15 s, profitabel nur bei niedrigsten Gebühren und Mid-Ausführung ([Schei 2019](https://research-api.cbs.dk/ws/portalfiles/portal/59795067/612646_High_Frequency_Lead_Lag_Relationships_in_The_Bitcoin_Market.pdf)) | SOL Spot→Perp ja; BTC-Spot→SOL-Perp ja; BTC/ETH-Perp nein | nein | Futures führen eher ([arXiv 2506.08718](https://arxiv.org/abs/2506.08718v1)); Spot-Bein 80 bp unmöglich |
| Funding-/Prämien-Signal | Ticker (funding_rate, premium, OI) + lange Historie | 8 h-Tage | kein Netto-Wert für Richtungshandel gefunden; Basis-Arbitrage Sharpe ca. 1,8 (BTC, höchste Binance-Gebührenstufe), schrumpft ca. 11 %/Jahr, zwei Beine ([He/Manela/Ross/von Wachter 2024](https://arxiv.org/pdf/2212.06888v5)) | Ticker ja; Historie per REST **nicht geprüft** | ja, falls Funding-Historie mehrjährig | BTC-Renditen schon durch H1/H2 verbraucht |
| Liquidations-Kaskaden | Trades (type=liquidation), OI, Preis | 1-30 min Onset, Reversion Stunden | 88 % des erzwungenen Verkaufs in 30 min, Schwere nicht vorab messbar ([arXiv 2608.03616](https://ideas.repec.org/p/arx/papers/2608.03616.html)); Fade-Rendite nicht gefunden | nein: 0-1 Ereignis in 14 Tagen | nur über OHLCVT-Proxy | n zu klein, Verwandtschaft zu gescheitertem SHOCK_FADE |

## 2. Kosten bei Kraken Futures (geprüft)

- Gebührentabelle ([kraken.com/features/fee-schedule](https://www.kraken.com/features/fee-schedule), abgerufen 25.10.2026, Seite ohne Datum): Stufe 1 (unter 5 Mio. USD/30 Tage) **Maker 0,02 %, Taker 0,05 %** je Seite. Bestätigt von [Datawallet, Stand 24.08.2026](https://www.datawallet.com/crypto/kraken-fees-explained). Die Annahme "Taker 0,05 %" im Briefing ist damit für die Standardstufe belegt; die API-Tabelle ist laut [Kraken-Doku](https://docs.kraken.com/api-reference/fee-schedules/get-fee-schedules.md) veraltet, die tatsächliche Rate liefert der Spot-Endpunkt GetTradeVolume (für das eigene Konto nicht geprüft).
- Roundtrip: **taker 10 bp, maker 4 bp, gemischt 7 bp**. Maker-Rebate (-0,003 %) erst ab 250 Mio. USD/30 Tage; mit 5 000-USD-Trades unerreichbar (Stufen zählen auch Spot-Volumen und Vermögen).
- Spread: laut Gate-Spec (aus 03 §5, Stufe L1) BTC ca. 0,1 bp, ETH ca. 0,4 bp, SOL nur Obergrenze (gesamt 16 bp), nicht gemessen. Tick: BTC 1 USD, ETH 0,1, SOL 0,01 ([Kraken Kontraktspezifikation](https://support.kraken.com/se/articles/4844359082772-Linear-Multi-Collateral-Perpetual-Contract-Specifications)). Relativer Tick ist bei SOL am größten, dort ist der OBI-Effekt laut 2602.00776 stärker, aber der Spread auch.
- Funding: stündlich, Rate = Prämie/8, Deckel ±0,5 %/h (gleiche Spezifikation). Spot taker bis 0,80 % ([Kraken-Support](https://support.kraken.com/articles/201893638-fee-schedule)).

## 3. Begründung je Mechanismus

**OBI/OFI.** Cont et al. zeigen einen linearen Zusammenhang zwischen OFI und Preisänderung, Steigung umgekehrt proportional zur Tiefe ([arXiv 1011.6402](https://arxiv.org/abs/1011.6402), 50 US-Aktien). Das ist **gleichzeitig**, nicht prädiktiv (der oft zitierte R² von ca. 70 % gilt für dieselbe Periode, vgl. [Towards Data Science](https://towardsdatascience.com/price-impact-of-order-book-imbalance-in-cryptocurrency-markets-bf39695246f6)). Prädiktive Korrelation ca. 25 % bei 10 s (dort für eine Aktie zitiert); ETH/Coinbase 2019: Effekt klingt mit dem Horizont schnell ab, Bewegungen meist unter 10 bp, "cannot directly be used for statistical arbitrage". DeepLOB-artige Krypto-Arbeiten melden 71 % Trefferquote bei 2 s, ohne Kosten und ohne Backtest ([arXiv 2010.01241](https://arxiv.org/abs/2010.01241)); Hawkes-Arbeit explizit ohne Transaktionskosten ([arXiv 2312.16190](https://arxiv.org/abs/2312.16190)). Alle sind Brutto-Werte vor Publikations-Zerfall. Mikropreis ([Stoikov 2018](https://ideas.repec.org/a/taf/quantf/v18y2018i12p1959-1966.html)) ist dieselbe Information, besserer Mid-Schätzer: Nutzen für Maker-Quote und Ausführung, kein eigener Edge.

**Taker-Ausführung.** Rechnung (BTC): Fenster 10 s, σ ≈ 2,5 bp, E\|r\| ≈ 2 bp. Bei Kosten 10,1 bp wäre ρ_min ≈ 5, also unmöglich (ρ_min = c/E\|r\| laut 03 §5). Erst bei 1 h (BTC 0,26, ETH 0,18, SOL 0,15) kommt man in den Bereich, den 03 §5 als gerade noch denkbar ansieht (Annahme 0,05-0,10). Auf diesen Horizonten ist OBI/OFI wertlos (abgeklungen).

**Maker-Ausführung.** Roundtrip 4 bp plus adverse Selektion. Ohne diese ist ρ_min bei 5 min BTC 0,41, ETH 0,28, SOL 0,23, bei 1 min 0,6-0,9: weiterhin über jeder plausiblen Schwelle. Arbeit 2502.18625: wer schnell gefüllt wird, bekommt schlechtere Folge-Renditen; tragfähig sei nur das **Gegenteil** der Imbalance (Reversal am Touch). [Albers et al. 2025](https://ideas.repec.org/a/taf/quantf/v25y2025i6p919-947.html): profitable Orders werden systematisch schlechter ausgeführt, Backtest-zu-Live-Lücke. Fill-Wahrscheinlichkeit und Queue-Position sind mit unseren Daten nicht beobachtbar [Annahme: nur Modell, kein Beleg]. Brutto-Edge müsste ≥ 4,5 bp + adverse Selektion (Größe **nicht gefunden**) sein.

**Trade-Sign-Persistenz.** Vorzeichen haben Langzeitgedächtnis (α ≈ 0,6, LSE-Aktien), Renditen bleiben trotzdem unkorreliert, weil Größe/Liquidität gegenläufig schwanken ([Lillo/Farmer](https://arxiv.org/abs/cond-mat/0311053v2)). Krypto-Evidenz: Kim/Hansen (siehe Tabelle), Brutto ca. 0,5 bp, ein Zehntel einer Standard-Taker-Gebühr.

**VPIN.** Kein Richtungssignal. Sinnvoll nur richtungsfrei, um E\|r\| bedingt zu messen (Gate aus 03 §5). Die LOB-Zustandsarbeit [arXiv 2607.09230](https://arxiv.org/abs/2607.09230) (Binance, 1-5 min) sagt Liquiditätszustände voraus, ausdrücklich ohne Profit-Auswertung; Order-Flow nur bei ETH additiv.

**Lead-Lag.** Die BTC-→-Alt-Führung liegt im Sekunden- bis Minutenbereich und schrumpft. Auf Kraken-Futures ist nur das Futures-Bein sinnvoll (10 bp Taker). Erwartete Aufholbewegung im Bereich unter 2 bp [Annahme: BTC-1-min-σ 6 bp, Beta ≈ 1] gegen 10-16 bp. Mit L2 BTC-Spot + SOL-Spot/Perp ist ein **richtungsfreies Vorab-Messen** (Kreuzkorrelation) billig und verbraucht keine Bestätigung.

**Funding/Basis.** Das einzige Feld, in dem Horizont (8 h-Tage) und Kostenbudget (ρ_min 0,07-0,26 bei 1-4 h bis 1 Tag) zusammenpassen und lange Historie möglich ist. Aber: Evidenz für Richtungshandel auf Funding **nicht gefunden**; die Basis-Arbitrage braucht Spot-Bein (Kraken Spot teuer). Past-Returns sagen die Perp-Spot-Lücke voraus (R² 0,26 laut Tabelle, He et al.).

**Liquidationen.** Kraken-Trade-Feed markiert `type=liquidation` ([Doku](https://docs.kraken.com/exchange/api-reference/futures-websocket/trade.md)), aber nur auf Kraken (klein). Kaskaden sind selten (7 Ereignisse 2022-25 in der Studie). Mit δ = 50 bp und σ = 150 bp je Ereignis wären ca. 56 Ereignisse nötig **[Annahme]**; 2 bp netto sind unauflösbar.

## 4. Power-Rechnung (alle Eingaben Annahmen)

Formel: n = ((z_α + z_β)·σ/δ)², δ = 2 bp, einseitig α = 0,05, Power 80 %. BH-Korrektur bei 8 Hypothesen (α′ = 0,05/8) etwa ×1,8. Alternative "95 %-KI ±2 bp": n = (1,96σ/2)², etwa ×0,62. σ je Trade aus Jahresvolatilität BTC 45 %, ETH 65 %, SOL 80 % **[Annahme]**; BTC-5-min-σ ≈ 13,9 bp passt zur Messung in 03 §5 (ca. 12,8 bp, rückgerechnet).

| Horizont | BTC σ / n | ETH σ / n | SOL σ / n | max. unabhängige Fenster in 14 Tagen je Asset |
|---|---|---|---|---|
| 1 min | 6 bp / 60 | 9 / 124 | 11 / 188 | 20 160 |
| 5 min | 14 / 298 | 20 / 621 | 25 / 941 | 4 032 |
| 1 h | 48 / 3 573 | 69 / 7 455 | 86 / 11 292 | 336 |
| 4 h | 96 / 14 292 | 139 / 29 819 | 171 / 45 169 | 84 |

(mit BH: ca. 537 / 1 120 / 1 697 bei 5 min, 6 444 / 13 446 / 20 367 bei 1 h.) Zusätzlich Design-Effekt für Fat Tails, Volatilitäts-Cluster und Überlappung **[Annahme: ×1,2 bis ×2]**. Die drei Perps sind stark korreliert (Annahme 0,7-0,8): N_eff ≈ 3/(1+2ρ) ≈ 1,2-1,3 (Formel wie 03 §7), Pooling hilft kaum.

Schlüsse: (1) Bis 5 min lassen sich 2 bp in wenigen Tagen auflösen, **aber** nur wenn der Brutto-Edge ≥ 12-18 bp existiert, was ρ ≈ 0,5-1 verlangt. Das Problem ist Größe, nicht Stichprobe. (2) Ab 1 h reichen 14 Tage nicht (336 Fenster gegen 3 600-11 300 nötige Trades); dort sind mehrjährige Historien nötig. (3) Abstrakt ist 2 bp als Zielauflösung für ein Taker-System sinnlos: die Kostenwand liegt bei 10-16 bp, ein Edge von 2 bp netto bedeutet 12-18 bp brutto.

## 5. Sind 14 Tage Discovery + ein Regime tragfähig?

Für **Existenz** eines sehr kurzen Zusammenhangs (OBI → 5-s-Rendite): ja, Millionen Ereignisse, aber die Literatur zeigt ihn ohnehin; Entdeckung ist unnötig. Für einen **handelbaren Netto-Edge**: nein. Spreads, Tiefe und Imbalance-Wirkung sind regimeabhängig (Oktober-2025-Crash, [arXiv 2602.00776](https://arxiv.org/abs/2602.00776); [2607.09230](https://arxiv.org/abs/2607.09230)); Zwei-Regime-Pflicht mit eigener L2-Aufzeichnung unerfüllbar (so schon 03 §5). Ein Tick-Regime-Ersatz: Binance veröffentlicht Trades/aggTrades/Klines frei, **ohne Orderbuch** ([binance-public-data](https://github.com/binance/binance-public-data); Taker-Seite-Feld nicht verifiziert). Damit gingen nur Trade-Fluss-Hypothesen über mehrere Regime, und deren Brutto-Größe ist 0,5 bp.

## 6. Zusätzliche Kanäle für BTC/ETH-Futures

Kraken-Futures-WebSocket `wss://futures.kraken.com/ws/v1`, öffentliche Feeds `book`, `trade`, `ticker`, `ticker_lite`, `heartbeat` ([Doku](https://docs.kraken.com/exchange/api-reference/futures-websocket.md)).
- `trade`: Taker-Seite (`side`), `type` (fill/liquidation/termination/block), ms-Zeit, `uid`, `seq` ([Doku](https://docs.kraken.com/exchange/api-reference/futures-websocket/trade.md)). Billig, Rate niedrig.
- `ticker`: auf 1 s gedrosselt, enthält `funding_rate`, `funding_rate_prediction`, `premium`, `markPrice`, `index`, `openInterest`, `bid_size/ask_size` ([Doku](https://docs.kraken.com/exchange/api-reference/futures-websocket/ticker.md)).
- `book`: Snapshot + Deltas (`qty` 0, vermutlich Löschung); **Snapshot-Tiefe, Update-Rate und Drosselung in der Doku nicht angegeben** (bei SOL-Perp liegen eigene Messwerte vor, 100 Ebenen).
- Limits ([Kraken-Doku](https://docs.kraken.com/exchange/guides/futures/ratelimits.md)): 100 gleichzeitige Verbindungen je Client, 100 Anfragen je Verbindung pro Sekunde (Änderungen vorbehalten); öffentliche REST-Endpunkte kosten kein Budget; Abo- und Nachrichtenraten-Limits **nicht gefunden**. Ping spätestens alle 60 s. Eine Verbindung für 3 Produkte × 3 Feeds reicht.
- Datenrate: SOL-Perp ca. 193 MiB Parquet/Tag, SOL gesamt ca. 0,47 GB/Tag (03 §4). BTC/ETH-Perp-Buch **[Annahme]** je 150-400 MiB/Tag, also +0,3-0,8 GB/Tag; bei 60 GB Disk blieben nur ca. 45-60 Tage Rohdaten, Retention-Regel nötig. Trade + Ticker allein: **[Annahme]** unter 30 MiB/Tag. Kosten 0 EUR.
- Empfehlung: Gemäß Regel "Kein Feed ohne Hypothese" (03 §6) nur `trade` + `ticker` für BTC/ETH-Perp starten (Funding-/Prämien-Reihe und BTC→SOL-Lead-Lag), `book` BTC/ETH nur nach bestandenem Gate.

## 7. Minimales vorregistrierbares Design (höchstens 3)

Vorab Gate (richtungsfrei, 03 §5) je Zelle; durchgefallene Zellen streichen. Familie wächst: BTC-Renditen sind durch H1/H2 verbraucht (03 §1), daher ETH/SOL oder BTC nur auf neuen Vorwärtsdaten.
1. **FUND-KONTRA**: extremer Funding-/Prämienwert (absolute Schwelle vor Datenblick) → Gegenposition 8-24 h, nur Perp-Bein (Taker 10 bp). Daten: Funding-Historie (REST, Verfügbarkeit prüfen) + OHLCVT, mehrere Regime. Erwartete Verwerfungswahrscheinlichkeit hoch, aber einzige Zelle mit tragfähigem ρ_min.
2. **EXTREMSCHOCK-REVERSION (Liquidations-Proxy)**: Rückgang ≥ k·σ (k ≥ 4, ex ante) in 5-15 min mit Volumen-Spitze → Long 1-4 h. Daten: OHLCVT 1m, viele Jahre. Abgrenzung zum gescheiterten SHOCK_FADE (24 h, w=4 h, k=1,5) explizit begründen.
3. **Optional, Abschlusstest Mikrostruktur**: kontrarianter Maker-Einstieg am Touch gegen OBI (nach 2502.18625), Halten 1-5 min, nur wenn Fill-Modell (B2) existiert **und** das Gate mit gemessenem adversem-Selektions-Kostenblock besteht. Erwartung: Nullbefund; Zweck ist ein sauber registrierter, billiger Schlussstrich. Nur ein Regime, daher bestenfalls "regime-lokal", kein Go für Geld.

## 8. Ehrliches Fazit

Mikrostruktur-Signale (OBI, OFI, Mikropreis, Lead-Lag, Trade-Sign) tragen bei Kraken-Futures-Kosten (taker 10 bp, maker 4 bp plus adverse Selektion) **nicht**: Signalgrößen 0,5-2 bp, selbst Studien mit Binance-Niedrigkosten zeigen für BTC keine signifikante Netto-Rendite. Der Engpass ist die Größe, nicht die Stichprobe. Lohnend nur auf Horizonten ≥ 1 h mit langer Historie.
