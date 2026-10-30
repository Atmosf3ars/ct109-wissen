#!/bin/bash
# ibkr_host_sync_v1.sh - gleicht /opt/new-signal-system mit main nach PR #13 ab (Hotfix-Zeile in monitor.py wird durch den Repo-Stand ersetzt). Nur fast-forward, nur wenn genau 6 Commits mit genau diesen 7 Dateien hereinkommen (PR #13 + zwei Doku-Commits SOL-O1 + Merge #12).
# Loescht nichts, liest keine Secrets. Danach nur signal-alerting neu starten.
set -u
R=${REPO:-/opt/new-signal-system}; F=src/alerting/monitor.py; B=${BACKUP:-/root/monitor.py.bak-sync-20261030}
echo "== vorher =="; date -u; git -C "$R" rev-parse --short HEAD; git -C "$R" status --short; grep -n '^SUPPRESSED_FEEDS' "$R/$F"
git -C "$R" fetch -q origin main || { echo "ABBRUCH: fetch fehlgeschlagen, nichts geaendert"; exit 1; }
if ! git -C "$R" merge-base --is-ancestor HEAD origin/main; then echo "ABBRUCH: HEAD ist kein Vorfahre von origin/main, nichts geaendert"; exit 1; fi
n=$(git -C "$R" rev-list --count HEAD..origin/main)
echo "-- kommt herein ($n Commits) --"; git -C "$R" log --oneline HEAD..origin/main
if [ "$n" != "6" ]; then echo "ABBRUCH: erwartet genau 6 Commits, nichts geaendert"; exit 1; fi
exp="PREREGISTRATION.md docs/CT109_SOL_PREREG_DRAFT_2026-10-21.md src/alerting/ibkr_watch.py src/alerting/monitor.py tests/conftest.py tests/test_alerting.py tests/test_alerting_suppress.py"
got=$(git -C "$R" diff --name-only HEAD origin/main | sort | tr '\n' ' ' | sed 's/ $//')
want=$(echo $exp | tr ' ' '\n' | sort | tr '\n' ' ' | sed 's/ $//')
if [ "$got" != "$want" ]; then echo "ABBRUCH: unerwartete Dateien: $got"; exit 1; fi
others=$(git -C "$R" status --porcelain --untracked-files=no | grep -v " $F\$" | wc -l)
if [ "$others" != "0" ]; then echo "ABBRUCH: weitere lokale Aenderungen ausser $F, nichts geaendert"; exit 1; fi
cp -p "$R/$F" "$B" || { echo "ABBRUCH: Backup fehlgeschlagen"; exit 1; }
git -C "$R" checkout -- "$F" && git -C "$R" merge --ff-only -q origin/main || { echo "FEHLER beim Abgleich -> Hotfix wiederherstellen"; cp -p "$B" "$R/$F"; exit 1; }
if ! runuser -u signalsvc -- env PYTHONPATH="$R/src" PYTHONDONTWRITEBYTECODE=1 "$R/.venv/bin/python" -c 'import alerting.monitor as m, alerting.ibkr_watch as w; print("SUPPRESSED_FEEDS =", m.SUPPRESSED_FEEDS)'; then
  echo "FEHLER beim Import -> Rollback auf vorherigen Stand"; git -C "$R" reset -q --hard ORIG_HEAD; cp -p "$B" "$R/$F"; exit 1
fi
systemctl restart signal-alerting; sleep 5
echo "== nachher =="; date -u; git -C "$R" rev-parse --short HEAD; git -C "$R" status --short; grep -n '^SUPPRESSED_FEEDS' "$R/$F"; systemctl is-active signal-alerting
echo "-- Journal signal-alerting, letzte 2 min --"; journalctl -u signal-alerting --since "-2min" --no-pager | tail -n 6
echo "Ergebnis: fertig (Rollback: git -C $R reset --hard ORIG_HEAD; cp -p $B $R/$F; systemctl restart signal-alerting)"
