# run_orb_final.ps1 - EINMALIGER Lauf ORB (HINWEIS-Klasse). NUR nach GO FREEZE-ORB und vollstaendigem run_orb_data.ps1.
# Prueft Code-Hashes, schreibt das Datenmanifest der Testfenster-Dateien (Hash wird im Ergebnis registriert) und fuehrt den Test genau einmal aus.
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
if (Test-Path orb_final.txt) { Write-Host "ABBRUCH: orb_final.txt existiert bereits (Fenster nur einmal oeffnen)."; exit 1 }
$done = (Get-Content D:\CT109-Data\alpaca-first5\_done_days.txt | Where-Object { $_ -ge "2020-01-01" }).Count
$done5 = (Get-Content D:\CT109-Data\alpaca-day5-test\_done_days.txt).Count
Write-Host "Testtage erste Kerzen: $done | Ganztagstage: $done5 (erwartet je ca. 1631)"
if ($done -lt 1600 -or $done5 -lt 1600) { Write-Host "ABBRUCH: Datenlauf unvollstaendig."; exit 1 }
$files = @()
$files += Get-ChildItem D:\CT109-Data\alpaca-first5 -Filter "first5_*.csv" | Where-Object { $_.Name -match "^first5_202[0-9]-" }
$files += Get-Item D:\CT109-Data\alpaca-first5\_orb_sel_test_k20.csv
$files += Get-ChildItem D:\CT109-Data\alpaca-day5-test -Filter "day5_*.csv"
$lines = foreach ($f in ($files | Sort-Object FullName)) { (Get-FileHash -Algorithm SHA256 -Path $f.FullName).Hash.ToLower() + "  " + $f.Name }
$lines | Out-File -Encoding ascii orb_test_data_manifest.txt
$mh = (Get-FileHash -Algorithm SHA256 -Path orb_test_data_manifest.txt).Hash.ToLower()
Write-Host "Datenmanifest: $($lines.Count) Dateien, Hash $mh"
python -u orb_test_v1.py final D:\CT109-Data\alpaca-day5-test D:\CT109-Data\alpaca-first5\_orb_sel_test_k20.csv --spec-hash $freeze 2>&1 | Out-File -Encoding utf8 orb_final.txt
Get-Content orb_final.txt
Write-Host "Datenmanifest-Hash: $mh"
