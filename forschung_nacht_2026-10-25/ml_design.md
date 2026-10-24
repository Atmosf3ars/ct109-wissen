# ML für Signal-Discovery ohne Data-Snooping – Entwurf (Stand 25.10.2026)

Legende: **[A]** = Annahme/eigene Herleitung, nicht gemessen. Alle Zahlen zu σ und Volatilität sind [A]. Veröffentlichte Effektgrößen sind brutto und vor Publikations-Zerfall.

## 1. Kandidaten

| Kandidat | Mechanismus | Daten | Horizont | Erwartete Netto-Größe (Quelle) | Mit unseren Daten testbar? | Zwei Regime? | Hauptrisiko |
|---|---|---|---|---|---|---|---|
| **ML-1** Ridge-Querschnitt Aktien (Zelle: 3 Ridge-α + 1 flacher GBRT-Baum, nur Discovery) | Lineare Kombination bekannter OHLCV-Anomalien (Umkehr, Momentum, Vol, Liquidität) bündelt schwache Kanten | 495 Tageskerzen, Fenster A/E/F wie `lf2` | 10 Handelstage | ≈ 0 ± 2 bp/Tag [A]. Brutto-Zuwachs ggü. STR plausibel +1…3 bp/Tag [A]. Kosten+Leihe ≈ 2,4 bp/Tag (`03`). Netto-ML-Evidenz Aktien: Avramov et al. 2023: Gewinne schrumpfen ohne Microcaps/Distressed, Kosten fressen den Rest | ja, aber MDE 2,4–3,6 bp/Tag (§6) | ja (A ruhig; E: 2006–11; F: 2020–26) | E/F sind durch R-H1/R-H2 **nicht unberührt** (Aggregate gesehen); Survivorship begünstigt Umkehr-Features |
| **ML-2** Panel-Ridge Krypto-Perps, L/S Top-2/Bottom-2 | Volumen-/Trade-Zahl-/Flow-Proxies aus Kerzen (passt zu K1/D25) | Kraken OHLCVT 1h, ≤ 12 Coins | 24 h | Cakici et al. 2024: ML-Strategien netto profitabel, aber in kleinen, illiquiden Coins (für Kraken-Größe schlecht handelbar) | nur mit Vorab-Abbruchregel; MDE ≈ 15–25 bp/Trade [A] | ja (HV/LV nach Gate-Spec §3) | Kante, die Kosten (10 bp) deckt, liegt unter der Auflösung; Spot (160 bp) tot |
| Meta-Labeling auf STR/H1 | Zweitmodell filtert Trades des Primärsignals | wie oben | – | Evidenz nur synthetisch/simuliert (Joubert 2022; Wikipedia vermerkt Interessenkonflikt) | zurückgestellt: Primärsignal ist netto null | – | weniger Trades, kleineres n |
| Triple-Barrier-Label | pfadabhängiges Ziel | – | – | – | **nicht empfohlen** (§3) | – | Barrieren = zusätzliche Freiheitsgrade |

## 2. Warum H-ML-A scheiterte (Ergebnis ist nur als Zusammenfassung in `02` D22 dokumentiert, `01` §5: "Ergebnis nicht dokumentiert"; Ursachen daher [A])
1. **Horizont 30 s gegen Kostenmauer.** Bei Vorzeichenhandel gilt ρ = E[s·r]/E|r| ≈ IC (Gauß-Herleitung [A]). Break-even braucht IC ≥ c/E|r|. BTC 1 h: 10 bp / 43 bp ≈ 23 %. Kein OHLCV-Modell erreicht das. Bei 30 s ist es noch schlimmer.
2. **0 Trades ist die erwartete Folge.** Ein regularisiertes Modell sagt Werte nahe dem Mittel voraus: |ŷ| ≈ IC·σ_h ≈ 0,03 · 50 bp ≈ 1,5 bp, weit unter jeder Kostenschwelle. Mit Schwelle "ŷ > c" feuert es nie. Das hätte man **vor** Testöffnung auf Discovery-Daten sehen können.
3. **Stichprobe:** 10 Testtage, ein Regime, BTC/ETH hoch korreliert (N_eff ≈ 1,2 [A]).
4. **Vermeidung (verbindlich):** (a) Horizont aus dem Bewegungsbudget-Gate wählen (nur Beträge), nicht aus Datenverfügbarkeit. (b) **Trade-Raten-Vorcheck** auf Discovery: erwartete Trades ≥ Mindestzahl, sonst Abbruch als `NICHT_GETESTET` (verbraucht keine Bestätigungsdaten). (c) Power-Rechnung vor Freeze. (d) "0 Trades" ist INSUFFICIENT, kein Nullbefund.

## 3. Methodenempfehlungen
**Zielgröße.** Empfohlen: **Vorwärtsrendite, im Querschnitt rang-normiert** (Aktien) bzw. vol-normiert und panel-demeant (Krypto). Kein Pfad, keine Barrieren, Überlappung nur durch H. Triple-Barrier (López de Prado 2018, *Advances in Financial Machine Learning*, Wiley) nicht jetzt: Barrierebreiten und Vertikalhorizont sind Hyperparameter, jedes Setting wäre eine Hypothese. Bei Kerzen ist zudem die Reihenfolge der Barrieren innerhalb einer Kerze unbekannt. Meta-Labeling erst, wenn ein Primärsignal brutto Kante zeigt.

**CV.** Discovery: **Combinatorial Purged CV** (N = 8 Gruppen, k = 2 → 28 Splits, 7 Pfade; Pfade = C(N−1, k−1)) mit Purge = H und Embargo ≥ 21 Tage [A] (Beschreibung: Wikipedia "Purged cross-validation"; Methode: López de Prado 2018). CPCV liefert eine Verteilung statt einer Zahl. Es trainiert aber auch auf Zukunftsdaten, daher zusätzlich ein **verankerter Walk-Forward** als Pseudo-Live-Check. Bestätigung: **kein CV**. Das Modell wird eingefroren und einmal auf versiegelte Fenster angewendet. Die Empfehlung "CPCV > Walk-Forward" stammt aus der Sekundärliteratur; die Studie von Arian/Norouzi/Seco habe ich nicht verifizieren können (nicht gefunden).

**Mehrfachtest-Maße.** (i) **BH-FDR** (Benjamini/Hochberg 1995, JRSS-B 57) bleibt Pflicht. Bei starker Abhängigkeit zusätzlich Benjamini/Yekutieli 2001 als Gegenprobe. (ii) **Hansen-SPA** (JBES 2005) bzw. White Reality Check (Econometrica 2000), Benchmark = Nicht-Handeln, auf der Netto-Renditematrix aller Konfigurationen. SPA ist robuster gegen viele schlechte Zellen. (iii) **Romano-Wolf-Stepdown** (Econometrica 2005): stärkere FWER-Kontrolle mit Abhängigkeitsstruktur. (iv) **DSR** (Bailey/López de Prado 2014, JPM 40(5)): SR0 = √V[SR_k]·((1−γ)Φ⁻¹(1−1/N) + γΦ⁻¹(1−1/(Ne))), korrigiert Selektion und Nicht-Normalität. (v) **PBO** via CSCV (Bailey et al., J. Computational Finance 20(4)) braucht ≥ 8 Zellen, hat bei unseren 4 Zellen je Hypothese kaum Auflösung. Empfehlung: DSR und SPA als Filter in Discovery, BH + Romano-Wolf in Bestätigung.

## 4. Modellkomplexität und ehrliche Einschätzung
**Empfehlung: Ridge als Standard, flacher Baum (Tiefe 2, ≥ 2 000 Zeilen je Blatt) nur bei klarem Vorsprung, kein tiefes Boosting, keine neuronalen Netze.** Gründe: Unser effektives n ist klein (§6). Die Aktien-Evidenz für Nichtlinearität stammt aus 60 Jahren, ~6 200 Aktien/Monat, inkl. Small Caps (Gu/Kelly/Xiu, RFS 2020: monatliches OOS-R² OLS-3 0,16 %, Elastic Net 0,11 %, GBRT 0,34 %, RF 0,33 %, NN3 0,40 %; Kosten dort nicht behandelt). Avramov et al. (Management Science 2023): Deep-Learning-Gewinne konzentrieren sich auf schwer arbitragierbare Titel und hohe Volatilität, Kosten erodieren sie. Krauss/Do/Huck (EJOR 2017, S&P 500, 1992–2015): > 0,45 %/Tag **vor Kosten** (k = 10), "rückläufig in den letzten Jahren". McLean/Pontiff (JF 2016): Anomalie-Renditen −26 % außerhalb der Stichprobe, −58 % nach Veröffentlichung. Nagel (NBER 34104, 2025) zeigt, dass die "Tugend der Komplexität" (Kelly/Malamud/Zhou, JF 2024) im Kern ein verkleideter Momentum-Zeitfenstereffekt ist. Krypto: Cakici et al. (IRFA 2024): "begrenzter Nutzen zusätzlicher Komplexität", Vorhersagekraft kommt aus wenigen einfachen Merkmalen (Preis, Illiquidität, Momentum). Sebastião/Godinho (Financial Innovation 2021): BTC/ETH/LTC täglich, 0,5 % Roundtrip, aber nur ~325 Testtage, long-only, eine Periode.

**Urteil:** Gegenüber den einfachen Regeln wird ML bei uns **realistisch höchstens einen kleinen Zuwachs** bringen (Bündelung bekannter Kanten, kein neuer Mechanismus). Die Netto-Erwartung ist ≈ 0 [A]. Der Zuwachs muss ≥ 2–3 bp/Tag sein, um überhaupt nachweisbar zu sein, und hängt an Faktoren (Kurzfrist-Umkehr), die brutto nur +0,9…+2,7 bp/Tag zeigten. ML ist ein sauberer Test dieser Frage, kein Hebel für große Kanten. Ein ehrliches `NULLBEFUND` ist das wahrscheinlichste Ergebnis [A].

## 5. Vorregistrierbare Hypothesen

### ML-1 (Aktien)
- **Daten:** `lf2`-Tiingo, 495 Titel, Handelbarkeit und Fenster wie `RUNDE2_SPEC_v1` R1/R3. Training/Discovery nur **A (2012–2019)**.
- **Features (≈ 24, jeden Tag querschnittlich rang-normiert, kein globaler Scaler):** Umkehr (r1, r5, r10, r21), Momentum (r63, 252−21), Vol (σ21, Parkinson21, σ5/σ63, MAX21, Schiefe63), Kerze (CLV5, Range5/Range63, Overnight-Gap5, Intraday5), Liquidität (log DV60, Amihud21, v5/v63), Markt (β252, idio-Vol63, Korr63 zu SPY), 52-Wochen-Hoch-Quote. Liste und Hash vor Freeze. Preisniveau und Dollarvolumen aus **unadjustierten** `close`/`volume`.
- **Ziel:** querschnittlicher Rang der 10-Tage-Open-zu-Open-Log-Rendite (Entry Open t+1, Exit Open t+11).
- **Modell/Zellen (4, zählen gegen den Deckel 8):** Ridge α ∈ {10, 100, 1000}; GBRT (Tiefe 2, 300 Bäume, lr 0,03, subsample 0,5, min_leaf 2000).
- **Auswahl (nur A, CPCV wie §3):** höchste CPCV-Median-Netto-bp/Tag; GBRT nur, wenn ≥ 0,5 bp/Tag besser als bestes Ridge **und** DSR > 0,95 (Schwellen [A]); sonst Ridge. Gewinner wird auf ganz A gefittet und **eingefroren (kein Refit)**.
- **Regel:** täglich neue Kohorte, Long oberes / Short unteres Quintil von ŷ, Halten 10 Tage, dollar-neutral.
- **Kosten:** `lf2` R5 (4/7/12 bp × 1,25, Leihe 1,0 bp/Tag), Stress ×1,5 und Entry t+2.
- **Bestätigung:** Einmal-Lauf auf E und F. GO nur, wenn pooled E+F Netto-Mittel > 0 mit LCB95 > 0 (Blockbootstrap, Block max(20, 4H) = 40 Tage), beide Fenster Punktschätzung > 0, Placebos C3/C3b bestanden, Stress-Netto > 0, kein Einzeljahr > 50 % der Summe, BH-q = 0,05 über die Gesamtfamilie (§7) und SPA/Romano-Wolf stimmen zu. Zusätzlich Berichte je Position (Cluster-Bootstrap nach Tag).
- **Offenlegung:** Features enthalten STR/MOM. E/F sind in Aggregaten gesehen (R-H1 brutto positiv). Ein Pass ist daher nur "bestätigt unter Kontaminationsvorbehalt"; die eigentliche Bestätigung ist das vollautomatische Paper.

### ML-2 (Krypto, bedingt)
- **Daten:** Kraken OHLCVT 1h UTC, ≤ 12 USD-Paare mit Kraken-Perp (Auswahl nur nach Median-Dollarvolumen, kein Renditeblick). Fenster nach Gate-Spec §3 (HV ≥ 0,55 / LV ≤ 0,45); Training in ruhigem + hohem Regime vor den Bestätigungsfenstern; Juli–Sept 2026 als versiegeltes Vorwärtsfenster [A: unberührt, Register prüfen]. BTC-E bleibt verbraucht; ETH/SOL als Assets frisch, aber regime-korreliert.
- **Features (≈ 20):** r_1h/4h/24h/72h/168h, σ24/σ168, Parkinson, log-Volumen vs. 168-h-Median, Trade-Zahl-Schub, mittlere Tradegröße (V/N), CLV·V-Flow (24 h), Korr(r, V), Amihud, BTC-residuale Rendite. Kerzen-Zeitstempel = Bar-Beginn [A, prüfen]; Features erst ab Bar-Ende verwenden.
- **Ziel:** 24-h-Vorwärtsrendite (Open t+1 h bis t+25 h), panel-demeant, durch σ̂168 geteilt. **Modell:** Ridge, α ∈ {10, 100, 1000}, + 1 Zelle logistisch ("Vorzeichen", gleiche Merkmale) = 4 Zellen.
- **Regel:** täglich 00:00 UTC Long Top-2 / Short Bottom-2, nur Perps, Kosten 10 bp Roundtrip je Position + Funding-Stress [A, Historie nicht belegt] + Slippage +50 %.
- **Vorab-Abbruch (Pflicht, nur Discovery):** CPCV-Median-Brutto je Trade ≥ c + 0,5·MDE (≈ 10 + 10 bp) **und** erwartete Trades ≥ Power-Mindestzahl. Sonst `NICHT_GETESTET`. **Meine Erwartung: der Vorcheck scheitert** [A]; dann ist K1 (Regeln auf Volumen-Anomalien) der bessere Einsatz.
- **Entscheidungsregel Bestätigung:** wie ML-1, Fenster HV/LV, LCB95 > 0 je Trade.

## 6. Mindeststichprobe (n = z²·(σ/δ)², z = 3,34 aus α' = 0,05/8 einseitig, β = 0,2; stimmt mit SOL-Entwurf: σ 20 / δ 2 → 1 116)
| σ je Trade/Tag | n für δ = 2 bp | | Setting | Auflösung (MDE) |
|---|---|---|---|---|
| 20 bp | ≈ 1 100 | | Aktien-Portfolio, σ 40 bp/Tag, E+F 3 150 Tage, Autokorr.-Faktor 1–2 | **2,4–4,8 bp/Tag** (nur F: 3,3–6,6) |
| 50 bp | ≈ 7 000 | | Krypto 1 h, ETH, 4,8 J. | 1,2 bp, aber ρ_min 17 % |
| 200 bp | ≈ 111 500 | | Krypto 24 h, ETH / SOL (1 coin-äquivalent) | 29 / 38 bp, ρ_min 3,4 / 2,7 % |
| 300 bp | ≈ 251 000 | | Krypto 7 d, ETH | ≈ 205 bp |

**Folgerung:** 2 bp Netto-Auflösung ist mit unseren Daten bei Krypto-24-h **nicht** erreichbar und bei Aktien nur in der Nähe der Grenze (das `lf2`-δ_min 2,0 ist optimistisch). Hohes n (kurze Horizonte) läuft in die Kostenmauer, niedrige Kosten (lange Horizonte) in zu kleines n. Überlappende Labels reduzieren n_eff um den Faktor H; korrelierte Coins um K/(1+(K−1)ρ).

## 7. Mehrfachtest-Buchführung
- **Ebene 0, Trial-Register:** jeder Trainingslauf (Konfiguration, Seed, Fenster, Datum, Hash), auch Abbrüche, append-only. Jede Ablation, jede Merkmalsänderung = neue Zelle.
- **Ebene 1, Discovery:** Jede Zelle zählt gegen den Rundendeckel 8 (ML-1: 4, ML-2: 4 = 8). Hyperparameter-Raster ≤ 3 Werte je Familie, vor Datenöffnung gehasht. DSR mit N = Zellzahl (konservativ), N_eff ist nur Zusatz. Mehr als 8 Zellen = neue Runde.
- **Ebene 2, Bestätigung:** pro Hypothese geht **nur der vorab regelbasierte Gewinner** auf E/F (frische Daten, daher kein Selektionsbias der p-Werte). BH-Familie = neue Gewinner (≤ 2) **plus alle früher auf denselben Fenstern geprüften p-Werte** (Aktien: R-H1, R-H2; Krypto BTC: H1, H2). Das ist konservativ.
- **Strengere Alternative (wörtliche Lesart von D22):** alle 8 Zellen laufen in die Bestätigung, BH über m = 8 + Altlast. Weniger Power, kein Selektionsrisiko. Meine Empfehlung bleibt die Gewinner-Variante, weil die Selektion nur auf Discovery-Daten stattfindet und im Register belegt ist. **Entscheidung beim Einsatzleiter.**
- **Nach Öffnung kein Refit, keine zweite Sicht.** Feature-Importanz nur beschreibend (Permutation, Discovery).

## 8. Leckage-Fallen
Überlappung: Purge = H, Embargo ≥ 21 d, kein Trade über Fenstergrenzen. Normalisierung: nur tagesquerschnittlich, Zeitreihen-Z-Scores nur mit Fenster bis t, Winsorisieren je Tag, kein globaler Scaler/PCA. Tiingo-adjustierte Preise rückwirkend: Renditen ja, Niveaus nein. Survivorship (nur heutige S&P-Mitglieder) + Index-Look-ahead: begünstigt Umkehr-/Verlierer-Long-Signale. Merkmals- und Horizontwahl dürfen die bereits gesehenen R-H1-Aggregate nicht ausnutzen (offenlegen). Kraken-Kerzen: Zeitstempel, unvollständige letzte Kerze. Delistete Coins im Krypto-Panel [A: ob OHLCVT sie enthält, nicht geprüft].

## Quellen (abgerufen am 25.10.2026, sofern nicht anders vermerkt)
- Gu/Kelly/Xiu 2020, RFS: https://www.nber.org/papers/w25398.pdf
- Avramov/Cheng/Metzker 2023, Mgmt Sci: https://papers.ssrn.com/abstract=3450322
- Krauss/Do/Huck 2017, EJOR: https://ideas.repec.org/a/eee/ejores/v259y2017i2p689-702.html
- McLean/Pontiff 2016, JF: https://counterpointfunds.com/wp-content/uploads/2017/07/PredictabilityMcleanPontiff.pdf
- Harvey/Liu/Zhu 2016, RFS (t > 3,0): https://nber.org/papers/w20592
- Nagel 2025: https://www.nber.org/index%2ephp/papers/w34104; Kelly/Malamud/Zhou 2024: https://nber.org/system/files/working_papers/w30217/w30217.pdf (Inhalt nicht lesbar, nur Titel verifiziert)
- Cakici et al. 2024, IRFA 94:103244: https://open.icm.edu.pl/items/7566337e-2e7e-40e7-86da-413d57c313b0
- Sebastião/Godinho 2021: https://pmc.ncbi.nlm.nih.gov/articles/PMC7785332
- Bailey/López de Prado 2014 (DSR): https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551
- PBO (Bailey/Borwein/López de Prado/Zhu): https://scholarworks.wmich.edu/math_pubs/42
- Purged CV/CPCV/Embargo: https://en.wikipedia.org/wiki/Purged_cross-validation (Sekundärquelle)
- Meta-Labeling, Joubert 2022 JFDS 4(3): https://en.wikipedia.org/wiki/Meta-Labeling (Sekundärquelle)
- Romano/Wolf 2005: https://www.econometricsociety.org/publications/econometrica/browse/2005/07/01/stepwise-multiple-testing-formalized-data-snooping
- Nur aus Gedächtnis, URL nicht geprüft: White 2000 (Econometrica 68), Hansen 2005 (JBES 23), Benjamini/Hochberg 1995, Benjamini/Yekutieli 2001, López de Prado 2018 (Wiley).
