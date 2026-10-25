$agg = "D:\CT109-Data\kraken-trades\agg"
$csv = "SOL,XRP,XDG,ADA,LTC,DOT,LINK,XMR,ZEC,XLM,BCH,ATOM,SUI,PEPE,AVAX,TAO,FIL,UNI,TRX,AAVE,FET,NEAR,DASH,CRV,ICP,FARTCOIN,INJ,PENGU,ONDO,SEI,TIA,TRUMP"
$pairs = $csv.Split(",")
Set-Location D:\CT109-Data\kraken-trades\tools
python -u count_events_v3.py $agg @pairs *> k4pf_count.txt
$m = Select-String -Path k4pf_count.txt -Pattern "Streuung 4-h \(alle Einstiege, zentriert\) (\d+) bp"
if (-not $m) { Write-Host "FEHLER: Streuungszeile nicht gefunden"; exit 1 }
$sd = $m.Matches[0].Groups[1].Value
Write-Host "gezaehlte Streuung je Einstieg (K4P, gefilterter Pool): $sd bp"
Get-Content k4pf_count.txt | Select-String "K4P vereinigt|je Zustand|je Jahr|innerhalb|Tage mit Einstieg|Streuung 4-h"
python -u k4_test_v1.py calib $agg $csv --sigma $sd *> calib_k4pf.txt
Get-Content calib_k4pf.txt
