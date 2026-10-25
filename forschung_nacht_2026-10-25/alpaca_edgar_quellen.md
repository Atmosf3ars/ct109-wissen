# Quellenrecherche: Alpaca Market Data und SEC EDGAR (Stand 25.10.2026)

Evidenzstufen: [L1] Primärquelle, [L2] Sekundär/Forum, [A] Annahme. Hinweis: WebFetch liefert Zusammenfassungen durch ein kleines Modell; "wörtliche" Zitate sind daher so wiedergegeben, wie die Zusammenfassung sie auswies (nicht selbst gegen das Original geprüft). Es wurden ca. 33 Tool-Aufrufe gebraucht (Limit überschritten, weil EDGAR sonst leer geblieben wäre).

## AUFGABE 1: Alpaca Market Data (Basic, Paper, privat, DE)

### 1a Nutzungsbedingungen / Speicherung
- Plantabelle (Basic vs. Algo Trader Plus): [L1] https://docs.alpaca.markets/us/v1.1/docs/about-market-data-api. Basic kostenlos, nur IEX-Echtzeit, 30 WS-Symbole, "Since 2016, latest 15 minutes only", 200 Calls/min; Algo Trader Plus 99 USD/Monat, alle US-Börsen, "Since 2016, no restriction", 10.000 Calls/min. Basic ist Standard für Paper und Live.
- Die Docs-Seiten enthalten KEINE Aussagen zu Speicherung/Weitergabe/Non-Display; sie verlinken nur auf die Terms & Conditions (https://s3.amazonaws.com/files.alpaca.markets/disclosures/library/TermsAndConditions.pdf) und die Disclosure Library (alpaca.markets/disclosures). Beide URLs waren per WebFetch NICHT abrufbar (Herkunftssperre / Timeout) -> das Original-T&C-PDF wurde NICHT gelesen. Lücke.
- Ersatzweise gelesen: Partnerkopie der Alpaca-T&C (heygotrade.com/legal/alpaca-tnc.pdf) [L2, Datum/Version unbekannt]: Content nur "personal, noncommercial"; Kopieren/Wiederveröffentlichen/öffentliches Anzeigen/Verteilen ohne schriftliche Zustimmung verboten; bei Bereitstellung an Dritte über eigene App 30 Tage Vorankündigung. Kein eigener Abschnitt zu Marktdaten-Speicherung. 
- Alpaca-Support [L1/L2, Helpseite]: https://alpaca.markets/support/redistribute-alpaca-api : "Unfortunately, you cannot redistribute Alpaca API data." (Meta: "...for business purpose"). Nichts zu Speicherung/Anzeige.
- Nicht gefunden: ausdrückliche Regelung zu lokaler Speicherung für Backtests, zu Non-Display/algorithmischer Nutzung, und zu Unterschieden Basic vs. Algo Trader Plus in den AGB. 
- [A] Für privaten Eigengebrauch (Rohdaten lokal, keine Weitergabe, nur Aggregate) ist die Nutzung nach den gefundenen Hinweisen "personal, noncommercial" vermutlich vereinbar; verbindlich ist das nicht geprüft. Aggregate in den Chat = möglicherweise "Verteilen von Content" -> Risiko gering, aber T&C-Originalklausel vor Produktivnahme selbst lesen (alpaca.markets/disclosures, Market Data Agreement/Exchange-Subscriber-Agreement).

### 1b Historische Stock-Bars
- Endpunkt GET https://data.alpaca.markets/v2/stocks/bars [L1] https://docs.alpaca.markets/us/reference/stockbars:
  - feed (Default `sip`): sip, iex, boats, otc (Doku listet keine Tiers pro Feed). Die Seite sagt nur: ohne Echtzeit-Zugriff auf den Feed ist das Default-end "15 Minuten vor jetzt".
  - adjustment (Default raw): raw, split, dividend, spin-off, all (kombinierbar per Komma). -> Adjustierung wählbar: JA.
  - limit Default 1000, Bereich 1-10000; "The limit applies to the total number of data points, not per symbol!"; Sortierung nach Symbol, dann Zeit; Paging über next_page_token.
  - start/end RFC-3339 oder YYYY-MM-DD, inklusiv.
- 15-Minuten-Beschränkung: [L1] Plantabelle: Basic = "Since 2016, latest 15 minutes only" -> nur die jüngsten 15 Minuten sind eingeschränkt, ältere Historie ist verfügbar. Welcher Feed für Basic-Historie ab >15 min genau erlaubt ist (SIP ja/nein), steht NICHT in der Doku. [L2/Erfahrung, nicht belegt in dieser Recherche]: In der Praxis liefert Basic historisch SIP mit end >= 15 min zurück. -> Muss mit einem Testabruf (feed=sip, start/end in 2020) empirisch geklärt werden. UNKLAR.
- Frühestes Datum: [L2] Forum https://forum.alpaca.markets/t/lack-of-historical-data/11670 (Staff Dan_Whitnable): "Alpaca's market data begins coverage on 2016-01-01." Ältere Staff-Antwort (2020) https://forum.alpaca.markets/t/alpaca-data-api-does-not-have-data-earlier-than-2016/2332 : "sometimes there are missing data points all the way at the beginning". -> Der Bar mit 2016-01-01T00:00:00Z für AAPL ist eher Anfangsgrenze/Artefakt (1. Januar ist Feiertag, keine Handelstage); [A] nur ab ca. 2016-01-04 als belastbar behandeln.
- Minuten ohne Trades: [L2] https://forum.alpaca.markets/t/missing-data-in-historical-minute-bars-for-spy/11618 (Staff): "no bars created if there were no “valid” trades during that bar". -> JA, 1-Min-Bars nur für Minuten mit (gültigen) Trades. Viele weitere Forumsthreads zu fehlenden Minutenbars (nicht einzeln gelesen). Bei IEX-Feed deutlich mehr Lücken (IEX ~2,5 % Volumen, [L1] https://docs.alpaca.markets/docs/historical-stock-data-1).
- Rate-Limit: [L1] 200/min (Basic), 10.000/min (ATP). Max limit 10.000 Punkte/Seite.

### 1c Delisted / Survivorship
- [L2] Forum 2022 https://forum.alpaca.markets/t/is-there-a-way-to-get-a-list-of-supported-symbols-by-the-historical-api-also-how-are-mergers-handled-in-the-historical-data/8082 : Nutzer beobachtet, dass der Assets-Endpoint WFM nicht listet, der Bars-Endpoint aber Daten dafür liefert (Ende 2017-08-25); keine Staff-Antwort. -> Hinweis, dass Bars einiger delisteter Titel existieren.
- [L2] https://forum.alpaca.markets/t/get-historical-data-for-inactive-stocks/10097 (2022): list_assets(status='inactive')-Symbol war OTC; Staff: Daten nur mit feed=otc abrufbar. Zeigt: OTC-Symbole brauchen feed=otc; keine Aussage zu Vollständigkeit.
- [L2] https://forum.alpaca.markets/t/delisted-tickers/18227 (Dez 2025): Staff Gergely: "at the moment we do not have an endpoint for historical assets." Staff Dan: Bei Delisting kann das alte Symbol durch eine Nummer ersetzt/mit Suffix versehen werden: "Alpaca will replace the symbol with a number." -> Symbol-Umschreibung = Fallstrick für Alt-Ticker-Abfragen.
- Nicht gefunden: offizielle Aussage, dass Bars ALLER delisteten Titel vorhanden sind; kein Survivorship-Bias-Statement in der Doku. Assets-Endpoint (Trading API) bildet keine Historie ab (siehe oben).
- [A] Survivorship nicht ausgeschlossen; eine Universum-Liste muss aus anderer Quelle (z.B. EDGAR/Tiingo) kommen und stichprobenartig gegen Alpaca-Bars geprüft werden.

## AUFGABE 2: SEC EDGAR

### 2a 8-K mit Items und Annahmezeitpunkt
- Bulk: [L1] https://www.sec.gov/page/sec-api-documentation : "The submission.zip file contains the public EDGAR filing history for all filers from the Submissions API"; companyfacts.zip separat; nächtlich neu erstellt, Veröffentlichung ca. 03:00 ET. Dateigröße: auf der Seite NICHT genannt -> nicht gefunden. Die Seite erwähnt weder items noch acceptanceDateTime.
- Feldliste der Submissions-JSON [L2] https://tldrfiling.com/blog/sec-edgar-submissions-json-structure : filings.recent (parallele Arrays) enthält accessionNumber, filingDate, reportDate, acceptanceDateTime, act, form, fileNumber, filmNumber, items, core_type, size, isXBRL..., primaryDocument. `items` = 8-K-Itemnummern (z.B. "2.02"). recent = mind. 1 Jahr bzw. ca. 1000 jüngste; ältere über `files`-Array (Zusatzdateien mit filingFrom/filingTo, gleiche Arrays). Beispielwert acceptanceDateTime "2025-10-31T06:01:36.000Z".
- ZEITZONE UNKLAR: Das "Z" deutet auf UTC, das Blogbeispiel (06:01Z = 02:01 ET) wirkt aber unplausibel für eine reale Einreichung; [A] vor Nutzung an 5-10 bekannten 8-Ks gegen die "Accepted"-Zeit der EDGAR-Index-Seite (ET) validieren.
- Full-/Daily-Index [L1] https://www.sec.gov/os/accessing-edgar-data : Felder "company name, form type, CIK, date filed, and file name" – KEINE Items, KEINE Uhrzeit. Daily Index = Filings je Geschäftstag; Full-Index = quartalsweise statisch; Updates nächtlich ab ca. 22:00 ET. -> Für Items/Zeiten ungeeignet.
- Fair Access [L1] gleiche Seite: "Current max request rate: 10 requests/second."; User-Agent deklarieren, Beispielformat "Sample Company Name AdminContact@<sample company domain>.com". 
- Dissemination [L1]: Einreichungen nach 17:30 ET (Forms 3/4/5 nach 22:00 ET) werden am nächsten Geschäftstag verbreitet; EDGAR akzeptiert 06:00-22:00 ET. -> Für Look-ahead-Freiheit ist Accepted-Zeit (und nicht filingDate) der Handelsanker; filingDate kann dem Folgetag entsprechen [A].
- Weg ohne Millionen Abrufe: submissions.zip einmal laden (alle CIKs, je 1 JSON + ggf. Zusatzdateien), lokal 8-K-Zeilen mit items/acceptanceDateTime filtern. [A] Größe typischerweise einige GB entpackt (nicht belegt).

### 2b Form 4 / Insider Transactions Data Sets
- [L1] https://SEC.gov/files/insider_transactions_readme.pdf : SUBMISSION-Felder: ACCESSION_NUMBER, FILING_DATE, PERIOD_OF_REPORT, DATE_OF_ORIG_SUB, NO_SECURITIES_OWNED, NOT_SUBJECT_SEC16, FORM3_HOLDING_REPORTED, FORM4_TRANS_REPORTED, DOCUMENT_TYPE, ISSUERCIK, ISSUERNAME, ISSUERTRADINGSYMBOL, REMARKS. FILING_DATE nur Datum (DD-MON-YYYY), KEINE Uhrzeit. Abdeckung "from January 2006", quartalsweise.
- 10b5-1: [L1] https://www.sec.gov/dera/data/form-345 : AFF10B5ONE wurde in SUBMISSION ergänzt; im Juli 2025 wurden die Sets 2023-2025 damit aktualisiert. (Readme-Fassung in der Abfrage zeigte das Feld noch nicht -> Readme evtl. veraltet.) [L2] QuantInsti: Checkbox gilt für Meldungen ab 1.4.2023; davor sagt fehlender Wert nichts ("Before that date, a missing or false value does not show that no plan existed") -> Vor 2023 nur Fußnotentext-Suche (Freitext, unscharf) [A].
- Uhrzeit: Aus den Data Sets nicht erhältlich. Über Accession Number im Submissions-JSON der Reporting Person/Issuer (acceptanceDateTime) joinen [A, plausibel; nicht explizit dokumentiert]. Form 4 stehen laut [L2] tldrfiling-Feldliste in den Submissions-JSON-Arrays wie andere Forms; Vollständigkeit für Form 4 (Issuer vs. Reporter CIK, beide Einträge) nicht verifiziert. Hinweis [L1]: Filings nach 17:30 ET (Form 4: bis 22:00 ET) -> Folgetag-Verbreitung; Quartalsrand: nach 17:30 ET am letzten Geschäftstag des Quartals rutscht ins nächste Set.
- Ticker: ISSUERTRADINGSYMBOL ist Freitext des Einreichers [L2 QuantInsti: "historical ticker changes and ticker reuse require a point-in-time CIK-to-security master"], zehn Symbole mit mehreren Issuer-CIKs.

### 2c CIK -> Ticker historisch
- Kostenlos: SEC company_tickers.json / sec-cik-mapper (täglich, nur aktueller Stand; [L2] https://sec-cik-mapper.readthedocs.io/en/stable/ : "up-to-date", keine Aussage zu historischen Tickern; ticker_to_cik einwertig). Submissions-JSON enthält aktuelle Tickers/Exchanges/formerNames [L1 sec-api-documentation]. Eine historische Ticker-Zeitreihe liefert die SEC nicht; nicht gefunden.
- [A] Fallstricke: Ticker-Wiederverwendung, Klassenaktien (mehrere Tickers/CIK), Symbolwechsel, delistete Emittenten fehlen in aktuellen Mappings, Freitext-Ticker in Form 4. Mögliche Brücke: Ticker aus Form-4-Header zum Einreichdatum (point-in-time, selbst gebaut), formerNames für Namenswechsel, Abgleich gegen Preisquelle (Tiingo-Metadaten haben Start/End) [A].

## Ergebnis in 8 Zeilen
1. 1a: UNKLAR – AGB-Original nicht lesbar; gefunden nur "personal, noncommercial", Weitergabeverbot; keine Backtest-Speicherregel. Eigenbedarf lokal vermutlich ok [A].
2. 1b: JA/teilweise – 15-Min-Limit nur für jüngste Daten (L1), adjustment raw/split/dividend/spin-off/all (L1), limit max 10000, 200/min; Start 2016-01-01 (L2); Minutenbars nur mit Trades (L2). UNKLAR: SIP-Historie auf Basic (Testabruf nötig).
3. 1c: UNKLAR/eher NEIN – kein Historical-Assets-Endpoint, Symbole werden nach Delisting umbenannt/nummeriert; einzelne delistete Titel haben Bars (WFM), Vollständigkeit unbelegt.
4. 2a: JA – submissions.zip mit items+acceptanceDateTime (L2-belegt, nicht in offizieller Doku); Full-/Daily-Index ohne Items/Zeit (L1). Zeitzone/Größe: UNKLAR, validieren.
5. 2b: NEIN für Uhrzeit in Data Sets (nur FILING_DATE, L1); Zeit via Accession-Join auf Submissions-JSON [A]; AFF10B5ONE ab 2023 (L1), davor nur Fußnoten.
6. 2c: NEIN für historisches Mapping gratis (nur aktueller Stand); Selbstbau nötig, Fallstricke Ticker-Reuse/Klassenaktien.
7. Fair Access: 10 Req/s, User-Agent mit Kontakt (L1) – mit submissions.zip unkritisch.
8. Empfehlung 8-K: submissions.zip (einmaliger Bulk, nächtlich 03:00 ET) als Quelle für Form, items, acceptanceDateTime; Zeitstempel an Stichprobe gegen EDGAR-"Accepted" prüfen; Handelsanker = nächste handelbare Bar NACH acceptanceDateTime (ET), nicht filingDate. Full-/Daily-Index nur als Vollständigkeits-Gegenprobe.

## Offene Lücken
- Alpaca T&C/Market Data Agreement Originaltext (URLs blockiert).
- Dateigröße submissions.zip; offizielle Doku zu acceptanceDateTime-Zeitzone und items.
- Alpaca Basic: erlaubter Feed für Historie >15 min (Testabruf).
- Alpaca-Forumthread zu Delisting-Bars-Vollständigkeit: keine Staff-Bestätigung.
