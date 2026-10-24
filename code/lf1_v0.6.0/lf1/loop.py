"""Stundenschleife des Runners. Alle Abhaengigkeiten (Abruf, Uhr, Schlaf) sind einsetzbar, damit sie ohne Netz testbar ist."""
HOUR = 3600
OFFSET_S = 20          # Abruf kurz nach Barbeginn
RETRY_S = 45
RETRIES = 3


def next_fetch_ts(now):
    """Naechster Abrufzeitpunkt (Stundenbeginn + OFFSET_S), strikt nach `now`."""
    base = (int(now) // HOUR) * HOUR
    t = base + OFFSET_S
    return t if t > now else t + HOUR


def run_cycle(runner, assets, fetch, clock, sleep, fetch_tickers=None):
    """Ein Zyklus: Kerzen je Asset holen und einspeisen; Fehler werden gezaehlt und geloggt, nie verschluckt."""
    for asset in assets:
        for attempt in range(RETRIES):
            try:
                candles = fetch(asset)
                now = clock()
                runner.ingest(asset, candles, now)
                if (not candles or max(int(c[0]) for c in candles) < now // HOUR * HOUR) and attempt < RETRIES - 1:
                    with runner.conn:
                        runner._event(now, "bar_missing", {"asset": asset, "attempt": attempt + 1})
                    sleep(RETRY_S)         # aktuelle Kerze fehlt noch: erneut abrufen (QA2 m3)
                    continue
                break
            except Exception as e:   # Netz-/Formatfehler: Ereignis, Wiederholung, danach naechste Stunde
                with runner.conn:
                    runner._event(clock(), "fetch_error", {"asset": asset, "attempt": attempt + 1, "err": type(e).__name__ + ": " + str(e)[:200]})
                if attempt < RETRIES - 1:
                    sleep(RETRY_S)
    if fetch_tickers is not None:
        try:
            tk = fetch_tickers(assets)
            with runner.conn:
                runner._event(clock(), "basis_log" if tk else "ticker_empty", tk)
        except Exception as e:
            with runner.conn:
                runner._event(clock(), "ticker_error", {"err": type(e).__name__ + ": " + str(e)[:200]})


def run_loop(runner, assets, fetch, clock, sleep, fetch_tickers=None, max_cycles=None, stop=None):
    n = 0
    while True:
        if stop is not None and stop():
            return n
        run_cycle(runner, assets, fetch, clock, sleep, fetch_tickers)
        n += 1
        if max_cycles is not None and n >= max_cycles:
            return n
        now = clock()
        sleep(max(1, next_fetch_ts(now) - now))
