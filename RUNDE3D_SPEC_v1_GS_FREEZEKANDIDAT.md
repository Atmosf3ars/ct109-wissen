# CT109 – RUNDE-3D-SPEZIFIKATION v1 (FREEZE-KANDIDAT GOLD-SILBER, HINWEIS-KLASSE, NICHT GEHASHT)

**Status:** Kandidat des Einsatzleiters, Stand So 25.10.2026 (≈ 21:45 Berlin), auf ausdrücklichen Wunsch von Andi („gold silber testen wir jetzt“, 21:12). Wird erst mit dem Freeze-Eintrag in `01` (Datum, Freeze-Hash) **gültig**. Entscheidung `02` D50 (HINWEIS-Klasse) und D51 (Lauf als HINWEIS). Evidenzstufen: [L2] von Andi gemessen, [A] Annahme, [R] Recherche.

## 1 Gegenstand und Klasse
**GS** testet, ob die **Spread-Bewegung** von Silber gegen Gold (SLV minus β·GLD) in der Folgewoche **fortgesetzt (GS-C)** oder **umgekehrt (GS-R)** wird. **Klasse HINWEIS: kein α-Konto-Platz** (D37 bleibt 7/20), kein BESTAETIGT möglich. Zweck: Andis Frage beantworten und eine Vorwärtsbeobachtung begründen. Zwei Seiten werden berichtet, beide ohne Mehrfachtest-Korrektur (deshalb nur Hinweis). Vorab-Erwartung der Netto-Kante: ≲ 5 % p. a. [A] gegen MDE ≈ 15 % p. a. (siehe §6) ⇒ **wahrscheinlichstes Ergebnis: NICHT NACHWEISBAR, kein Nullbefund.**

## 2 Daten und Fenster
GLD und SLV, Alpaca-Tageskerzen (SIP, adjustment=all), Andis PC; `register/MANIFEST_GS_DATA_SHA256.txt`; Fenster 2016-01-04 … 2026-06-30 (hartes Ende, ≥ 2026-07-01 wird beim Laden verworfen); 2 637 gemeinsame Handelstage [L2, `count_gs_v1`]. Rohdaten bleiben auf dem PC.

## 3 Regel (alles ex ante)
1. **Woche** = ISO-Kalenderwoche der gemeinsamen Handelstage; Wochenrendite je ETF = ln(Close letzter Handelstag / Open erster Handelstag) (nur Handelszeit, Wochenendlücke ausgelassen).
2. **β_k** (zu Beginn der Handelswoche k bekannt) = OLS-Steigung der Wochenrenditen SLV auf GLD über die 52 Wochen k−52 … k−1. Erste Handelswoche mit β: Woche 53.
3. **Signal** der Handelswoche k: `s = sign(RS_{k−1} − β_k · RG_{k−1})` (Spread der Vorwoche mit β_k). s = 0 ⇒ kein Trade.
4. **Position GS-C:** Spread-Position `d = s` (Long SLV / Short β·GLD, wenn s = +1). **GS-R:** `d = −s`. Einstieg zum Open des ersten Handelstags der Woche k, Ausstieg zum Close des letzten Handelstags der Woche k; Gewicht β auf GLD (dollar-gewichtet nach Beta).
5. **Netto-Rendite der Woche:** `d·(RS_k − β_k·RG_k)·10⁴ − 6 bp`. Kosten 6 bp je Woche = 4 ETF-Seiten × 1,5 bp [A: liquide US-ETFs, Spread ≈ 1–2 bp] pro Rundreise, in **jeder** Woche voll angesetzt (konservativ: kein Netting aufeinanderfolgender gleicher Positionen); Leihgebühr/Funding der Short-Seite nicht abgezogen [A-GS1] (GLD/SLV: Leihe ≈ 0,3–1 % p. a., hier unter 1 bp/Woche).
6. **Inferenz-Einheit:** die Woche. Keine Überlappung.

## 4 Kriterien (je Seite; Kategorie HINWEIS-POSITIV nur, wenn alle erfüllt)
(a) Netto-Mittel m > 0; (b) Block-Bootstrap über Wochen (Blocklänge 4, 10 000 Ziehungen, Seed 20261025), einseitig p ≤ 0,05; (c) m größer als das Quantil 0,975 von 2 000 Zeitversatz-Placebos (Signal um ±8 … ±52 Wochen verschoben); (d) beide zeitlichen Hälften > 0; (e) Kosten × 1,5 bleibt > 0. Sonst: **NICHT NACHWEISBAR** (m ≤ 0 oder Kriterien verfehlt; kein Nullbefund bei Kante unter MDE). **Es gibt kein BESTAETIGT.** Ein HINWEIS-POSITIV-Ergebnis begründet nur die Vorwärtsbeobachtung (Fenster ab 2026-07-01 und Paper), nie Echtgeld.
Zustände (Regel 3, ≥ 2 Zustände): bei HINWEIS-Klasse nicht erforderlich, aber im Vorwärtsfenster nachzuholen.

## 5 Kalibrierung (C7-lite, Andi-Gerät-Lauf 25.10. ≈ 21:40; `gs_test_v1.py calib`, SHA-Kurzform `008b120b1e763a6e`, 200 Nullwelten = Signal um ±8 … ±52 Wochen verschoben, je Welt 100 Placebos, 2 000 Ziehungen)
n = 495 Handelswochen mit Signal, Streuung 263 bp/Woche (zentriert), **MDE80 (einseitig 0,05) = 29,4 bp/Woche ≈ 15,3 % p. a.** je Seite.
| Seite | Fehlpass δ=0 | Regel bei ½MDE (14,7 bp) | bei MDE (29,4 bp) | bei 2·MDE (58,8 bp) |
|---|---|---|---|---|
| GS-C | 0/200 | 0,5 % | 76,5 % | 100 % |
| GS-R | 0/200 | 0 % | 88,5 % | 100 % |
Fehlpass-Rate ≤ 5 % ✓. Grenze: Nullwelten ohne Marktstruktur, die Zeitversatz-Welten erben die Autokorrelation des Spreads [A].

## 6 Power-Zeile (Regel 2)
Erwartete Netto-Kante ≲ 5 % p. a. (≈ 10 bp/Woche) [A] gegen MDE 29,4 bp/Woche ⇒ **unter Auflösung ⇒ HINWEIS-Klasse (deklariert, D50).** Die Power bei 10 bp wäre ≈ 0,5 % (δ = ½MDE → < 1 %). Der Lauf kann also nur eine **große** Kante (≥ 15 % p. a.) belegen; sonst ist das Ergebnis „nicht nachweisbar“.

## 7 Lauf
`python -u gs_test_v1.py final D:\CT109-Data\alpaca-daily --spec-hash <FREEZE_HASH>` genau einmal nach Freeze; Ausgabe nur Aggregate; Registerzeile auch bei Abbruch. Täglicher Spread-Test (4 ETF-Seiten × 1,5 bp = 6 bp je Tag) ist kostenseitig aussichtslos und nicht Teil dieses Laufs.

## 8 Änderungslog
- v1 (25.10.2026 ≈ 21:45): Kandidat; Code `code/tools/gs_test_v1.py` (SHA-Kurzform `008b120b1e763a6e`), Zählung `count_gs_v1.py`.
