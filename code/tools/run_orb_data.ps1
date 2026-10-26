# run_orb_data.ps1 - ORB Testfenster-Daten laden (2020-01-02 .. 2026-06-30). NUR nach GO FREEZE-ORB (siehe FREEZE_PAKET_ORB_v1.md). Schluessel als Umgebungsvariablen.
# Prueft Code-Hashes gegen das Freeze-Manifest, laedt dann (mit Wiederaufnahme): erste 5-Min-Kerzen, Auswahl Top-20, Ganztags-Bars. Keine Auswertung.
$ErrorActionPreference = "Stop"
$freeze = "662a156fce8a3c432676a21967d8bb9712597daf4cafb2e6db7b70ec576b336d"
Set-Location D:\CT109-Data\kraken-trades\tools
$code = @{
    "orb_test_v1.py" = "13ca0ccdad9c298f8ba321ea9dd5c45c8cde8aeb0834fe0cb89ca356f228b0d8"
    "orb_select_v2.py" = "d5ae2b7201345ebd6140104afdf46b76527a4f7f641931f7b6243789f6ccb994"
    "alpaca_intraday_v1.py" = "97ffec6535a4fddd761e994e06d1382132cdfd308304cab04b69d24b63981647"
    "alpaca_day5_v1.py" = "0d1e64c4402de81bc56d184b9c278450f7ff5f5e74b9246db424100c469f007f"
    "alpaca_daily_v1.py" = "143a43a382bba8b451233597ec4519b8ca091dd4cb8caeddac80165c8e00ca0b"
}
$bad = 0
foreach ($k in $code.Keys) { $h = (Get-FileHash -Algorithm SHA256 -Path $k).Hash.ToLower(); if ($h -ne $code[$k]) { Write-Host "ABWEICHUNG $k : $h"; $bad = 1 } else { Write-Host "ok $k" } }
if ($bad -eq 1) { Write-Host "ABBRUCH: Code weicht vom Freeze ab."; exit 1 }
python -u alpaca_intraday_v1.py first --daily D:\CT109-Data\alpaca-daily-full --daily D:\CT109-Data\alpaca-daily --out D:\CT109-Data\alpaca-first5 --from 2020-01-02 --to 2026-06-30 --allow-test | Tee-Object orb_test_first_out.txt
python -u orb_select_v2.py D:\CT109-Data\alpaca-first5 D:\CT109-Data\alpaca-first5\_orb_sel_test_k20.csv --from 2020-01-02 --to 2026-06-30 --k 20 | Tee-Object orb_test_select_out.txt
python -u alpaca_day5_v1.py D:\CT109-Data\alpaca-first5\_orb_sel_test_k20.csv --out D:\CT109-Data\alpaca-day5-test --allow-test | Tee-Object orb_test_day5_out.txt
Write-Host "Datenlauf beendet. Wenn alle drei Schlusszeilen 'Fehltage 0' zeigen: run_orb_final.ps1 starten."
