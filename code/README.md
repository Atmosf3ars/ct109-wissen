# code/ – Bau-Code (nur Code, keine Daten, keine Schlüssel)

Unveränderte Auszüge der geprüften Pakete (Dateien = ZIP-Inhalt). Die Hashes unten sind die maßgeblichen; bei Abweichung gilt das ZIP auf `D:\CT109-Bau`.

| Ordner | Zweck | ZIP-SHA-256 | `code_hash` (`<paket>/*.py`) |
|---|---|---|---|
| `lf1_v0.6.0/` | Krypto: Freeze, Stufe D/B, Paper-Runner (`deploy/`) | `fd110abe…f355` (voller Hash in `01`) | `901f6e0a3086184cb55952dbdcda195f03aa0fba2fd8588b14de3be01edbdaa6` (= Freeze, = laufender Runner) |
| `lf2_v0.3.0/` | US-Aktien Runde 2: Universum, Abruf, Q-Zähler, Gate S, Freeze, Stufen | `d0b84c74afc9d8dc231219211c1ddb31e144931cbf73b66dd2df4e284472c84b` | `de89780bc341680ddf22fdf5aaa643c8a8676290889029f319dcea8376128590` |

Prüfen: im Paketordner `python -m lf1 selfcheck` bzw. `python -m lf2 selfcheck`. Tests: `python -W ignore -m unittest discover -s tests` (lf2: `-p "test_lf2_*.py"`).

**Regeln:** Dateien hier nie ändern, sonst ändert sich der Code-Hash, der in Freeze/Manifest steht. Neue Version = neuer Ordner (alte bleiben als gehashte Vorgeschichte). Rohkursdaten (Tiingo) gehören nie hierher (Lizenz „Internal Use Only“).
