DROP TABLE IF EXISTS realtime_updates CASCADE;
CREATE TABLE realtime_updates (
  trip_id TEXT,
  route_id TEXT,
  vehicle_label TEXT,
  stop_id TEXT,
  stop_sequence INT,
  arrival_delay INT,
  arrival_time BIGINT,
  maj_le TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_rt_stop ON realtime_updates (stop_id);
CREATE INDEX idx_rt_route ON realtime_updates (route_id);

CREATE TABLE IF NOT EXISTS realtime_alerts (
  alert_id TEXT,
  route_id TEXT,
  stop_id TEXT,
  header_text TEXT,
  description_text TEXT,
  effect INT,
  start_time BIGINT,
  end_time BIGINT,
  updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_alert_stop ON realtime_alerts (stop_id);
CREATE INDEX IF NOT EXISTS idx_alert_route ON realtime_alerts (route_id);

CREATE TABLE IF NOT EXISTS realtime_sync_status (
  sync_name TEXT PRIMARY KEY,
  last_success TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  entity_count INT NOT NULL DEFAULT 0,
  update_count INT NOT NULL DEFAULT 0,
  alert_count INT NOT NULL DEFAULT 0
);
