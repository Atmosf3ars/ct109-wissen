# CT109 – GATE-SPEZIFIKATION v1 („Bewegungsbudget-Gate“, LF-1)

**Erstellt:** Do 22.10.2026, 20:15 UTC (22:15 Berlin). **Autor:** Einsatzleiter (Claude), Regime „Entscheiden, nicht fragen“ (00 §6). **Status:** Entscheidung des Einsatzleiters, kein Owner-GO, kein Datenzugriff nötig oder erteilt.
**Unveränderlich nach Hash-Eintrag** (SHA-256 dieser Datei steht im Änderungslog von `01_STATUS.md`). Änderungen nur als v2 mit Begründung und nur **vor** der Öffnung von Historiedaten. Nach dem Gate-Lauf ist v1 eingefroren.
Parameter mit Dezimalpunkt. Alle Zeiten UTC.

## 0. Zweck und Grenzen
- Das Gate prüft die **notwendige** Bedingung `ρ_min = c / E|r_h| ≤ ρ_plausibel` (03 §5). Es misst nur **Beträge** von Renditen, nie Vorzeichen, nie Signale. Gate-PASS ist **kein** Edge-Beleg.
- Es bestimmt, welche (Asset, Horizont)-Zellen Hypothesen der Hauptlinie LF-1 (Momentum/Ausbruch, Mean-Reversion; Horizont ≥ 1 h) tragen dürfen. Zellen ohne Zulassung werden vor dem Freeze gestrichen.
- **Offenlegung zum Wissensstand:** Vor dieser Spezifikation lagen nur die in 03 §5 dokumentierten σ-Werte (5-min, 05.–08.10.2026, L1) vor, keine Historie der LF-1-Universen. Allgemeines Vorwissen des Autors über Krypto-/Aktienmärkte ist nicht ausschließbar; deshalb sind alle Schwellen unten **vor** dem Datenblick festgelegt und nicht anpassbar.

## 1. Universen und Preisreihen
- **Krypto (Track K):** BTC, ETH, SOL. Ausführungsinstrument = Kraken-Futures-Perpetual (PF_XBTUSD, PF_ETHUSD, PF_SOLUSD); Preisreihe = Kraken-Spot-OHLCVT (XBT/USD, ETH/USD, SOL/USD), **60-min-Bars** als Preisproxy (Basis Spot↔Perp ist ein ungemessenes Risiko, Annahme A5).
- **Aktien (Track S):** TSLA, INTC, NVDA (die gebuchten Depth-Titel). Datenquelle **offen** (kein Kauf ohne Andis Abo-GO). Gate-Parameter gelten unverändert; Sitzungsdetails (nur reguläre Handelszeit, Close-to-Close ab 1 Handelstag) werden in v1.1 **vor** Datenzugriff festgeschrieben, ohne Schwellenänderung.
- Keine weiteren Assets in v1 (kein Nachschieben nach Datenblick).

## 2. Horizonte
- Krypto: h ∈ {1 h, 4 h, 24 h, 72 h}. Aktien: h ∈ {1 h, 4 h, 1 Handelstag, 3 Handelstage}.
- 5-min- bis 30-min-Horizonte sind gesperrt (03 §5, Kostenwand belegt). Fenster starten stündlich (überlappend), Rendite `r = 1e4 · ln(P_{t+h} / P_t)` in bp. Fenster mit fehlendem Endpunkt-Bar werden verworfen.

## 3. Regime (ex ante, operativ)
- Regimewahl nur aus **BTC/USD-Tagesschlusskursen (UTC)** bis 2026-06-30: `RV30(t) = sqrt(365) · Std_{ddof=1}(ln(C_k/C_{k-1}), k = t-29..t)`, nur Information ≤ t.
- Kandidatenfenster der Länge W Tage (Start täglich), Score `M` = Median von RV30 im Fenster. **LV-Fenster:** M ≤ 0.45. **HV-Fenster:** M ≥ 0.55.
- **Regime A (Gate und Discovery) = LV-Fenster** mit spätestem Ende ≤ 2026-06-30. **Regime B (Bestätigung) = HV-Fenster** mit spätestem Ende, das A weder überlappt noch näher als 14 Tage an A liegt. Begründung: A ist das für die Kostendeckung **strengere** Regime (kleinstes E|r|); was dort zulässig ist, ist in B nicht schwerer.
- W = 270 Tage; existiert A oder B nicht, W = 180 Tage; existiert dann immer noch eines nicht: **Status BLOCKED** (keine Historien-Discovery; Fallback = Forward-Daten ab 01.07.2026 mit eigener Vorregistrierung).
- Aktien-Regime (v1.1, vorab festgelegt): Referenz SPY-Tagesschlüsse, gleiche Formel, Schwellen LV ≤ 0.13, HV ≥ 0.20.
- Ergebnis der Regimewahl (Datumsgrenzen) wird **vor** dem Gate-Lauf gehasht und protokolliert.

## 4. Messgröße
- Je Zelle (a, h) in Regime A: `E|r|` = Mittelwert von |r| über alle gültigen stündlichen Fenster in A.
- **Untere Vertrauensgrenze LCB95** = 5-%-Quantil von `E|r|` aus Moving-Block-Bootstrap (Blocklänge 168 h, 2000 Ziehungen, Seed 20261022).
- **n_eff** = floor(gültige Stunden in A / h) (nichtüberlappende Fenster). Zelle mit n_eff < 60 = **nicht bewertbar** (zählt als nicht zugelassen).

## 5. Kostenmodell (Roundtrip, bp, Notional 5 000 USD)
`c_gate(a,h) = 1.25 · c0(a) + c_fund(h)`
- `c0` (Gebühren + Spread-Median; L1 aus 03 §5): BTC-Perp 10.1, ETH-Perp 10.4, SOL-Perp **16.0** (Obergrenze aus Scouting-Hürden, Rechnung, nicht gemessen), TSLA 3.7, INTC 3.9, NVDA 2.3.
- Faktor 1.25 = Puffer für ungemessene Latenz-/Slippage-Anteile (Annahme A2, nicht optimiert).
- `c_fund(h) = 1.0 bp · h/8 h` für Perps (Annahme A4, konservative Konstante; echtes Funding wird nur berichtet, ändert v1 nicht); Aktien 0.

## 6. Entscheidungsregel
- `ρ_min⁺(a,h) = c_gate(a,h) / LCB95(E|r_{a,h}|)`.
- **Klasse P:** ρ_min⁺ ≤ 0.05 (plausibel). **Klasse W:** 0.05 < ρ_min⁺ ≤ 0.10 (weit). **Klasse X:** > 0.10 oder nicht bewertbar (gesperrt). (ρ_plausibel 0.05/0.10 sind Annahmen A1, nicht gemessen.)
- Zulässig sind nur P und W. Ein Horizont ist gesperrt, wenn in **keinem** Asset zulässig.
- LF-1-Freeze: ≤ 8 Hypothesen, jede nur in zulässigen Zellen; **Klasse-W-Zellen tragen höchstens 2 der 8 Hypothesen.** Keine zulässige Zelle = **dokumentierter Nullbefund**, keine LF-1-Discovery, Runde 2 sofort (04 §4).
- **Bestätigungsbedingung (Regime B):** dieselbe Messung auf B muss für die Zelle ρ_min⁺ ≤ 0.10 ergeben, sonst gilt die Hypothese in B als nicht bestanden (kein Ersatz, kein Nachjustieren).

## 7. Datenqualität (vor dem Gate-Lauf, nur Q-Metriken)
Je Asset in A: fehlende 60-min-Bars ≤ 1.0 %; keine zusammenhängende Lücke > 6 h; keine doppelten Zeitstempel; Bars ohne Volumen ≤ 5 %; |1h-Rendite| > 30 % → Prüfliste (keine automatische Entfernung). Verfehlt ein Asset Q, sind seine Zellen **nicht bewertbar**. Survivorship (nur heute gelistete Paare) wird vermerkt.

## 8. Prozess
1. Spec-Hash in `01` eintragen. 2. Rohdaten laden (Hash der Dateien notieren). 3. Q-Prüfung. 4. Regimewahl (§3) → Hash. 5. Gate-Lauf, **einmalig**; Skript-Hash, Daten-Hash und Seed vorab notiert; Ausgabe nur Aggregat je Zelle: n_eff, E|r|, LCB95, c_gate, ρ_min⁺, Klasse. 6. Wiederholung nur bei technischem Fehler mit identischem Skript-Hash, Fehler protokolliert. 7. Danach Freeze der Liste (Hash), erst dann Discovery.
- **Verboten bis zum Freeze:** jede Statistik mit Vorzeichen (Momentum-Rendite, Autokorrelation der Richtung, Trefferquote, Sharpe, Backtest).
- Maßstab später: Netto-Expectancy je Trade in bp nach Kosten; bei festem Zeitausstieg gibt es kein R, damit keine Fair-Rate-Formel (Review R12), sonst gilt `1/(1+R)` je Trade.
- Festgelegt vor Datenzugriff: BH-FDR q = 0.05, Bonferroni-Gegenprobe α = 0.05/m.

## 9. Annahmen (nicht gemessen)
A1 ρ_plausibel 0.05/0.10. A2 Kostenfaktor 1.25. A3 c0-Werte, SOL 16.0 bp. A4 Funding 1.0 bp je 8 h. A5 Spot als Preisproxy für Perp. A6 Regime-Schwellen 0.45/0.55 und Fensterlängen 270/180. A7 Horizontsatz. A8 Notional 5 000 USD.

## 10. Vorab-Erwartung (subjektiv, nicht bindend, damit Überraschung messbar bleibt)
1-h-Zellen: alle Klasse X. Krypto 4 h: X. Krypto 24 h/72 h in LV: knapp, höchstens W; P(≥ 1 Krypto-Zelle zulässig) ≈ 0.5. Aktien 1 Tag/3 Tage: P(≥ 1 Zelle zulässig) ≈ 0.8, sobald eine Quelle vorliegt.
