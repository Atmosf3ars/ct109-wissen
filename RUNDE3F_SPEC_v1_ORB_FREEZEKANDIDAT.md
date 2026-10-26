# CT109 – RUNDE 3F SPEC v1 – ORB (Opening Range Breakout, „Stocks in Play“) – FREEZE-KANDIDAT (HINWEIS-Klasse)

**Stand:** Mo 26.10.2026 ≈ 19:00 Berlin. Auftrag: Andi „orb mit 2020 – 2026“. **Kein α-Verbrauch** (HINWEIS-Klasse, Regel 2: erwartete Netto-Kante ≤ 0 < Nachweisgrenze), α-Konto bleibt 7/20 (D37). Evidenz: Zahlen aus dem Entwicklungsfenster sind [G] (Roh in `register/results/`), Erwartungen [A].

## 1 Hypothese und Vorbefund
**H:** Die Richtung der ersten 5-Minuten-Kerze (09:30–09:35 ET) von US-Aktien mit ungewöhnlich hohem Eröffnungsvolumen (Top-20 je Tag nach RV5) sagt die Tagesrichtung so voraus, dass ein Breakout-Trade nach Provision und Slippage einen positiven Erwartungswert hat (Zarattini/Barbon/Aziz, Working Paper).
**Vorbefund (Entwicklungsfenster 2016–2019, `03` §8.31, D63) [G]:** brutto +0,056 R, aber Zufallsrichtung +0,068 R (Differenz −0,009 R), 10:30-Placebo +0,113 R; ohne Stops +4,5 bp (SE 2,4); netto −0,014 R (s = 0) / −0,163 R (s = 5 bp). **Erwartung für das Testfenster: ≤ 0.** Zweck des Laufs: unabhängige Bestätigung/Widerlegung in einem anderen Regime (2020–2026H1: Corona-Crash, Retail-Boom 2021, Bärenjahr 2022, Zinswende) und endgültiger Abschluss der Familie.

## 2 Daten (alle lokal auf Andis PC, nur Aggregate in den Chat)
- Tagesbars (Alpaca SIP, adjustment=all): `alpaca-daily-full` + `alpaca-daily`, 13 402 Symbole inkl. 5 339 beendeter; Eligible-Filter (Vortagesschluss ≥ 5 USD, ATR14 ≥ 0,5 USD, Vol14 ≥ 1 Mio., Lücke ≤ 5 Kalendertage) wie in `orb_count_v2.py`.
- Erste 5-Min-Kerze aller Eligible-Symbol-Tage (`alpaca_intraday_v1.py first`, adjustment=split, SIP) und Ganztags-5-Min-Bars der Top-20 (`alpaca_day5_v1.py`).
- **Testfenster:** 2020-01-02 … 2026-06-30 (Datenende hart 2026-06-30; ab 2026-07-01 gesperrt). Das Fenster wird **einmal** geöffnet. Das Entwicklungsfenster 2016–2019 ist verbraucht.
- Survivorship: Universum aus Alpaca-Assets (aktiv+inaktiv, ohne OTC/Warrants) plus alle Form-3/4/5-Ticker; 79 % der beendeten Symbole eines Referenzbestands fehlten in den Assets ⇒ Form-4-Ergänzung; vollständige Delisting-Liste fehlt weiter ⇒ Rest-Verzerrung unbekannt [A].

## 3 Regel (fest, keine Änderung nach Freeze)
Auswahl: je Tag Top-**20** nach RV5 = Volumen der ersten Kerze / Mittel der 14 Vortage (≥ 10 vorhanden), Doji ausgeschlossen (`orb_select_v2.py`, Gleichstand nach Symbol). Signal: 09:30-Kerze; Long bei Close > Open, Short bei Close < Open. Einstieg Open der nächsten vorhandenen Bar; Stop am Gegenende der Signalkerze; Ziel 10 R; sonst Schluss (letzte Bar); Stop vor Ziel in derselben Bar; Lücke durch den Stop ⇒ Füllung zum Open; Entry jenseits des Stops ⇒ kein Trade. Kosten: Provision 0,70 USD je Round-Trip bei Ticket 1 500 USD; Slippage **5 bp je Seite (primär)**, 0 und 10 bp berichtet. **Alle Parameter stammen aus dem Paper bzw. sind vor dem Testfenster gesetzt; im Entwicklungsfenster wurde nichts „optimiert“** (K=5/10/60, Ziel 3 R/ohne, Risikofilter wurden nur gesichtet und gehen nicht ein).

## 4 Kennzahlen und Kriterien (`orb_test_v1.py`, Modus `final`)
Primär: mittleres Netto-R je Trade (s = 5 bp). SE: Tagesblock-Bootstrap (zirkuläre Blöcke à 5 Handelstage, 10 000 Ziehungen, Seed 20261026); z_adj = m / (1,3 · SE) [Aufschlag 1,3 ohne eigene Nullwelten, vorsorglich [A]]. **Kategorie HINWEIS-POSITIV nur wenn alle vier gelten:** (i) n ≥ 20 000 Trades (sonst INSUFFICIENT), (ii) Netto-R(s=5) > 0 mit z_adj ≥ 1,645, (iii) **Richtungswert** (Kerzenrichtung minus Mittel beider Richtungen, brutto, gleiche Stop-Geometrie, nur beidseitig handelbare Trades) > 0 mit z_adj ≥ 1,645, (iv) beide Hälften (2020–2022, 2023–2026H1) Netto-R > 0. Sonst **NICHT NACHWEISBAR**. Nur berichtet: Brutto, s = 0/10, Jahre, Long/Short, K=5/10, Zeitversatz-Placebo 10:30, Diagnose ohne Stops. Es gibt **kein BESTAETIGT** (kein α).

## 5 Power-Zeile (Regel 2)
Erwarteter Umfang ≈ 32 000 Trades (1 632 Tage × 20). MDE70 je Trade 0,04–0,10 R (σ 1,5–2,5 R, ρ_Tag 0,05–0,20, `03` §8.30). **Erwartete Netto-Kante ≈ −0,014 … −0,163 R ≤ MDE ⇒ HINWEIS-Klasse.** Wahrscheinlichstes Ergebnis: NICHT NACHWEISBAR mit negativer Punktschätzung. Nutzen: Familie sauber abschließen; ein überraschend positives Ergebnis wäre nur ein Hinweis für Vorwärtsbeobachtung, kein Beleg.

## 6 Ablauf
1. GO FREEZE-ORB (Andi) → Registerzeile. 2. `run_orb_data.ps1` (Andi): Tool-Hashes prüfen, Testfenster-Daten laden (erste Kerzen ≈ 1,6 h, Auswahl, Ganztags-Bars ≈ 0,4 h; mit Wiederaufnahme). 3. `run_orb_final.ps1` (Andi): Tool-Hashes prüfen, Datenmanifest der Testfenster-Dateien schreiben (Hash wird im Ergebnis registriert), Lauf **einmal**. 4. Einsatzleiter: Ergebnis registrieren (nur mit zweitem GO nach Schablone), `01`–`04` aktualisieren.

## 7 Risiken
Datenabruf bei Alpaca kann nachträgliche Korrekturen enthalten (Datenmanifest hält den Stand fest); Slippage-Annahme (5 bp) ist eine Annahme, keine Messung; kein Spread-/Quote-Test; Ticker-Wiederverwendung; Rate-Limit 150/200 Abrufe/min (Lauf von ≈ 2 h); Paper-Literatur überschneidet sich mit 2020–2023 (Hypothese ist literaturbekannt, nicht erst durch unsere Daten gefunden).
