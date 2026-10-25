# CT109 – RUNDE-4A-SPEZIFIKATION v0.1 (ENTWURF K6 FLOW, NICHT GEHASHT)

**Status:** Entwurf des Einsatzleiters, Stand So 25.10.2026 ≈ 17:45 Berlin. Nicht gültig bis zum Freeze-Eintrag in `01`. Ergänzt `RUNDE3A_SPEC_v1_FREEZEKANDIDAT.md` (gleiche Datenbasis, gleiche Zustandsvariable, gleiche Test-Mechanik C2–C7); bei Widerspruch gilt für K6 diese Datei. Entscheidung: `02` D43. Evidenzstufen wie dort.

## 1 Gegenstand
**K6 FLOW:** Kraken-USD-Paare, Stunden mit Volumenschock **und** starkem Aggressor-Ungleichgewicht. **Ein** Konto-Platz (Register-Index 7), zwei einseitige Tests auf denselben Ereignissen, je α = α_i/2 = 0,00125 (z = 3,023): **K6-C** (Position in Richtung der Imbalance = Fortsetzung), **K6-R** (entgegen = Umkehr). Beide können nicht gleichzeitig bestehen (Bruttovorzeichen entgegengesetzt). Offene Entdeckungs-Ausnahme analog D41: Prior der Netto-Kante −10 … +15 bp [A] liegt bei/unter der Nachweisgrenze; ein nicht signifikantes Ergebnis ist **kein** Nullbefund.

## 2 Daten und Fenster
Wie Freeze-Kandidat 3A §2: 1-Minuten-Aggregate (Spalten `vol_b`, `vol_s`, `notional` je Minute), Fenster 2019-01-01 … 2026-06-30, hartes Ende ≥ 2026-07-01, gleiche Fehldruck-Bereinigung, Manifest `register/MANIFEST_AGG_SHA256.txt` (41 Dateien). **Paare:** alle 41 (XBT, ETH + K4P-Pool). Vorwärtsfenster 2026-07-01 … 09-30 bleibt unberührt bis nach dem Haupttest.

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
8. **Verteilung der Ereignisse (Zählung, Andi-Lauf):** sehr ungleich: XBT 3, ETH 6, SOL 4, XRP 39, **ETC 1 437, DASH 1 547, ZEC 987, XTZ 848**, übrige 3 … 600. K6 testet damit überwiegend **Flussschocks in dünn gehandelten Alts**. Die Kostenannahme 26 bp ist dort **optimistisch** (Perp-Liquidität ungeprüft); Stress C4(a) (× 1,5) ist daher besonders ernst zu nehmen, und Paper (Säule B) muss die Kosten je Paar messen. **Echtgeld-Umsetzbarkeit offen** (Positionsgröße ≤ 600 EUR in dünnen Perps).

## 5 Kriterien (je Seite)
Wie 3A §5 mit α = 0,00125: C2 (Bootstrap über Kalenderwochen, Blocklänge 4, 10 000 Ziehungen, Seed 20261025), C3 (2000 Zeitversatz- und 500 vol-gematchte Placebos, Quantil 0,975, Ereignisse behalten Richtung und Zustand), C4 (Kosten × 1,5; Einstieg 1 Minute später; Slippage × 2 in HOCH), C5, C6; Kategorien wie 3A. „0 Trades“ = INSUFFICIENT.

## 6 Kalibrierung C7 (Platzhalter bis Lauf)
`calib_k6` (Skript-Hash `b715f5fa4fdfa6ef`, 200 Nullwelten, `--sigma 241`): Ergebnisse folgen.

## 7 Paper
Zulauf ≈ 400–650 Episoden/Jahr (Zählung 2022–2025: 579 / 681 / 619 / 645 bei m=20/i=0,7) ⇒ Vorwärtsbestätigung bereits in Monaten möglich: n = (2,487·σ/δ)² [R]: σ ≈ 240 bp, δ = 20 bp ⇒ ≈ 1 440 Episoden ≈ 2–3 Jahre; δ = 40 bp ⇒ ≈ 360 Episoden ≈ 9 Monate. Säulen A–D wie Entwurf 3A §10, Looks bei n = 100 / 250 / 500 Episoden [A].

## 8 Offen vor Freeze
Kalibrierung C7; Spec-Endfassung; Freeze-Paket (Manifest, Code-Hash `k6_test_v1.py`, Seeds); GO-Schablone Registry (Andi). K6 kann **gemeinsam mit 3A** (Register-Index 5, 6, 7) oder als eigener Freeze gesetzt werden.
