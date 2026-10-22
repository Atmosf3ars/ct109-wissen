# CT109 – ARCHIV / INDEX (alt → neu)

**Regel:** Nichts wird gelöscht oder verändert. Die Originale bleiben unverändert im Übergabe-ZIP `CT109_MODELLWECHSEL_3_BOTS_AGENTS_TRUE_2026-10-22.zip` (SHA-256 `afd708104fecdbb0fc40cec7182553909f4ede8646929b710b01ffeda6727d00`, 406 158 B). Dieser Index sagt, wo der Inhalt jeder Datei jetzt lebt. Bei Widerspruch gilt: Hostbeleg > V167 > V168 > V166-Vorderseite > V166-Anhänge.

## A. Übergabe-ZIP (14 Dateien + Index)
| Original (SHA-256, Anfang) | Rolle | Lebt jetzt in | Archiv-Status |
|---|---|---|---|
| `CT109_10_TAGE_PLAN_2026-10-20_BIS_2026-10-29.md` (`71f2370c4df4`) | Owner-Plan 19.10. | `04` (Review, Kurs); Original bleibt maßgeblich als Owner-Text | Original behalten, nicht ersetzt |
| `CT109_START_HIER_2026-10-23.md` (`df8e9e519659`) | Einstieg | `00` | ersetzt |
| `CT109_UEBERGABE_V168_MODELLWECHSEL_2026-10-23.md` (`fc648bf9ec78`) | Handbuch | `00`, `01`, `02` | ersetzt |
| `CT109_MASTERSTATUS_V167.md` (`8b95694f24e9`) | Gates 22.10. | `01` §1 | ersetzt |
| `CT109_Komponentenuebersicht_2026-10-22_V167.md` (`2570c20b7b03`) | Komponenten | `01` §1/§4 | ersetzt (Inhalt nahezu identisch mit Masterstatus V167) |
| `CT109_RELEASE_REGISTER_2026-10-22_V167.md` (`ca3b81710f77`) | Commit-/Release-Matrix | `01` §1 (Kennungen), Hashes: unten §C | ersetzt |
| `CT109_TAGESBILANZ_2026-10-22_V167.md` (`889177d6de91`) | Tagesbilanz | `01` §6 Änderungslog | ersetzt |
| `CT109_ABENDUEBERGABE_2026-10-22.md` (`7fd3981718c7`) | Abendplan (Zeitbudget) | `04` | ersetzt |
| `CT109_AGENTIC_LAB_3_BOTS_UEBERGABE_2026-10-22.md` (`0807fd2b1958`) | Lab-Rollen, Live-Abgleich-Checkliste | `01` §1 (Lab), `04` Auftrag C | ersetzt; die 7-Punkte-Checkliste im Original bleibt die Vorlage für Auftrag C |
| `CT109_SOL_PREREG_DRAFT_2026-10-21.md` (`befe0c7e238d`) | SOL-Entwurf (identisch mit `docs/` auf GitHub-main) | `03` §3/§4 (Auszug); vollständig im Repo | **Referenz behalten** (O1–O12, R1–R9, §8) |
| `CT109_MASTERSTATUS_V166.md` (`7ec2a5c0dd44`, 847 057 B) | Historie bis V165/V164 | `03`/`01` (Kernfakten); sonst Archiv | Historie; nicht als Tagesstatus lesen. Enthält u. a. §77.1 (Incident 114) und die E-132-Hürden |
| `CT109_Komponentenuebersicht_2026-10-21_V166.md` (`d8e2f0acba0e`) | Vorstatus 21.10. | Archiv | Historie |
| `CT109_RELEASE_REGISTER_2026-10-21_V166.md` (`e848674260ee`) | Vorstatus 21.10. | Archiv | Historie |
| `CT109_TAGESBILANZ_2026-10-21_V166.md` (`d35440fda8e2`) | Vorstatus 21.10. | Archiv | Historie |
| `CT109_QUELLENINDEX_SHA256_2026-10-22.md` (`e0765a221eee`) | Prüfsummen | dieser Index | ersetzt (Hashes oben bestätigt am 22.10. in der Sandbox) |

## B. Weitere hochgeladene Dateien (ältere Stände)
| Datei | Rolle | Lebt jetzt in | Status |
|---|---|---|---|
| `CT109_PROJECT.md`, `CT109_PROJECT_PROMPT.md` | Gründungsdokumente | unverändert | **unverändert maßgeblich** |
| `PROJEKTSTAND.md` (09.10., 389 Zeilen) | Entscheidungsliste E-40…E-72, Registerliste 1–46, Kosten §10, Glossar §13 | `03` §2 (Kosten), Rest im Archiv | Archiv; Glossar und E-Liste bei Bedarf dort lesen |
| `RUNBOOK.md` (alt), `README.md`, `PREREGISTRATION.md` (alt, Präfix des heutigen HEAD) | Repo-Dokumente, ältere Stände | Repo-Versionen sind maßgeblich | Archiv |
| `CT109_KRITISCHER_PROJEKTREVIEW_PRUEFAUFTRAG.md` | externer Review R01–R17 (09.10.) | `01` §5.2 (Disposition fehlt) | Archiv; **Abarbeitung offen** |
| Ältere Masterstatus-Snapshots (bis V62 und bis V139) | Historie | – | Archiv; zeilenweise in V166 enthalten (geprüft) |
| Antworten des Vorgängermodells (Übernahme-Rückfragen) | Begleitprotokoll | – | Archiv |

## C. Kennungen, die nicht verloren gehen dürfen
- Prod `main` lokal `d2b1efc5c9156d09a8dad5896bfdd3fc2016b395`; GitHub-main `13d58ad38e40b81a5675edf05e2f154540973e25` (PR #12).
- V142: `889b52cefcb1a2f2db60dd429d80728a2cdb4c62`, Branch `rc/futures-l2-integ3-2026-10-19`.
- BTC/ETH-L2-RC `66b4b0b`; SSD-Pfad A `9d29b94`; Lernbot Slot 0 `4db7110` (alle nur V166-Berichte, L1).
- `archive.py` SHA-256 `494cff0dc4ec42ea834e79def059b4d55de506e707581c156e9d7a5973ea9e67`.
- `PREREGISTRATION.md` lokal (Prod) SHA-256 `354df567fd6d9e0df56bef4d0a681bcf3ce7e42df3e3cc4777912c1564667adb`, letzter Dokumentcommit `313be8fed1b4b32431b1be6e5310e7ef9f628654`.
- E-129-Wortlaut: Projektchat 11.10. `https://claude.ai/chat/1d9a9527-9ba3-4168-aac6-24ae66ad143e`.
- Code-Prüfstand dieser Konsolidierung: Repo `Atmosf3ars/new-signal-system` @ `13d58ad`.

## D. Nachtrag: `pc_downloads.zip` (38 MD-Dateien, vom Owner gefunden, 22.10. abends)
Nur Markdown, **kein Code** – es gibt dort keine unveröffentlichte Entwicklung. Hash-Abgleich gegen ZIP/Repo/Uploads:
- **Bereits bekannt (identisch):** BLUEPRINT, README, RUNBOOK, PROJEKTSTAND, PROJECT, PROJECT_PROMPT, KRITISCHER_PROJEKTREVIEW, 10-Tage-Plan, SOL-Entwurf, Masterstatus V62/V139/V166, Komponentenübersicht/Register/Tagesbilanz V166. `PREREGISTRATION.md` ist der **Prod-lokale Stand** (SHA `354df567…`, ohne SOL-Nachtrag).
- **Ältere Stände (nur Historie):** Masterstatus V164 und V165, Komponentenübersicht 19.10./V164/V165, Release-Register V164/V165, Tagesbilanz V165, `CT109_MASTERSTATUS.md` (17.10.), `uebergabe_neues_signalsystem.md` (17.10.), `uebergabe-neues-system.md` (23.09.). `ARCHITECTURE.md` hier hat 619 Zeilen und ist **älter** als die Repo-Version (714 Zeilen, enthält Archiv-Stufe-1-Nachtrag 11.10.) – Repo gilt.
- **Altes Trading-Dashboard (CT107, nicht CT109):** `SPEC.md`, `SPEC-EXT.md`, `DECISIONS.md` (D1…, 221 KB), `BACKLOG.md`, `blueprint-paket-c.md`, `blueprint-paket-c2.md`, `ergebnis_paket_c.md`, `ergebnis_pruefauftrag_news_earnings.md`. Kein Bestandteil des neuen Systems; nur Vorgeschichte (Konfluenz-Framework).
- **Neues System, nur Entwurf:** `ergebnis.md` (03.10., Entwurf Schattenbot Ebene C; nichts gebaut). Die umgesetzte Fassung ist der Lernbot (`docs/LERNBOT_DESIGN.md` im Repo).
Der E-129-Wortlaut und V167/V168 stehen **nicht** darin. Nach `ARCHIV/` verschieben, nichts löschen.
