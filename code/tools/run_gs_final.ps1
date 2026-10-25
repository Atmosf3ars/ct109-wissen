# run_gs_final.ps1 - EINMALIGER Lauf GOLD-SILBER (HINWEIS-Klasse). Nur nach GO FREEZE-GS (siehe FREEZE_PAKET_GS_v1.md).
# Prueft Code- und Datenhashes gegen das Freeze-Manifest, bricht bei Abweichung ab. Ausgabe nur Aggregate.
$ErrorActionPreference = "Stop"
$freeze = "405f212563447712aec313b8cf659bbc8b29208bd2924b9e33595ebb014f1b0a"
Set-Location D:\CT109-Data\kraken-trades\tools
$expected = @{
    "gs_test_v1.py"  = "008b120b1e763a6e942614fa0621f8fd64aaffaba4691d15937a62bb6009f330"
    "count_gs_v1.py" = "1af5deb5a5cd8b3605100d3ae1c3cc203d786d465ed8a44634830f73d4f6db3f"
}
$data = @{
    "D:\CT109-Data\alpaca-daily\GLD.csv" = "b9adc93e9faafa0e86b56f4fcd625a307dc80fd769efd6e164fdff4b6c0a9df7"
    "D:\CT109-Data\alpaca-daily\SLV.csv" = "366d33c6987a17eeef9bb0151fb61854abb325b6e954e51980a40e49cc5022e5"
}
$bad = 0
foreach ($k in $expected.Keys) { $h = (Get-FileHash -Algorithm SHA256 -Path $k).Hash.ToLower(); if ($h -ne $expected[$k]) { Write-Host "ABWEICHUNG $k : $h"; $bad = 1 } else { Write-Host "ok $k" } }
foreach ($k in $data.Keys) { $h = (Get-FileHash -Algorithm SHA256 -Path $k).Hash.ToLower(); if ($h -ne $data[$k]) { Write-Host "ABWEICHUNG $k : $h"; $bad = 1 } else { Write-Host "ok $k" } }
if ($bad -eq 1) { Write-Host "ABBRUCH: Code/Daten weichen vom Freeze ab. Kein Lauf."; exit 1 }
if (Test-Path gs_final.txt) { Write-Host "ABBRUCH: gs_final.txt existiert bereits (Fenster nur einmal oeffnen)."; exit 1 }
python -u gs_test_v1.py final D:\CT109-Data\alpaca-daily --spec-hash $freeze *> gs_final.txt
Get-Content gs_final.txt
