#!/bin/bash
# ibkr_alert_off_v1.sh - schaltet NUR den Feed-Alarm fuer ibkr ab (SUPPRESSED_FEEDS = {"ibkr"}, wie im Code dokumentiert) und startet signal-alerting neu.
# Aendert genau eine Zeile in monitor.py (Backup vorher), loescht nichts, liest keine Secrets.
set -u
F=/opt/new-signal-system/src/alerting/monitor.py
B=/root/monitor.py.bak-ibkr-alert-20261030
echo "== vorher =="; date -u; grep -n '^SUPPRESSED_FEEDS' "$F"; systemctl is-active signal-alerting
n=$(grep -c '^SUPPRESSED_FEEDS: set\[str\] = set()$' "$F")
if [ "$n" != "1" ]; then echo "ABBRUCH: erwartete Zeile nicht genau einmal ($n), nichts geaendert"; exit 1; fi
cp -p "$F" "$B" || { echo "ABBRUCH: Backup fehlgeschlagen"; exit 1; }
sed -i 's/^SUPPRESSED_FEEDS: set\[str\] = set()$/SUPPRESSED_FEEDS: set[str] = {"ibkr"}  # D66 2026-10-30: IBKR beendet, Alarm aus/' "$F"
chown --reference="$B" "$F"; chmod --reference="$B" "$F"
if ! runuser -u signalsvc -- env PYTHONPATH=/opt/new-signal-system/src PYTHONDONTWRITEBYTECODE=1 /opt/new-signal-system/.venv/bin/python -c 'import alerting.monitor as m; print("SUPPRESSED_FEEDS =", m.SUPPRESSED_FEEDS)'; then
  echo "FEHLER beim Import -> Rollback"; cp -p "$B" "$F"; exit 1
fi
systemctl restart signal-alerting; sleep 5
echo "== nachher =="; date -u; grep -n '^SUPPRESSED_FEEDS' "$F"; systemctl is-active signal-alerting
echo "-- Git-Stand (Datei ist jetzt geaendert) --"; git -C /opt/new-signal-system status --short
echo "-- Journal signal-alerting, letzte 2 min --"; journalctl -u signal-alerting --since "-2min" --no-pager | tail -n 8
echo "Ergebnis: fertig (Rollback: cp -p $B $F; systemctl restart signal-alerting)"
