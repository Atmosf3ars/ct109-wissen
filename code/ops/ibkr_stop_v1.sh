#!/bin/bash
# ibkr_stop_v1.sh - stoppt und deaktiviert NUR die IBKR-Einheiten auf CT109. Loescht nichts, aendert keine Dateien, liest keine Secrets.
set -u
U="signal-ibkr-watch.timer signal-ibkr-watch.service signal-ibkr.service ibgateway.service"
echo "== vorher =="; date -u
for u in $U; do printf '%s active=%s enabled=%s\n' "$u" "$(systemctl is-active "$u" 2>&1)" "$(systemctl is-enabled "$u" 2>&1)"; done
echo "-- nicht betroffen (nur Anzeige) --"
systemctl list-units 'signal-*' --all --no-pager --plain --no-legend | awk '{print $1,$3,$4}' | grep -v ibkr
for u in $U; do
  if systemctl cat "$u" >/dev/null 2>&1; then echo "$u:"; systemctl disable --now "$u" 2>&1 | tail -n 1; else echo "$u: nicht vorhanden, uebersprungen"; fi
done
systemctl reset-failed $U 2>/dev/null
echo "== nachher =="; date -u
for u in $U; do printf '%s active=%s enabled=%s\n' "$u" "$(systemctl is-active "$u" 2>&1)" "$(systemctl is-enabled "$u" 2>&1)"; done
echo "-- Rest (soll Kraken usw. weiter active zeigen) --"
systemctl list-units 'signal-*' --all --no-pager --plain --no-legend | awk '{print $1,$3,$4}' | grep -v ibkr
echo "-- fehlgeschlagene Einheiten --"; systemctl --failed --no-pager --plain --no-legend | awk '{print $1}'
echo "Ergebnis: fertig (bei Abweichung Ausgabe an Claude)"
