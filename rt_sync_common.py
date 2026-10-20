import os
"""Fetch and persist the Bordeaux GTFS-Realtime feed safely."""

import time

import psycopg2
import requests
from google.transit import gtfs_realtime_pb2


URL = "https://bdx.mecatran.com/utw/ws/gtfsfeed/realtime/bordeaux?apiKey=opendata-bordeaux-metropole-flux-gtfs-rt"
DB = dict(host=os.environ.get("DB_HOST", "localhost"), port=int(os.environ.get("DB_PORT", "5433")), dbname=os.environ.get("DB_NAME", "tbm_db"), user=os.environ.get("DB_USER", "tbm"), password=os.environ["DB_PASSWORD"])
MAX_FEED_AGE_SECONDS = 300


def _translated(field):
    translations = field.translation
    french = next((t.text for t in translations if t.language.lower().startswith("fr") and t.text), None)
    return french or next((t.text for t in translations if t.text), None)


def _fetch_rows():
    response = requests.get(URL, timeout=(5, 20))
    response.raise_for_status()
    if not response.content:
        raise ValueError("Le flux GTFS-RT est vide")

    feed = gtfs_realtime_pb2.FeedMessage()
    feed.ParseFromString(response.content)
    if not feed.IsInitialized() or not feed.entity:
        raise ValueError("Le flux GTFS-RT ne contient pas d'entités valides")

    if feed.header.HasField("timestamp"):
        age = int(time.time()) - feed.header.timestamp
        if age > MAX_FEED_AGE_SECONDS or age < -60:
            raise ValueError(f"Horodatage GTFS-RT invalide ou trop ancien ({age}s)")

    rows = []
    alert_rows = []
    trip_count = 0
    for entity in feed.entity:
        if entity.HasField("trip_update"):
            trip_count += 1
            trip_update = entity.trip_update
            route_id = trip_update.trip.route_id
            trip_id = trip_update.trip.trip_id
            vehicle_label = trip_update.vehicle.label if trip_update.HasField("vehicle") else ""
            for stop_update in trip_update.stop_time_update:
                arrival = stop_update.arrival if stop_update.HasField("arrival") else None
                rows.append((
                    trip_id, route_id, vehicle_label, stop_update.stop_id,
                    stop_update.stop_sequence,
                    arrival.delay if arrival and arrival.HasField("delay") else None,
                    arrival.time if arrival and arrival.HasField("time") else None,
                ))

        if entity.HasField("alert"):
            alert = entity.alert
            informed_entities = list(alert.informed_entity) or [None]
            active_periods = list(alert.active_period) or [None]
            for informed in informed_entities:
                route_id = informed.route_id if informed and informed.route_id else None
                stop_id = informed.stop_id if informed and informed.stop_id else None
                for period in active_periods:
                    start = period.start if period and period.HasField("start") else None
                    end = period.end if period and period.HasField("end") else None
                    alert_rows.append((
                        entity.id, route_id, stop_id,
                        _translated(alert.header_text) if alert.HasField("header_text") else None,
                        _translated(alert.description_text) if alert.HasField("description_text") else None,
                        int(alert.effect) if alert.HasField("effect") else None,
                        start, end,
                    ))

    # A malformed or unexpectedly empty trip feed must never erase the last good cache.
    if trip_count == 0 or not rows:
        raise ValueError("Le flux ne contient aucun passage exploitable ; cache conservé")
    return feed, rows, alert_rows


def sync():
    feed, rows, alert_rows = _fetch_rows()
    conn = psycopg2.connect(**DB)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""CREATE TABLE IF NOT EXISTS realtime_alerts (
                    alert_id TEXT, route_id TEXT, stop_id TEXT, header_text TEXT,
                    description_text TEXT, effect INT, start_time BIGINT, end_time BIGINT,
                    updated_at TIMESTAMP DEFAULT NOW())""")
                cur.execute("""CREATE TABLE IF NOT EXISTS realtime_sync_status (
                    sync_name TEXT PRIMARY KEY, last_success TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    entity_count INT NOT NULL DEFAULT 0, update_count INT NOT NULL DEFAULT 0,
                    alert_count INT NOT NULL DEFAULT 0)""")
                # DELETE is MVCC-safe for concurrent API readers; TRUNCATE would block
                # live departure requests until this entire large batch commits.
                cur.execute("DELETE FROM realtime_updates")
                cur.execute("DELETE FROM realtime_alerts")
                cur.executemany(
                    """INSERT INTO realtime_updates
                    (trip_id,route_id,vehicle_label,stop_id,stop_sequence,arrival_delay,arrival_time)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                    rows,
                )
                cur.executemany(
                    """INSERT INTO realtime_alerts
                    (alert_id,route_id,stop_id,header_text,description_text,effect,start_time,end_time)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                    alert_rows,
                )
                cur.execute("""INSERT INTO realtime_sync_status
                    (sync_name,last_success,entity_count,update_count,alert_count)
                    VALUES ('gtfs_rt',NOW(),%s,%s,%s)
                    ON CONFLICT (sync_name) DO UPDATE SET last_success=EXCLUDED.last_success,
                    entity_count=EXCLUDED.entity_count, update_count=EXCLUDED.update_count,
                    alert_count=EXCLUDED.alert_count""",
                    (len(feed.entity), len(rows), len(alert_rows)))
    finally:
        conn.close()
    return len(feed.entity), len(rows), len(alert_rows)
