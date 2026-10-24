# Querdenker-Nischen: kapazitätsbegrenzte, strukturelle und ereignisgetriebene Edges für ein kleines Konto

Stand 25.10.2026. Alle Effektgrößen aus der Literatur sind **brutto** und stammen aus Zeiträumen vor ihrer Veröffentlichung. Mit **[Annahme]** markiert ist alles, was ich nicht belegen konnte. "Nicht gelesen" heißt: nur Titel oder Abstract gesehen.

## Top-Kandidaten (Rang = Plausibilität x Testbarkeit, plus Mut-Bonus)

| # | Mechanismus | Daten | Horizont | Erwartete Größe (brutto, Quelle) | Mit unseren Daten testbar? | 2 Regime? | Erfolgschance / Hauptrisiko |
|---|---|---|---|---|---|---|---|
| 1 | Funding-/Basis-Carry (Spot long, Perp short, delta-neutral) | Kraken-Futures-Funding-Historie (öffentliche Historie [Annahme: Endpunkt vorhanden, prüfen]); BTC/ETH-Funding bei uns erst ab Okt. 2026 | Wochen bis Monate | Carry im Mittel über 10 % p.a., Spitzen bis 60 % (BIS WP 1087 "Crypto carry", 2023) | Teilweise: Historie muss extern geholt werden | Ja (2021 bis 2026 hat Boom, Bär, Seitwärts) | **mittel**; Eintritts- und Austrittskosten fressen den Carry, wenn er normal ist |
| 2 | Token-Unlock-Druck (Short Perp, BTC-hedged) | Unlock-Kalender (frei, z. B. DefiLlama/Tokenomist [Annahme]); Kraken-OHLCVT | 1 bis 3 Wochen | Keyrock (Marktmacher, 16 000+ Unlocks): ca. 90 % mit Abwärtsdruck, Beginn vor dem Unlock, Team-Unlocks bis -25 % (BeInCrypto, 06.12.2024) | Ja für Preise; Kalender extern; Short nur auf Kraken-Futures-gelisteten Coins | Ja (2022 bis 2026) | **niedrig bis mittel**; Alt-Coins bluten ohnehin, Effekt ist dann nur Basisrate |
| 3 | Kraken-Listing-Lebenszyklus (Listing-Run-up; Delisting-Druck) | Erste Kerze je Paar in OHLCVT (Handelsstart); Ankündigungszeit aus Kraken-Blog/Support (frei, Scraping) | Minuten bis 10 Tage | Listings: 7,4 % Tagesrendite, 3,2 % schon bei (-3,-2) (Ante, Blockchain Research Lab, 327 Listings; Zeitraum nicht gelesen); Coinbase: -1 bis +14 %, abhängig vom Marktumfeld (Coin Metrics 2020); SHIB +25 % in Stunden (ForkLog 29.11.2021); Monero -6,55 % am Delisting-Ankündigungstag (iTiger 02.10.2024) | Handelsstart ja, Ankündigungsminute nein | Ja, aber Ereignisse ballen sich 2021 | **niedrig bis mittel**; Reaktion läuft in Minuten, vor unserer Latenz |
| 4 | Overnight-Momentum (nachts halten, tagsüber nicht) | Aktien-Tageskerzen mit Open [Annahme: Open vorhanden] | über Nacht, monatlich neu sortiert | Overnight-Persistenz 3,47 %/Monat (3-Faktor-Alpha, t=16,8), US 1993 bis 2013; Autoren: Kosten machen es "viel weniger profitabel" (Lou/Polk/Skouras, "A Tug of War") | Ja, vollständig | Ja | **niedrig**; ca. 5 bp je Nacht Kosten [Annahme] gegen kleinen Large-Cap-Effekt |
| 5 | Opex-Pinning (Kurs zieht zum Strike) | Tageskerzen, Opex-Kalender; Open Interest fehlt | 1 Tag | Schlusskurse clustern an Strikes, mind. 16,5 bp Renditeverschiebung je Verfallstag, ca. 9 Mrd. USD Marktkap. (Ni/Pearson/Poteshman, Abstract; Zeitraum nicht gelesen) | Nur als Proxy (Rundstrike-Nähe) | Ja | **niedrig**; 16,5 bp sind ein Mittel der Beträge, Richtung muss man treffen |
| 6 | Russell-Rekonstitution (Liquidität liefern an Indexfonds) | Russell-Add/Delete-Listen (frei), Kleinwert-Kurse (haben wir nicht) | Tage | "Hohe Profite" für Liquiditätsgeber, aber konzentriert und teuer (Chen/Noronha/Singal, FAJ 2003, nur Abstract; Daten 1996 bis 2002) | Nein, nur mit neuem Datenkauf | möglich | **niedrig bis mittel**; Datenlücke, Spreads kleiner Titel |
| 7 | Spin-offs (Zwangsverkäufe durch Mandate) | EDGAR Form 10 (frei), neue Ticker | Wochen bis Monate | Europa: Ankündigung +2,6 %, langfristig nicht signifikant (Veld/Veld-Merkoulova 2002); US-Studien positiv, nicht gelesen | Nein, Daten fehlen | schwer | **niedrig**; kleine Stichprobe, Lang-Zeit-Effekt in Europa nicht da |
| 8 | Maker-Quoting SOL-Perp (Spread-Vereinnahmung) | SOL-Futures-L2/Trades (ab 11.10.2026) | Sekunden bis Minuten | Maker-Gebühr 0,02 %, Taker 0,05 % (Kraken-Doku, Endpunkt veraltet, gilt nicht mehr ab 22.06.2026) | Ja, aber nur 2 Wochen, ein Regime, Queue-Position unbekannt | Nein | **niedrig**; 2 bp Maker-Gebühr gegen ca. 1 bp halber Spread plus adverse Selektion |

## Begründung je Kandidat (Signal, Kill-Kriterium, Ereigniszahl)

**1. Funding-/Basis-Carry.** Struktureller Zwang: Kleinanleger wollen gehebelt long, Arbitragekapital ist knapp, also zahlen Longs Funding (BIS 2023). Kapazität: Millionenbereich bei 5 000 USD kein Thema, die Nische ist für uns eher "zu klein für Fonds" bei Altcoins. Kosten: Spot-Taker 0,80 %/Seite (Briefing, Datawallet bestätigt Kraken-Pro-Tier-1 0,40 % Maker / 0,80 % Taker) macht 160 bp Roundtrip plus ca. 10 bp Futures. Break-even bei 10 % p.a. rund 62 Tage Haltedauer, bei Maker-Fills auf der Spot-Seite rund 31 Tage. Das ist **Arithmetik, kein Signal**: Das Ergebnis hängt vom Funding-Verlauf, nicht von Vorhersagekraft.
- Signal: Einstieg, wenn 7-Tage-Mittel des annualisierten Funding > 20 %; Ausstieg bei < 8 %; Position delta-neutral; Schwellen jetzt festschreiben, nicht aus Daten wählen.
- Kill: Netto (nach Kosten, Funding-Kosten bei Gegenvorzeichen, abzüglich T-Bill ca. 4 % [Annahme]) in einem der zwei Regime (z. B. 2021 vs. 2023) nicht positiv, oder Anteil Tage über Schwelle < 15 %.
- Ereignisse: Das sind ~10 bis 15 unabhängige Funding-Episoden in 5 Jahren (Autokorrelation), ein t-Test ist hier wertlos. Aussage über Episoden-Verteilung, nicht über p-Werte.
- Zusatzrisiken: Margin-/Liquidationsrisiko im Crash (BIS nennt Marginspitzen); Verfügbarkeit von Kraken-Futures für deutsche Privatkunden [nicht geprüft]; Funding-Mechanik und Intervall bei Kraken [nicht gefunden, Seite nicht abrufbar].

**2. Token-Unlocks.** Ökonomischer Zwang: neue Angebotsmenge, Empfänger (Team, frühe Investoren) verkaufen. Keyrock ist Marktmacher mit Eigeninteresse; die 90 % sind unkontrolliert gegen Alt-Coin-Basisrate [Annahme: Alts verlieren 2022 bis 2025 gegen BTC systematisch].
- Signal: Unlock > 1 % des Umlaufs, Empfänger Team/Investor, Coin auf Kraken Futures → Short 7 Tage vor bis 3 Tage nach Unlock, beta-hedged mit BTC-Perp.
- Kill: mittlere Netto-Überrendite (nach 5 bp je Seite, Funding, BTC-Hedge) gegenüber 1:1 gematchten Zufallsfenstern desselben Coins ≤ 0, oder Vorzeichen in einem Regime umgekehrt.
- Ereignisse (grob): Std. der 14-Tage-Überrendite ca. 15 bis 20 % [Annahme], Ziel 5 % netto: n = (1,96+0,84)² · (σ/δ)² ≈ 70 bis 125 Ereignisse. Auf Kraken-Futures-Coins vermutlich knapp; Poolen mit Spot-Signalen unmöglich (kein Spot-Short).

**3. Kraken-Listing/Delisting.** Zwang: Anleger sammeln Kraken-Liquidität (Listing) bzw. müssen aus EEA-Handel (Delisting) raus; Kraken konvertiert Restbestände zwangsweise (iTiger: Monero-Umwandlung in BTC am 06.01.2025).
- Signal A (ohne Scraping): Erster Handelstag aus OHLCVT → Verhalten Tag 0 bis Tag +10 (Fade-Hypothese: Pop, dann Drift nach unten). Signal B: Delisting-Ankündigung → Rendite bis Handelsende.
- Kill: Netto (160 bp Roundtrip Spot, Slippage dünner Paare) ≤ 0 oder Median negativ trotz positivem Mittel (Ausreißer wie XTZ/LINK/OMG >50 % bei Coinbase verzerren).
- Ereignisse: σ ca. 15 bis 20 %, δ netto ca. 3,4 % (7 % minus 160 bp minus Slippage): n ≈ 150 bis 270. Kraken-Listings pro Jahr [nicht gefunden]; nur Spot-Long handelbar, Fade nicht (Short nicht verfügbar) → ein zweiter Schwachpunkt.

**4. Overnight-Momentum.** Mechanismus: Institutionen handeln intraday/Close, Privatanleger zum Open; Rückwärts-Persistenz über Jahre (Lou et al.). Test ist billig, weil alles in unseren Tageskerzen liegt. **Warnung:** survivorship-behaftete 495-Titel-Daten verzerren Reversal-/Persistenzsignale; in Large Caps ist der Effekt vermutlich klein. Signal: Monatsende Top-Dezil Overnight-Rendite des Vormonats → nur Overnight halten (MOC kaufen, MOO verkaufen [Annahme: IBKR erlaubt]). Kill: Netto je Nacht < 0 nach 5 bp; Ereignisse reichlich (Panel), Power kein Problem.

**5. Opex-Pinning.** Hedge-Rebalancing der Marktmacher zieht Kurse zum Strike. Ohne Open Interest nur Proxy (Abstand zum nächsten 5-USD-Strike). Signal: Opex-Donnerstag-Schluss, Abstand zum Strike > x bp → Position Richtung Strike, Ausstieg Freitag-Schluss. Kill: Netto < 0 nach 4 bp Kosten oder Pinning-Test (|Schluss − Strike| kleiner als an Nicht-Opex-Freitagen) nicht signifikant. Power: 250 Opex-Termine in 20 Jahren, cluster-korrigiert nach Datum; reicht für ca. 10 bp Effekt kaum.

**6./7. Russell, Spin-offs.** Beide plausibel (Zwangsverkäufe, Mandate) und kapazitätsbegrenzt, aber ohne Datenkauf bzw. EDGAR-Parsing nicht testbar; daher hinten. S&P-500-Index-Effekt selbst ist **tot**: Aufnahme 7,6 % (1990er) → 0,8 % (2010 bis 2020, statistisch nicht von Null verschieden), Abgänge -16,6 % → -0,6 % (Greenwood/Sammon, NBER w30748, J. Finance 2025).

**8. Maker-Quoting.** Nur der Vollständigkeit halber: ohne Queue-Simulation und mit 2 Wochen Daten wäre jede Aussage Wunschdenken.

## Verworfen (kurz)
- Cross-Exchange-Arbitrage: Lücken sind laut Makarov/Schoar (JFE 2020) vor allem **zwischen Ländern** wegen Kapitalverkehrskontrollen; innerhalb US/EU klein, und 80 bis 160 bp Kraken-Gebühren schlucken sie.
- Jahresend-Steuerverkäufe/Januar-Effekt: seit 2000 "klein oder nicht vorhanden" (NC State MBA, 2024). Unsere Aktiendaten haben zusätzlich Survivorship-Bias, der genau Verlierer-Rebounds künstlich aufbläst.
- Ex-Dividende/Dividend Capture: keine Dividendendaten, Quellensteuer/Abgeltungsteuer [Annahme] machen es für uns unattraktiv.

## Die 3 Ideen, die ich zuerst testen würde
1. **Funding-Carry (#1)**: rein arithmetisch, geringste Datenanforderung, strukturell (nicht richtungsabhängig). Zuerst prüfen, ob die Funding-Historie extern verfügbar ist und ob Kraken Futures für uns zulässig ist.
2. **Token-Unlock (#2)**: Kraken-OHLCVT enthält Altcoins inklusive später delisteter Paare (muss geprüft werden), also weniger Survivorship als bei Aktien. Gematchte Kontrolle ist Pflicht.
3. **Kraken-Listing/Delisting Signal A/B (#3)**: Handelsstart steckt in unseren eigenen Daten, Ankündigungsscraping optional. Gleiche Datenquelle für mehrere Hypothesen.

Overnight-Momentum (#4) wäre mein günstigstes "Nebenbei"-Experiment, aber mit schlechter Erfolgsaussicht; die Familie wächst mit jeder Hypothese (BH-FDR), also nur bei freier Kapazität.

## Die verrückte Idee: Wick-Catcher im Zwangsverkauf
Kraken verkauft Restbestände delisteter Token zwangsweise, mit Warnung, dass bei dünner Liquidität "die Erlöse null sein können" (Titel eines Artikels bei Digital Today; Text nicht gelesen). Ein Zwangsverkäufer mit Gewalt gegen dünne Orderbücher produziert Wicks nach unten. Idee: kleine Limit-Käufe (z. B. 100 USD) weit unter Markt bei delisteten Paaren am Umwandlungsdatum, Ausstieg per Withdrawal auf eine andere Börse.
- Test mit vorhandenen Daten: Für jedes delistete Paar in OHLCVT das Verhältnis Tief/Schluss der letzten 1m-Kerzen vor Handelsende. Wie oft und wie tief gibt es einen Wick, und mit welchem Volumen? Das ist **reines Beobachten ohne Geld**.
- Kill: Median-Wick < 15 % oder Volumen im Wick zu klein, um 100 USD zu füllen; oder die Paare sind nicht in OHLCVT enthalten.
- Risiko: Token geht auf null, Withdrawal gesperrt, Steuer-/Compliance-Aufwand. Kapazität winzig, deshalb für Fonds uninteressant. Ereignisse: ca. 20 Token pro Delisting-Welle (BeInCrypto, Titel); 10 bis 30 Fälle reichen nur für eine deskriptive Aussage, nicht für Signifikanz.

## Quellen
- Greenwood/Sammon, "The Disappearing Index Effect", NBER w30748 (2023): https://www.nber.org/system/files/working_papers/w30748/w30748.pdf
- Schmeling/Schrimpf/Todorov, "Crypto carry", BIS WP 1087 (2023): https://www.bis.org/publ/work1087.pdf
- Lou/Polk/Skouras, "A tug of war: overnight versus intraday expected returns", JFE (2019): https://personal.lse.ac.uk/polk/research/TugOfWar.pdf
- Makarov/Schoar, "Trading and arbitrage in cryptocurrency markets", JFE (2020): https://eprints.lse.ac.uk/100409
- Keyrock Token-Unlock-Studie (via BeInCrypto, 06.12.2024): https://beincrypto.com/keyrock-research-token-unlocks/
- Ante, Market Reaction to Exchange Listings of Cryptocurrencies (Blockchain Research Lab): https://www.blockchainresearchlab.org/de/2019/09/10/market-reaction-to-exchange-listings-of-cryptocurrencies-2/
- Coin Metrics zu Coinbase-Listings (2020): https://cointelegraph.com/news/coinmetrics-finds-the-coinbase-effect-is-actually-pretty-lame
- Kraken SHIB-Listing (ForkLog, 29.11.2021): https://forklog.com/en/shiba-inu-price-climbs-25-after-kraken-listing-announcement/amp
- Monero/Kraken EEA-Delisting (iTiger, 02.10.2024): https://www.itiger.com/news/2472528551
- Ni/Pearson/Poteshman, "Stock price clustering on option expiration dates" (Abstract): https://scholars.hkbu.edu.hk/en/publications/stock-price-clustering-on-option-expiration-dates-3/
- Chen/Noronha/Singal, Russell reconstitution effect, FAJ 2003 (Abstract): https://rpc.cfainstitute.org/en/research/financial-analysts-journal/2003/the-russell-reconstitution-effect
- Veld/Veld-Merkoulova, Europäische Spin-offs (2002): https://storre.stir.ac.uk/bitstream/1893/451/1/Spinoff-jbf.pdf
- Kraken-Gebühren: Datawallet https://www.datawallet.com/crypto/kraken-fees-explained ; Kraken Futures Doku (veralteter Endpunkt) https://docs.kraken.com/api-reference/fee-schedules/get-fee-schedules.md
- Januar-Effekt (NC State MBA, 2024): https://mba.ncsu.edu/2024/12/17/does-the-stock-market-feel-the-holiday-spirit
- Digital Today zu Kraken-Zwangsverkauf (nur Titel gesehen): https://www.digitaltoday.co.kr/en/view/88951/kraken-starts-forced-sale-of-7-delisted-tokens-warns-proceeds-could-be-zero-if-liquidity-thin
