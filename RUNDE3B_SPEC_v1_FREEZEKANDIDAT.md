# CT109 – RUNDE-3B-SPEZIFIKATION v1 (FREEZE-KANDIDAT K6 FLOW, NICHT GEHASHT)

**Status:** Kandidat des Einsatzleiters, Stand So 25.10.2026 (Endlektüre ≈ 17:15 Berlin) (früher `RUNDE4A_SPEC_v0.1_ENTWURF_K6.md`, umbenannt: K6 geht gemeinsam mit 3A in **einen** Freeze). Wird erst mit dem Freeze-Eintrag in `01` (Datum, Freeze-Hash) **gültig**; nach dem Freeze keine Änderung. Ergänzt `RUNDE3A_SPEC_v1_FREEZEKANDIDAT.md` **in der gemeinsam gefrorenen Fassung** (gleiche Datenbasis, Zustandsvariable und Test-Mechanik C2–C7); bei Widerspruch gilt für K6 diese Datei. Entscheidungen: `02` D43 (Parameter), D44 (Liquiditätsfilter). Evidenzstufen: [L1] Herstellerangabe, [L2] von Andi gemessen, [A] Annahme, [R] Recherche.

## 1 Gegenstand
**K6 FLOW:** Kraken-USD-Paare, Stunden mit Volumenschock **und** starkem Aggressor-Ungleichgewicht. **Ein** Konto-Platz (Register-Index 7), zwei einseitige Tests auf denselben Ereignissen, je α = α_i/2 = 0,00125 (z = 3,023): **K6-C** (Position in Richtung der Imbalance = Fortsetzung), **K6-R** (entgegen = Umkehr). Beide können nicht gleichzeitig bestehen (Bruttovorzeichen entgegengesetzt). Offene Entdeckungs-Ausnahme analog D41: Prior der Netto-Kante −10 … +15 bp [A] liegt bei/unter der Nachweisgrenze; ein nicht signifikantes Ergebnis ist **kein** Nullbefund.

## 2 Daten und Fenster
Wie Freeze-Kandidat 3A §2: 1-Minuten-Aggregate (Spalten `vol_b`, `vol_s`, `notional` je Minute), Fenster 2019-01-01 … 2026-06-30, hartes Ende ≥ 2026-07-01, gleiche Fehldruck-Bereinigung, Manifest `register/MANIFEST_AGG_SHA256.txt` (41 Dateien). **Paare:** 34 nach Liquiditätsfilter D44 (Perp vorhanden, Median-Spread ≤ 12 bp, 24-h-Volumen ≥ 250 000 USD; Liste `register/K6_POOL_LIQFILTER_20261025.txt`, wird mitgehasht; ausgeschlossen ALGO, XTZ, SHIB, ETC, MANA, KAS, FLOW). Vorwärtsfenster 2026-07-01 … 09-30 bleibt unberührt bis nach dem Haupttest.

## 3 Zustand
Wie 3A §3 (XBT-RV30-Perzentil, NIEDRIG/MITTEL/HOCH, nur Information ≤ D−1).

## 4 Ereignis und Handelsregel
1. **Stundenreihen** je Paar (UTC-Stunde): `N_h` = Summe `notional`, `V_b`, `V_s` = Summen `vol_b`, `vol_s`; `imb_h = (V_b − V_s)/(V_b + V_s)`. `med_h` = Median von `N` der 720 Vorstunden (Stunden ohne Handel zählen als 0; mindestens 720 Stunden Historie).
2. **Ereignis** (Paar, Stunde `h`, `h ≥ 2019-01-01`, Zustand vorhanden): `N_h ≥ 20·med_h` **und** `|imb_h| ≥ 0,7`. Richtung `d = sign(imb_h)`. (Schwellen nach Zählregel D43: strengster Rasterpunkt mit ≥ 2 000 Episoden; Raster m ∈ {5, 10, 20}, i ∈ {0,3; 0,5; 0,7}.)
3. **Einstieg:** Taker zum Open der ersten Minute ≥ `h + 3600 s` (Toleranz 600 s, sonst kein Trade); K6-C: Position `d`, K6-R: Position `−d`.
4. **Ausstieg:** Open der ersten Minute ≥ Einstieg + 4 h (Toleranz 600 s) oder **Stop** 5 % gegen die Position (Fill zum schlechteren von Stop und Open der Stop-Minute, 10 bp Zusatz-Slippage).
5. **Sperre je Paar:** neues Ereignis erst nach Ausstieg des laufenden Trades (keine Überlappung).
6. **Netto-Rendite:** `d_pos·ln(Exit/Entry)·10⁴ − Rundreise`; Rundreise **16 bp (XBT, ETH)** bzw. **26 bp (übrige)** [A-C3/A-C5]; Funding im 4-h-Fenster nicht abgezogen [A-C2].
7. **Episode:** Einstiege aller Paare, Abstand < 4 h zum vorherigen Einstieg ⇒ gleiche Episode; Episodenrendite = Mittel je Paar, dann über Paare; Zeit = erster Einstieg, Zustand = des ersten Einstiegs.
8. **Verteilung der Ereignisse (Zählung, gefilterter Pool, Raster 20/0,7):** 8 537 Ereignisse, 3 533 Episoden, σ je Einstieg 246 bp, Zustände [1 956, 1 122, 468] Episoden, je Jahr 2019: 422, 2020: 487, 2021: 210, 2022: 552, 2023: 698, 2024: 549, 2025: 485, 2026 (H1): 130. Verteilung bleibt ungleich (DASH 1 547, ZEC 987, ATOM 432, … XBT 3, ETH 6): K6 testet überwiegend **Flussschocks mittelliquider Alts**. Ungefilterter Pool (41 Paare) war: 4 014 Episoden, σ 241 bp. Kostenannahme 26 bp (Spread-Beleg D44: ereignisgewichtet ≈ 5 bp Voll-Spread im gefilterten Pool, Top-of-Book-Tiefe nur ≈ 100–400 USD) ist für 600-USD-Orders über Level 1 hinaus **ungemessen**; Stress C4 und Paper (Säule B, Kosten je Paar) sind maßgeblich. **Echtgeld-Umsetzbarkeit offen.**

## 5 Kriterien (je Seite)
Wie 3A §5 mit α = 0,00125: C2 (Bootstrap über Kalenderwochen, Blocklänge 4, 10 000 Ziehungen, Seed 20261025), C3 (2000 Zeitversatz- und 500 vol-gematchte Placebos, Quantil 0,975, Ereignisse behalten Richtung und Zustand), C4 (Kosten × 1,5; Einstieg 1 Minute später; Slippage × 2 in HOCH), C5, C6; Kategorien wie 3A. „0 Trades“ = INSUFFICIENT.

## 6 Kalibrierung C7 (Hauptlauf mit gefiltertem Pool, 34 Paare; Andi-Lauf 25.10. ≈ 16:45, L2; `run_k6f.ps1` Hash `d82733aaf400d6e4`, Skript `k6_test_v1` SHA-Kurzform `b715f5fa4fdfa6ef`; 200 Nullwelten, 2000 Zeitversatz- und 500 vol-gematchte Placebos, 10 000 Ziehungen, Seed 20261025, α je Seite 0,00125; Nullwelten auf gezähltes σ = 246 bp je Einstieg skaliert, Faktor 0,99 = Annahme A)
| Seite | Episoden | Episoden-σ skaliert | MDE80 | Fehlpass δ=0 | Gesamtregel bei ½MDE / MDE / 2·MDE |
|---|---|---|---|---|---|
| K6-C (Fortsetzung) | 2 973 | 218 bp | 15,4 bp | 0/200 | 6,5 % (7,7 bp) / 65 % (15,4 bp) / 100 % (30,9 bp) |
| K6-R (Umkehr) | 2 971 | 219 bp | 15,5 bp | 0/200 | 9,5 % (7,8 bp) / 68,5 % (15,5 bp) / 100 % (31,0 bp) |
**Beide Seiten zusammen: Fehlpass 0/200 = 0 % (≤ 5 % ✓) ⇒ C7 bestanden.** Einzelkriterien bei MDE (C): C2 142, C3 193, C4 135, C5 189, C6 200 von 200 ⇒ weiterhin C4 (Stress) und C2 binden. 80 % Gesamt-Power bei ≈ 1,2 × MDE ≈ **18–19 bp** wahrer Netto-Kante (Interpolation, [A]); bei 10 bp ≈ 25 %, bei 15 bp ≈ 62 % (interpoliert). Der Filter hat die Nachweisgrenze von 13,5 auf 15,4 bp verschlechtert (weniger Episoden), die Gesamt-Power bei MDE aber verbessert (51–58 % → 65–68 %), weil dünne Alts den Stress-Test besonders belasteten.
*Referenz ungefilterter Pool (41 Paare, 3 553 Episoden, σ 241 bp, MDE80 13,5 bp): Fehlpass 1/200 (K6-R) bzw. 0,5 % zusammen; Gesamtregel bei MDE C 57,5 %, R 51 % – nicht Grundlage des Freezes (D44).* Grenzen wie 3A (Nullwelten ohne Mikrostruktur, Skalierung auf Streuung).

## 7 Paper
Zulauf ≈ 500–700 Episoden/Jahr (gefiltert, Zählung 2022–2025: 552 / 698 / 549 / 485) ⇒ Vorwärtsbestätigung in Monaten bis wenigen Jahren: n = (2,487·σ/δ)² [R] mit σ ≈ 218 bp: δ = 20 bp ⇒ ≈ 735 Episoden ≈ 1,3 Jahre; δ = 40 bp ⇒ ≈ 184 Episoden ≈ 4 Monate (Rechnung gegenüber dem Vorentwurf, der 1 440 / 360 nannte, korrigiert). Säulen A–D (Entwurf `RUNDE3_SPEC_v0.1_ENTWURF.md` §10; werden vor Paper-Start separat gehasht), Looks bei n = 100 / 250 / 500 Episoden [A].

## 8 Code, Lauf und Vorwärtsfenster
- **Code:** `code/tools/k6_test_v1.py` (Modus `final`, Pflichtargument `--spec-hash`), Lader/Hilfen `count_events_v2.py`, `count_cs_v1.py` (Pool-Konstante, wird für K6 durch die Namensliste ersetzt), Zählung `count_events_v4.py`; Voll-Hashes stehen im Freeze-Manifest.
- **Lauf:** einmalig nach Freeze auf Andis PC: `python -u k6_test_v1.py final <agg> <34 Paare laut register/K6_POOL_LIQFILTER_20261025.txt> --spec-hash <Freeze-Hash>`; Ausgabe nur Aggregate; Registerzeile auch bei Abbruch. Reihenfolge der Läufe: K4, K4P, K6; kein Zwischenblick.
- **Vorwärtsfenster** 2026-07-01 … 09-30: einmal nach dem Haupttest, gleiche Regel, Fensterargument, nur Aggregate.
- **Veto-Prüfung Einsatzleiter (Stand 25.10.):** Beleg ✓ (C7, Zählung, Kostencheck L1), Protokoll ✓ (Spec vor Datenöffnung), Echtgeld nicht berührt ✓, Budget ✓ (0 EUR). Kein Veto; die offenen Annahmen sind in §4.8 und §6 offengelegt.

## 9 Changelog
- 25.10.2026 (Nachmittag): aus Entwurf v0.1 zum Freeze-Kandidaten v1 (Pool 34 nach D44, C7 mit gefiltertem Pool, Paper-Rechnung korrigiert, §8 neu).
