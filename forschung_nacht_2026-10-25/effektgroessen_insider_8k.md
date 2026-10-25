# Effektgrößen: Insider-Käufe (Form 4), 8-K-Items/Nachrichtenreaktion, Intraday-Sympathie

Stand 25.10.2026. Reine Web-Recherche (ca. 26 Tool-Aufrufe), keine Rohdaten. Zahlen stammen aus Abstracts/Zusammenfassungen, die per WebFetch gelesen wurden. Volltext-Tabellen habe ich meist NICHT gesehen; die Tabellenwerte kommen dann aus der Fetch-Zusammenfassung und gelten als [L1-sekundär gelesen]. Evidenz: [L1] Primärquelle gelesen (Abstract/Zusammenfassung), [L2] Sekundärquelle, [A] Annahme/eigene Rechnung. Netto/Brutto ist angegeben; wo nichts steht, ist es BRUTTO (fast alle Papers rechnen ohne Kosten).

## Generelle Einordnung (Zerfall)

- [L1] McLean/Pontiff (2016, J. Finance; 97 Anomalien): Prädiktor-Renditen sind out-of-sample 26 % niedriger, nach Publikation 58 % niedriger. Stärkerer Zerfall bei höherer In-Sample-Rendite. Quelle: https://academicnewsletter.sufe.edu.cn/info/359722 (Abstract; Stichprobenzeitraum dort nicht genannt). Als Prior für alle Kandidaten unten: Publikationsstichproben-Effekt mal ca. 0,4 [A].
- Auch Martineau (unten) und Curme et al. (unten) zeigen unabhängig: Large-Cap-Kanten sind nach 2005/2010 deutlich kleiner.

## Thema A: Insider-Käufe (Form 4, Code P)

**Cohen/Malloy/Pomorski (2012, J. Finance), "Decoding Inside Information"** [L1, Zusammenfassung von NBER-PDF w16454 gelesen]
- Daten: Thomson-Reuters-Insiderdatenbank, 01/1986–12/2007, CRSP/Compustat, alle US-Aktien. Routine = gleicher Kalendermonat in 3 Vorjahren in Folge; Rest opportunistisch. Opportunistisch sind nur 35,6 % der Käufe (48 % der Verkäufe).
- Carhart-4-Faktor-Alpha pro Monat, Kalenderzeit, BRUTTO: opportunistische Käufe equal-weight 1,45 %, value-weight 0,52 %; Routine-Käufe EW 0,82 %, VW 0,09 %. Die VW-Alphas sind überwiegend nicht signifikant.
- Long-Short opportunistisch Kauf minus Verkauf: VW 82 bp/Monat (t = 2,15), EW 180 bp/Monat (t = 6,07). Routine VW ca. -20 bp (t = -0,57).
- Horizont: Event-Zeit über 12 Monate, Anstieg ca. 6 Monate, keine Umkehr; Spread opportunistisch minus Routine ca. 4 % (VW) bis 8 % (EW) [L1-sekundär].
- Größe: Obere vs. untere Marktkapitalisierungshälfte; opportunistische Käufe/Verkäufe sagen in beiden Gruppen Renditen voraus, Routine nicht (Tabelle IX nicht lesbar, Koeffizienten LÜCKE).
- Wichtig für uns: Das Paper rechnet NICHT ab Einreichungsdatum. Median-Meldeverzug 3 Tage; Anhang A4 nutzt Rendite ab dem 11. Tag des Folgemonats (Ergebnisse "virtually identical"). Es sagt also nichts über 1/5/21-Tage-Renditen ab Filing. LÜCKE: kein Paper gefunden, das 1/5/21-Tage-CARs ab Filing für S&P 500/Russell 1000 getrennt ausweist.

**Lakonishok/Lee (2001, RFS)** [L1, Abstract]: NYSE/AMEX/Nasdaq 1975–1995. Prädiktionskraft kommt "mainly from smaller firms"; Verkäufe ohne Information. Strong-Buy minus Strong-Sell ca. 4,8 % im ersten Jahr, größen-/B/M-bereinigt [L2 via https://www.insidermonkey.com/blog/the-insider-trading-anomaly-recent-academic-studies-591/]. Das Large-Cap-Signal ist "much weaker" [L2 via IBKR Campus, https://www.interactivebrokers.com/campus/?p=256270], ohne Zahl.

**Jeng/Metrick/Zeckhauser (2003)** [L2]: 1975–1996, Rendite ab Transaktionsdatum: ca. 37–52 bp/Monat Carhart-Alpha für Käufe (0,52 %/Monat = 6,4 %/Jahr; Quelle Insider Monkey/IBKR). Ca. 1/6 der abnormalen Rendite innerhalb 5 Tage, 1/3 innerhalb 1 Monat, 3/4 innerhalb 6 Monate. Kein signifikanter Größenunterschied bei ihnen (widerspricht Lakonishok/Lee).

**Cluster:**
- Alldredge/Blank (2019, J. Financial Research 42(2)): [L1 Abstract] Cluster-Käufe mit ">2 % abnormaler Rendite im Folgemonat". [L2 via IBKR Campus]: 1986–2014, 8.789 Firmen; Kauf innerhalb 2 Tagen nach einem anderen Insider-Kauf: ca. 2,1 % im Folgemonat, ca. 0,9 Prozentpunkte mehr als Einzelkäufe; 23 % der Käufe am selben Tag wie ein anderer Kauf. Universum nicht nach Größe getrennt (LÜCKE), brutto, Messung ab Cluster-Ereignis nicht ab Filing geprüft.
- Kang/Kim/Wang (WP, 1986–2016): ca. 40 % der Transaktionen sind Cluster; Zahlen nicht extrahierbar [L2].
- Mikro-Cap-Studie (arXiv 2602.06198, Datensatz 2018–2024, Marktkapitalisierung 30–500 Mio. USD, 13.534 Kauf-Zeilen) [L1, nicht peer-reviewed, Qualität unklar]: mittlere CAR[1,30] 3,6 % (Median 1,3 %), CAR[1,20] 3,2 %; Cluster-Käufe (anderer Insider-Kauf in 30 Tagen zuvor) 4,4 % vs. 2,7 %; opportunistisch 2,6 % vs. Routine -1,8 %. Der Großteil fällt am ersten Ereignistag an (Alpha 2,10 %/Monat; ohne Tag 1 nur 0,68 %/Monat, t = 1,78). Nach 3 % Round-Trip-Kosten (Mikro-Caps) bleiben im Test-Jahr 2024 ca. 2,2 % mit Konfidenzintervall um Null. Eine Large-Cap-Erweiterung "fails every matched-comparison gate". Das ist kein Large-Cap-Beleg, eher ein Gegenbeleg; nur die Struktur (Tag-1-Konzentration) ist relevant.

**CEO/CFO:** Wang/Shin/Francis (2011 WP), 1992–07/2002, 12.936 CEO- und 7.049 CFO-Käufe [L2 via https://www.cxoadvisory.com/investing-expertise/cfos-vs-ceos-as-inside-traders/]: 12-Monats-CAR nach Meldung CFO 6,19 %, CEO 1,57 % (brutto). Der CFO-Vorteil liegt in kleinen/mittleren Firmen und fehlt im obersten Marktkapitalisierungs-Quartil. Quartilsbezug schlägt bei uns direkt auf Large Caps durch: kein CFO-Vorteil.

**Zerfall nach 2010:** KEIN direkter Beleg gefunden (kein Paper mit Subperioden 2010/2015/2020 für Large Caps). Alldredge/Blank (bis 2014) und Kang et al. (bis 2016) laufen über 2010 hinaus, Zerfall dort nicht ausgewiesen. [A] Erwartung: Wegen McLean/Pontiff und Tag-1-Konzentration ist die von uns handelbare Kante (Einstieg nach Filing, nicht Tag 0) klein.

**Häufigkeit im S&P 500:** LÜCKE, nichts Belastbares gefunden. [A] Open-Market-Käufe (P) sind in Large Caps selten (Insider verkaufen überwiegend); Cluster-Käufe im S&P 500 vermutlich nur wenige Dutzend pro Jahr, in Stressphasen (2020, 2022) gehäuft, was die Zahl unabhängiger Episoden weiter drückt. Muss mit eigenen EDGAR-Daten gezählt werden (Phase 0).

**Fallstricke:** (1) Meldefrist 2 Geschäftstage (seit 2002, SOX); Median-Verzug in älteren Daten 3 Tage [L1-sekundär]. Handelbar ist erst die Filing-Zeit (acceptance datetime, nicht Datum). (2) 10b5-1-Pläne: Käufe sind selten Plan-Käufe; Verkäufe überwiegen. Seit 2023 Checkbox/Offenlegungspflicht im Form 4 (Rule-Änderung SEC 2022) [A, nicht verifiziert]. (3) Code P exakt filtern (keine Optionsausübung, keine Geschenke), Routine-Klassifikation braucht 3 Jahre Historie (Cohen et al.), also Vorlauf-Daten. (4) Reaktion konzentriert sich auf Tag 0/1 [L1 Mikro-Cap-Paper]. (5) Cluster nicht doppelt zählen: unabhängige Episoden je Firma und Zeitfenster. (6) Marktphasen-Clustering: Käufe häufen sich nach Drawdowns, also Marktfaktor-Exposition (Kontrollgruppe nötig).

## Thema B: 8-K-Items und Nachrichten

**Lerman/Livnat, "The New Form 8-K Disclosures" (RAST 2010; WP 04/2008)** [L1, Tabelle 3 aus Fetch gelesen]. 8-K-Daten 2005–2006, ca. 127.273 Beobachtungen, alle Firmen (kein Large-Cap-Filter), abnormale BHAR gegen Size/BM-Portfolios, BRUTTO. "FD" = 3-Tage-Fenster um das Filing-Datum; Drift 30/60/90 Kalendertage nach Filing:
| Item | FD 3-Tage | Drift 30/60/90 d |
|---|---|---|
| 1.01 Vereinbarung | +0,41 % | +0,01/+0,10/+0,22 % |
| 2.01 Erwerb/Veräußerung | +0,44 % | n. s. |
| 2.02 Ergebnisse | -0,24 % | +0,18/+0,19/+0,29 % |
| 5.02 Direktoren/Führung | -0,11 % | -0,28/-0,36/-0,45 % |
| 2.05 Restrukturierung | -1,08 % | -1,11/-0,97/-1,14 % |
| 2.06 Wertminderung | -1,65 % | -1,23/-1,62/-1,95 % |
| 5.01 Kontrollwechsel | +0,40 % | -2,06/-3,69/-3,44 % |
Anteile: 1.01 ca. 28 %, 2.02 ca. 30 %, 5.02 ca. 12 % der Filings. Vorzeichen-Mittelwerte sind klein; Volumen und Volatilität steigen bei jedem Item signifikant ("signed returns understate information"). Wichtig: Item 5.02 ist gemischt (Rücktritt vs. Berufung; Vorzeichen nur per Textklassifikation lösbar, dies wurde im Paper nicht gemacht). Wer 5.02 nach Richtung (CEO-Abgang plötzlich/unfreiwillig) trennt, hat eventuell größere Effekte; Beleg LÜCKE (kein Paper gelesen; die Suche lieferte nur Titel wie Israelsen 2018 und Reaction to CEO turnover, ungelesen). Zeitraum 2005–2006 liegt vor dem Zerfall und vor starker Algo-Dominanz.

**PEAD / Item 2.02:** Martineau (2022, Critical Finance Review 11(3-4), "Rest in Peace PEAD") [L1 Abstract, https://ideas.repec.org/p/osf/socarx/z7k3p.html]: Für große Aktien ist PEAD "non-existent since 2006", Mikro-Caps erst zuletzt verschwunden; Preise reflektieren Überraschungen am Ankündigungstag. [L2 UCLA-Review, https://anderson-review.ucla.edu/is-post-earnings-announcement-drift-a-thing-again/]: Drift in Nicht-Mikro-Caps ab 2001 rückläufig, Subrahmanyam-Replikation 2001–2024 t = 2,18 (alle) vs. 1,43 ohne Mikro-Caps (untere 20 % NYSE) – nicht signifikant. Fazit: PEAD in Large Caps nach 2010 tot, Item 2.02 als Drift-Signal nicht verwenden. Intraday: Preisanpassung in Sekunden/Minuten [L2: arXiv 2601.08962 "Warp speed price moves: Jumps after earnings announcements", nur Titel gesehen, LÜCKE]. Dzielinski (2011) [L2 via CXO Advisory, 4.750 US-Aktien, 2003–2010]: Fortsetzung der Nachrichten-Tonalität für bis zu 2 Tage, dann teilweise Umkehr; bei Ergebnismeldungen Drift in Richtung des Ankündigungstags für ca. 2 Wochen ohne Umkehr (Größe nicht berichtet).

**Kursreaktion ohne Nachrichten:**
- Chan (2003, JFE 70, 223–260) [L1 Abstract]: Aktien mit negativen Schlagzeilen driften über Folgemonate weiter ab; Aktien mit extremen Kursbewegungen ohne öffentliche Nachrichten kehren teilweise um; Effekte bleiben nach Risikoadjustierung bestehen und konzentrieren sich auf kleinere, weniger liquide Aktien. Effektgrößen im Abstract nicht enthalten (LÜCKE; Volltext nicht zugänglich). Monatshorizont, nicht Tage.
- Boudoukh/Feldman/Kogan/Richardson (2013, NBER 18725; "Which News Moves Stock Prices?") [L1 Abstract]: Nach extremen Kursbewegungen: Umkehr an Tagen ohne identifizierte Nachricht, Fortsetzung an Tagen mit identifizierter Nachricht. Varianzverhältnis +120 % an Nachrichtentagen vs. +20 % bei nicht identifizierten. Keine bp-Angaben im Abstract (LÜCKE); Universum/Zeitraum nicht gelesen.
- Neuere Arbeiten zu Large-Cap-Intraday-Umkehr ohne Nachrichten: nicht gefunden (LÜCKE). [A] Unterscheidung News/No-News braucht saubere, zeitgestempelte Nachrichtenquelle (8-K-Zeitstempel + Presse); ohne sie ist die "Kein-News"-Klasse verunreinigt.

**Kosten bei Einzeltiteln [A]:** Large Cap liquide: Halb-Spread ca. 1–3 bp pro Seite plus Slippage ca. 2–5 bp, bei Position ca. 1.500 EUR dominiert die IBKR-Mindestprovision (ca. 1 USD je Seite, ca. 6–7 bp je Seite, ca. 12–14 bp Round-Trip). Round-Trip realistisch 15–25 bp Large Cap, 30–100 bp Small/Mid. Die Mikro-Cap-Studie nimmt 300 bp Round-Trip (anderes Universum). Eigene Kostenkalibrierung (D-Regel "Kosten richtungsfrei geeicht") ersetzt diese Schätzungen.

## Thema C: Intraday Lead-Lag/Sympathie

- Curme et al., "Emergence of statistically validated financial intraday lead-lag relationships" (arXiv 1401.0462; Autoren nicht auf der gelesenen Seite genannt, nach meiner Erinnerung Curme/Tumminello/Mantegna/Stanley/Kenett [A]) [L1]: 100 größte NYSE-Aktien, 2002–2003 und 2011–2012, Horizonte 5–130 min. Validierte Links wachsen stark unter 30 min; bei 130 min nur 1 (2011–12) bzw. 2 bei 65 min. 2002–2003 mehr Links als 2011–2012 ("increase in informational efficiency"). Effektgröße winzig: mittlere Lag-Korrelation 0,008 (5 min, 2002–03) bzw. -0,019 (130 min, 2011–12), Std. 0,02–0,03; gleichzeitige Korrelation 0,29–0,41. Tradability nicht getestet; Kosten/Leerverkauf werden als Hindernis genannt. Das spricht für Erosion nach 2010 und gegen Handelbarkeit im Fenster 15 min–3 h in Large Caps.
- Huth/Abergel "High Frequency Lead/lag Relationships – Empirical facts" (arXiv 1111.7103): nur Titel/Link aus Suche gesehen, nicht gelesen (LÜCKE).
- Thomas/Zhang (2006 WP, "Overreaction to Intra-Industry Information Transfers?") [L2 via https://www.cxoadvisory.com/animal-spirits/bet-against-big-sympathy-moves/]: 1973–2005, 245.742 Firma-Quartale. Sympathie-Bewegung nach Peer-Earnings (>= 5 Tage früher) kehrt sich zum eigenen Earnings-Termin um; Long/Short-Extremdezile ca. 1 % Excess-Return pro Quartal, brutto, vermutlich stärker bei Small Caps. Horizont Tage bis Wochen, nicht intraday. Passt zur "Rückfederung", aber nicht zum Fenster 15 min–3 h.
- Frankel/Godigbe/Rabier (2025, J. Accounting Research 63(1)) [L1 Abstract]: Ko-Bewegung mit Peers ist am Earnings-Tag des Leaders niedriger als an anderen Tagen; Zweifel an der Größe der Informations-Externalität. Schwächt die Sympathie-Hypothese für Earnings-Ereignisse.
- Spezifisch NVDA→AMD/INTC-Intraday, Rückfederung vs. Fortsetzung 15 min–3 h, Netto-Effektgröße: KEIN Beleg gefunden. Eintrag in Tabelle nur als [A].

## Tabelle

| Kandidat | erw. Netto-Kante je Ereignis (bp, Spanne) | Horizont | Quelle | Evidenz | Large-Cap-tauglich? | Zerfall |
|---|---|---|---|---|---|---|
| Insider-Kauf, opportunistisch/Cluster (Einstieg nach Filing) | 0 bis 30 bp [A]; Brutto-Literatur 52 bp/Monat VW-Alpha (1986–2007), Cluster ca. 210 bp/Monat (alle Größen) | 21 d (1 d, 5 d fast ohne Rest nach Tag 0/1) | Cohen et al. 2012; Alldredge/Blank 2019 | L1 (Brutto), Netto [A] | Schwach (Lakonishok/Lee; CFO-Effekt im Top-Quartil fehlt; VW-Alphas meist n. s.) | Nach 2010 nicht gemessen; Prior -58 % (McLean/Pontiff) und Tag-1-Konzentration |
| CEO/CFO-Käufe | 0 bis 20 bp [A] | 21 d | Wang et al. 2011 | L2 | Nein im Top-Quartil | Nicht gemessen |
| 8-K Item 2.02 (PEAD) | ca. 0 (Drift 18 bp/30 d in 2005–06, alle Firmen) | 1–30 d | Lerman/Livnat; Martineau 2022 | L1 | Nein (PEAD Large Cap seit ca. 2006 weg) | Vollständig |
| 8-K Item 5.02 (Führungswechsel) | -28 bp Drift/30 d (Short, ungerichtet, brutto); gerichtet (CEO-Abgang): unbekannt | 30–90 d | Lerman/Livnat 2005–06 | L1 | Unklar (Universum nicht getrennt) | Nicht gemessen |
| 8-K Items 1.01/2.01 | +41/+44 bp Filing-Fenster 3 d; Drift ca. 0 | 1–3 d | Lerman/Livnat | L1 | Unklar | Nicht gemessen; Reaktion am Filing-Tag, Einstieg danach vermutlich zu spät |
| 8-K Items 2.05/2.06 (Impairments/Restrukturierung) | -100 bis -190 bp (Short), selten | 30–90 d | Lerman/Livnat | L1 | Unklar | Nicht gemessen |
| No-News-Umkehr nach Extrembewegung | unbekannt (nur Richtung) | Tage–Monat | Chan 2003; Boudoukh et al. 2013 | L1 (qualitativ) | Eher klein-/illiquide konzentriert (Chan) | Nicht gemessen |
| Intraday Sympathie/Lead-Lag | ca. 0 [A] | 15 min–3 h | Curme et al.; Thomas/Zhang (Quartalshorizont) | L1 (Erosion) | Nein (Lag-Korr. ca. 0,01–0,02, Kosten > Kante) | Stark (2002/03 > 2011/12) |

## Nachweisgrenze (SE ≈ 25 bp bei σ ≈ 300 bp, n ≈ 150; MDE ≈ 90 bp)

Kein Kandidat hat nach Netto-Abzug eine erwartete Kante in der Nähe von 90 bp. Die einzigen Brutto-Zahlen über 90 bp sind (a) Insider-Cluster 210 bp/Monat (Alldredge/Blank, alle Größen, Brutto, Zerfall nicht gemessen) und (b) Short-Seiten bei seltenen negativen 8-K-Items (2.05/2.06/5.01: ca. 100–370 bp Drift), die in Large Caps selten sind (n klein) und shortbar sein müssen. Realistisch erwartbar bei Large Caps: Insider 0–30 bp, 8-K-Standarditems unter 40 bp; beides liegt bei n ≈ 150 unter der Auflösung. Damit sind diese Kandidaten nach Regel 2 voraussichtlich HINWEIS-Klasse. Gegen eine HINWEIS-Einstufung spricht höchstens: Insider-Cluster mit Zusatzfilter (Opportunistic, Erstkauf in 12 Monaten, tiefer Abstand vom 52-Wochen-Hoch; die Mikro-Cap-Studie nennt dafür 5,0 % vs. 2,7 %), allerdings in einem anderen Universum und ohne Large-Cap-Beleg. Wer die MDE senken will, braucht größere n (Russell 1000 statt S&P 500, 2010–2026 Vollzeitraum) oder geringere σ je Ereignis (Marktbereinigung, Sektor-Hedge, kürzeres Fenster); erst dann hilft die Rechnung. [A] SE = σ/√n: n = 600 bei gleichem σ gäbe SE = 12 bp und MDE ≈ 44 bp.

## Lücken (explizit)

Kein Beleg gefunden für: 1/5/21-Tage-CAR ab Filing für Large Caps; Insider-Zerfall nach 2010/2015/2020; Anzahl Cluster-Käufe im S&P 500; gerichtete 5.02-Effekte; bp-Größen von Chan 2003 und Boudoukh 2013; NVDA→AMD-artige Intraday-Sympathie; Netto-Zahlen außer der Mikro-Cap-Studie. Nächster Schritt wäre Volltext-Zugriff (SSRN/NBER PDFs) auf Cohen et al. Tabelle IX, Alldredge/Blank und Chan Tabellen, außerdem 10b5-1-Änderung 2023 prüfen.
