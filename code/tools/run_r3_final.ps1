# run_r3_final.ps1 - EINMALIGER Haupttest-Lauf Welle 3 (K4, K4P, K6). Nur nach GO FREEZE-R3 - 830bac6d.
# Prueft zuerst alle Code-Hashes gegen das Freeze-Manifest und bricht bei Abweichung ab. Ausgabe nur Aggregate.
$ErrorActionPreference = "Stop"
$freeze = "830bac6d59d10756c6ecd338270e083b4ccf1b74366a126f19eb27c67077a2a2"
$agg = "D:\CT109-Data\kraken-trades\agg"
Set-Location D:\CT109-Data\kraken-trades\tools
$expected = @{
    "k4_test_v1.py" = "d253f1a66c39003726f555645b15d60f339f1c693da08b15dfb68de6f0c3b1f5"
    "k6_test_v1.py" = "b715f5fa4fdfa6ef4ce15ba464be608aaa74283b406e1fc086aa6561d952ef8e"
    "count_events_v2.py" = "a2588ea0c3d3a8561ba11757fcb704fcc645fc55ca94f690944d89027412dc3d"
    "count_events_v3.py" = "6a93ec86fbfd846119cec77e1d87711d62518c40c4ee08b80a279ec9207fc936"
    "count_events_v4.py" = "931e1850c054fe780567dfb99cc8dc4a8a5cc68e022855198ff9bc6beef764f6"
    "count_cs_v1.py" = "81e2550ad6b716df0ebb3c3145bc7f24c37243ebb9651d1daaedcde375a77215"
}
$bad = 0
foreach ($k in $expected.Keys) {
    $h = (Get-FileHash -Algorithm SHA256 -Path $k).Hash.ToLower()
    if ($h -ne $expected[$k]) { Write-Host "ABWEICHUNG $k : $h"; $bad = 1 } else { Write-Host "ok $k" }
}
if ($bad -eq 1) { Write-Host "ABBRUCH: Code weicht vom Freeze ab. Kein Lauf."; exit 1 }
if (Test-Path r3_final_k4.txt) { Write-Host "ABBRUCH: r3_final_k4.txt existiert bereits (Fenster nur einmal oeffnen)."; exit 1 }
$k4p = "SOL,XRP,XDG,ADA,LTC,DOT,LINK,XMR,ZEC,XLM,BCH,ATOM,SUI,PEPE,AVAX,TAO,FIL,UNI,TRX,AAVE,FET,NEAR,DASH,CRV,ICP,FARTCOIN,INJ,PENGU,ONDO,SEI,TIA,TRUMP"
$k6 = "XBT,ETH,SOL,XRP,XDG,ADA,LTC,DOT,LINK,XMR,ZEC,XLM,BCH,ATOM,SUI,PEPE,AVAX,TAO,FIL,UNI,TRX,AAVE,FET,NEAR,DASH,CRV,ICP,FARTCOIN,INJ,PENGU,ONDO,SEI,TIA,TRUMP"
python -u k4_test_v1.py final $agg "XBT,ETH" --spec-hash $freeze *> r3_final_k4.txt
Get-Content r3_final_k4.txt
python -u k4_test_v1.py final $agg $k4p --spec-hash $freeze *> r3_final_k4p.txt
Get-Content r3_final_k4p.txt
python -u k6_test_v1.py final $agg $k6 --spec-hash $freeze *> r3_final_k6.txt
Get-Content r3_final_k6.txt
