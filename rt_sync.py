"""Run a single safe refresh of the TBM GTFS-Realtime cache."""

from rt_sync_common import sync


if __name__ == "__main__":
    entities, passages, alerts = sync()
    print(f"Synchronisation réussie — {entities} entités, {passages} passages, {alerts} alertes")
