-- CNC Telemetry — Continuous Aggregates (TimescaleDB)
-- Pre-computed views for fast queries

-- ==========================================
-- 5-minute aggregate
-- ==========================================
CREATE MATERIALIZED VIEW IF NOT EXISTS telemetry_5m
WITH (timescaledb.continuous) AS
  SELECT 
    time_bucket('5 minutes', ts) AS bucket,
    machine_id,
    AVG(rpm) AS rpm_avg,
    MAX(rpm) AS rpm_max,
    MIN(rpm) AS rpm_min,
    STDDEV(rpm) AS rpm_stddev,
    AVG(feed_mm_min) AS feed_avg,
    MAX(feed_mm_min) AS feed_max,
    MIN(feed_mm_min) AS feed_min,
    COUNT(*) AS sample_count,
    MODE() WITHIN GROUP (ORDER BY state) AS state_mode,
    SUM(CASE WHEN state='running' THEN 1 ELSE 0 END)::FLOAT / COUNT(*) AS uptime_ratio
  FROM telemetry
  GROUP BY bucket, machine_id
  WITH NO DATA;

-- Refresh policy (update every 5 minutes)
SELECT add_continuous_aggregate_policy('telemetry_5m',
  start_offset => INTERVAL '1 hour',
  end_offset => INTERVAL '5 minutes',
  schedule_interval => INTERVAL '5 minutes',
  if_not_exists => TRUE
);

-- ==========================================
-- 1-hour aggregate (from 5min)
-- ==========================================
CREATE MATERIALIZED VIEW IF NOT EXISTS telemetry_1h
WITH (timescaledb.continuous) AS
  SELECT 
    time_bucket('1 hour', bucket) AS bucket,
    machine_id,
    AVG(rpm_avg) AS rpm_avg,
    MAX(rpm_max) AS rpm_max,
    MIN(rpm_min) AS rpm_min,
    AVG(feed_avg) AS feed_avg,
    MAX(feed_max) AS feed_max,
    SUM(sample_count) AS sample_count,
    AVG(uptime_ratio) AS uptime_ratio
  FROM telemetry_5m
  GROUP BY 1, 2
  WITH NO DATA;

-- Refresh policy (update every 1 hour)
SELECT add_continuous_aggregate_policy('telemetry_1h',
  start_offset => INTERVAL '3 hours',
  end_offset => INTERVAL '1 hour',
  schedule_interval => INTERVAL '1 hour',
  if_not_exists => TRUE
);

-- ==========================================
-- 1-day aggregate (from 1h)
-- ==========================================
CREATE MATERIALIZED VIEW IF NOT EXISTS telemetry_1d
WITH (timescaledb.continuous) AS
  SELECT 
    time_bucket('1 day', bucket) AS date,
    machine_id,
    AVG(rpm_avg) AS rpm_avg,
    MAX(rpm_max) AS rpm_max,
    MIN(rpm_min) AS rpm_min,
    AVG(feed_avg) AS feed_avg,
    MAX(feed_max) AS feed_max,
    SUM(sample_count) AS sample_count,
    AVG(uptime_ratio) AS availability
  FROM telemetry_1h
  GROUP BY 1, 2
  WITH NO DATA;

-- Refresh policy (update once per day)
SELECT add_continuous_aggregate_policy('telemetry_1d',
  start_offset => INTERVAL '1 day',
  end_offset => INTERVAL '1 hour',
  schedule_interval => INTERVAL '1 day',
  if_not_exists => TRUE
);

-- Grant permissions
GRANT SELECT ON telemetry_5m TO cnc_user;
GRANT SELECT ON telemetry_1h TO cnc_user;
GRANT SELECT ON telemetry_1d TO cnc_user;
