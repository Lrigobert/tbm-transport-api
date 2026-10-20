"""Keep the TBM GTFS-Realtime cache current every 30 seconds."""

import time
from datetime import datetime

import psycopg2

from rt_sync_common import DB, sync


INTERVALLE = 30
LOCK_ID = 724051800


def main():
    lock_conn = psycopg2.connect(**DB)
    try:
        with lock_conn.cursor() as cur:
            cur.execute("SELECT pg_try_advisory_lock(%s)", (LOCK_ID,))
            if not cur.fetchone()[0]:
                print("Un synchroniseur temps réel TBM tourne déjà.", flush=True)
                return

        print("Synchronisation temps réel TBM démarrée (actualisation toutes les 30 s).", flush=True)
        while True:
            heure = datetime.now().strftime("%H:%M:%S")
            try:
                entities, passages, alertes = sync()
                print(f"[{heure}] OK — {entities} entités, {passages} passages, {alertes} alertes", flush=True)
            except Exception as exc:
                print(f"[{heure}] Échec — cache précédent conservé ({type(exc).__name__}: {exc})", flush=True)
            time.sleep(INTERVALLE)
    finally:
        if not lock_conn.closed:
            lock_conn.close()  # Closing the session releases its advisory lock.


if __name__ == "__main__":
    main()
