$agg = "D:\CT109-Data\kraken-trades\agg"
$csv = "XBT,ETH,SOL,XRP,XDG,ADA,LTC,DOT,LINK,XMR,ZEC,XLM,BCH,ATOM,SUI,PEPE,AVAX,TAO,FIL,UNI,TRX,AAVE,FET,NEAR,DASH,CRV,ICP,FARTCOIN,INJ,PENGU,ONDO,SEI,TIA,TRUMP"
$pairs = $csv.Split(",")
Set-Location D:\CT109-Data\kraken-trades\tools
python -u count_events_v4.py $agg @pairs *> k6f_count.txt
$m = Select-String -Path k6f_count.txt -Pattern "m=20\.0 i=0\.7:.*sd (\d+) bp"
if (-not $m) { Write-Host "FEHLER: sd-Zeile nicht gefunden"; exit 1 }
$sd = $m.Matches[0].Groups[1].Value
Write-Host "gezaehltes sd je Einstieg (Raster 20/0.7, gefilterter Pool): $sd bp"
python -u k6_test_v1.py calib $agg $csv --sigma $sd *> calib_k6f.txt
Get-Content k6f_count.txt | Select-String "m=20.0 i=0.7"
Get-Content calib_k6f.txt
