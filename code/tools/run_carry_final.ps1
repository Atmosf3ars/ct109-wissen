# run_carry_final.ps1 - EINMALIGER Lauf CARRY-HOLD (HINWEIS-Klasse). Nur nach GO FREEZE-CARRY (siehe FREEZE_PAKET_CARRY_v1.md).
# Prueft Code- und alle Datenhashes gegen das Freeze-Manifest, bricht bei Abweichung ab. Ausgabe nur Aggregate.
$ErrorActionPreference = "Stop"
$freeze = "72a5c862d2268de6a71126481710179c33b9681b513f9cc8304878c52c256b37"
Set-Location D:\CT109-Data\kraken-trades\tools
$code = @{
    "carry_test_v1.py"             = "5e0554a122d2d280bb8b382262e4e362f09d0f1e9491003cf31ab035b7b10f84"
    "MANIFEST_CARRY_DATA_SHA256.txt" = "19bfc1948281c23a32be1b061ea75ed9451c74c7551575a3eaeec387b949a105"
}
$bad = 0
foreach ($k in $code.Keys) { $h = (Get-FileHash -Algorithm SHA256 -Path $k).Hash.ToLower(); if ($h -ne $code[$k]) { Write-Host "ABWEICHUNG $k : $h"; $bad = 1 } else { Write-Host "ok $k" } }
$n = 0
foreach ($line in Get-Content MANIFEST_CARRY_DATA_SHA256.txt) {
    if ($line.Trim().Length -eq 0) { continue }
    $parts = $line -split "\s+", 2; $hash = $parts[0].ToLower(); $name = $parts[1].Trim().TrimStart("*")
    if ($name -like "*.zip") { $p = Join-Path "D:\CT109-Data\binance-klines" $name } else { $p = Join-Path "D:\CT109-Data\funding-binance" $name }
    $h = (Get-FileHash -Algorithm SHA256 -Path $p).Hash.ToLower(); $n++
    if ($h -ne $hash) { Write-Host "ABWEICHUNG $p : $h"; $bad = 1 }
}
Write-Host "Datendateien geprueft: $n (erwartet 322)"
if ($n -ne 322) { $bad = 1 }
if ($bad -eq 1) { Write-Host "ABBRUCH: Code/Daten weichen vom Freeze ab. Kein Lauf."; exit 1 }
if (Test-Path carry_final.txt) { Write-Host "ABBRUCH: carry_final.txt existiert bereits (Fenster nur einmal oeffnen)."; exit 1 }
python -u carry_test_v1.py final D:\CT109-Data\binance-klines D:\CT109-Data\funding-binance --spec-hash $freeze *> carry_final.txt
Get-Content carry_final.txt
