# CT109 – RUNDE-3C-SPEZIFIKATION v0.1 (ENTWURF INSIDER-ALL, NICHT GEHASHT)

**Status:** Entwurf des Einsatzleiters, Stand So 25.10.2026 (≈ 19:00 Berlin). Wird erst mit eigenem Freeze-Paket und GO-Satz **gültig**. Neuer, **eigener** Freeze (Register-Index 8), unabhängig vom Freeze `830bac6d…`. Evidenzstufen: [L1] Herstellerangabe, [L2] von Andi gemessen, [A] Annahme, [R] Recherche.

## 1 Gegenstand und Einordnung
**INSIDER-ALL:** Cluster von Insider-Käufen (Form 4, Code P) im **gesamten US-Universum** (nicht nur S&P 500). Long-Position, Haltedauer 28 Kalendertage, Zielgröße Netto-Überschussrendite gegen SPY in bp je Ereignis. **Ein** einseitiger Test (Long, Netto-Kante > 0), α_i = 0,0025 (z = 2,807), Register-Index 8 von 20 (D37). Danach 12 Plätze frei.
**Offene Entdeckungs-Ausnahme (D46):** Prior der Netto-Kante für illiquide Small Caps ist literaturgestützt positiv (brutto), aber Kosten dort hoch [A]; Ergebnis „nicht signifikant“ ist **kein** Nullbefund, sondern „nicht nachweisbar“, falls Kante < MDE.
**Warum dieser Test:** Haupttest Welle 3 zeigte für das 4-h-Krypto-Ereignis/Reversion/Flow-Muster brutto ≈ 0. Hier ein anderer Mechanismus (Informationsvorsprung gegenüber langsam arbitrierten Titeln, Wochen-Horizont), bei dem Kosten relativ zur Haltedauer kleiner sind.

## 2 Daten und Fenster
- **Ereignisse:** `D:\CT109-Data\sec-form345\insider_clusters_v2.csv` (SEC-Form-4-Datensätze, Code P, Offizier/Direktor, Fenster 14 Tage, ≥ 3 verschiedene Personen, Summe ≥ 100 000 USD, 30 Tage Sperre je CIK; Spalten `cik,symbol,cluster_date,n_owners,total_usd,avg_price,kmin`). Es zählen Zeilen mit `kmin = 3`, `avg_price ≥ 2 USD`, `cluster_date` in **2016-09-01 … 2026-05-31** (Ende so gewählt, dass Haltedauer vor dem Sperrdatum endet). `cluster_date` = Einreichungsdatum; Einstieg frühestens am **nächsten** Handelstag (konservativ gegenüber Annahmezeit).
- **Preise:** Alpaca-Tageskerzen (SIP, `adjustment=all`), je Symbol eine CSV in `D:\CT109-Data\alpaca-daily`; Bars existieren nur an Tagen mit Handel; **hartes Ende:** Bars ab 2026-07-01 werden beim Laden verworfen. Hedge: SPY (gleiches Verzeichnis, `--extra SPY,IWM`).
- **Rohdaten bleiben auf Andis PC** (Alpaca-Nutzungsbedingungen [A]: lokale Forschung); nur Aggregate in den Chat. Vorwärtsfenster 2026-07-01 … 09-30 bleibt unberührt.

## 3 Zustand (ex ante)
SPY-RV30 (annualisierte Standardabweichung der letzten 30 Tagesrenditen, Information ≤ D−1), Perzentil gegen die letzten 756 Handelstage (mind. 120): NIEDRIG < 1/3, MITTEL, HOCH > 2/3. Einfache Referenz; keine komplexere Zustandsvariable.

## 4 Ereignis und Handelsregel
1. **Zulässig:** Symbol hat Bars-Datei; mindestens 16 Bars vor `cluster_date` innerhalb von 40 Kalendertagen; **Median des Dollarvolumens (Close × Volumen) der letzten 20 Bars ≥ 300 000 USD**; Zustand vorhanden; Einstieg und Ausstieg bestimmbar. Nicht zulässige Ereignisse werden nur gezählt (Lücke/Liquidität).
2. **Einstieg:** Open der ersten Bar nach `cluster_date` (Toleranz 6 Kalendertage, sonst kein Trade).
3. **Ausstieg:** Open der ersten Bar ≥ Einstieg + 28 Kalendertage (Toleranz 6 Tage). Endet die Bar-Reihe früher (Delisting, Übernahme), Close der letzten Bar (Flag `early`; mindestens 3 Tage nach Einstieg).
4. **Überschussrendite:** `ln(Exit/Entry)·10⁴ − ln(SPY_Open_Ausstieg/SPY_Open_Einstieg)·10⁴`.
5. **Kosten (Rundreise, [A], richtungsfrei):** nach Dollarvolumen-Klasse (20-Tage-Median): 300 k–2 M USD **100 bp**, 2–10 M **50 bp**, ≥ 10 M **25 bp**; zusätzlich **4 bp** SPY-Hedge. Netto = Überschuss − Kosten − 4 bp.
6. **Episode/Inferenz-Einheit:** das Ereignis (Emittenten-Sperre 30 Tage verhindert Überlappung je CIK); Abhängigkeit zwischen Emittenten in derselben Marktphase wird über den **Wochen-Blockbootstrap** (Blocklänge 6 Wochen) abgebildet, nicht über unabhängige Ereignisse.

## 5 Kriterien (α_i = 0,0025, einseitig)
- **C1 Mindestmenge:** < 500 zulässige Ereignisse ⇒ INSUFFICIENT.
- **C2:** Block-Bootstrap über Kalenderwochen (Blocklänge 6, 10 000 Ziehungen, Seed 20261025): p(Mittel ≤ 0) ≤ α und untere α-Schranke > 0.
- **C3 Placebos (Quantil 0,975, beide müssen übertroffen werden):** (a) 2 000 Zeitversatz-Placebos (alle Clusterdaten gemeinsam um ±8 … ±104 Wochen verschoben, Kosten- und Zustandslogik identisch); (b) 500 Same-Symbol-Placebos (zufälliges Datum desselben Symbols, > 60 Tage von echten Ereignissen).
- **C4 Stress (alle vier Mittel > 0):** (a) Kosten × 1,5; (b) Einstieg einen Handelstag später; (c) Kosten Klasse 1 × 2; (d) **Survivorship-Stress:** Ereignisse ohne Bars-Datei werden mit dem 10-%-Quantil der Netto-Verteilung nachgezählt.
- **C5 Konzentration:** die zehn besten Ereignisse ≤ 25 % des Brutto-Gewinns (Summe positiver Netto-Werte); kein Jahr > 50 % der Gesamtsumme.
- **C6 Stabilität:** beide zeitlichen Hälften (nach Clusterdatum) Mittel > 0 **und** in mindestens zwei von drei SPY-RV30-Zuständen (je ≥ 100 Ereignisse) Mittel > 0.
- **C7 Kalibrierung:** Gesamtregel an Nullwelten (Zeitversatz-Nullen), Fehlpass bei δ = 0 ≤ 5 %; Power-Tabelle bei ½·MDE / MDE / 2·MDE; Nullwelten auf **gezählte zentrierte Streuung** skaliert.
- **Kategorien:** BESTAETIGT / NICHT BESTAETIGT (C2 erfüllt, anderes verfehlt) / POSITIV-UNTERPOWERT / NICHT NACHWEISBAR / INSUFFICIENT. Echtgeld nie aus diesem Test allein; Paper vorab (Pflicht).

## 6 Power-Zeile (vor Freeze)
MDE80 = (z_{1−α} + z_{0,8})·σ/√n = 3,649·σ/√n. Mit σ je Ereignis ≈ 1 500 bp [A] und n ≈ 3 400 ⇒ ≈ **88 bp** Nachweisgrenze. Erwartung der Netto-Kante: Literatur-Brutto für Small-Cap-Insider-Cluster 100–300 bp in 1–3 Monaten [R, nicht geprüft]; abzüglich 50–100 bp Kosten ⇒ Erwartung **0 … 150 bp** [A] – liegt **an** der Auflösung. **Zählung (Andi, 25.10. ≈ 19:00, L2):** n = 3 752, σ (zentriert) = 1 658 bp ⇒ MDE80 ≈ **99 bp**; Klassen 1 122 / 1 065 / 1 565, Zustände 1 022 / 1 099 / 1 631. Regel: liegt MDE > 120 bp, wird INSIDER-ALL als HINWEIS-Klasse deklariert.

## 7 Ablauf
1. `insider_test_v1.py count` (nur Anzahlen, zentrierte Streuung, keine Mittelwerte).
2. `calib --sigma <gezählt>` (C7; Operationscharakteristik).
3. Freeze-Paket (Manifest mit Spec, Code-Hash, Cluster-CSV-Hash, Bars-Manifest, Parameter) und GO-Satz „GO FREEZE-R3C – <Hash>“ (neuer, eigener Satz; ein bloßes „go“ gilt nicht).
4. `final … --spec-hash` genau einmal; keine Zwischenblicke; Registerzeile auch bei Abbruch.

## 8 Offene Punkte (vor Freeze zu klären)
- SPY/IWM-Download erledigt (25.10. ≈ 19:00).
- Tickerwiederverwendung/Umbenennungen: Symbol → Bars-Zuordnung kann falsche Firmen treffen [A]; wird über Ereignisse ohne Bars (301) und frühe Enden (21) beziffert, nicht korrigiert.
- Survivorship: Cluster-CSV enthält delistete Emittenten nur, wenn Alpaca Bars hält; Stress C4(d) deckelt die Verzerrung grob.
- Kostenannahmen 100/50/25 bp sind ungemessen (IBKR-Gebührenseite und echte Spreads small caps offen) – Paper-Säule B misst sie.
- Alpaca-Lizenz: nur lokale Forschung, keine Weitergabe [A].

## 9 Änderungslog
- v0.1 (25.10.2026 ≈ 19:00): Entwurf; Code `code/tools/insider_test_v1.py` (SHA `05c1e9d6192997c5`, synthetisch getestet: count/calib/final laufen, Nullwelt besteht nicht).
