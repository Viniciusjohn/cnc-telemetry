-- CNC Telemetry — TimescaleDB Schema
-- Database: cnc_telemetry
-- User: cnc_user

-- Main telemetry table
CREATE TABLE IF NOT EXISTS telemetry (
  ts TIMESTAMPTZ NOT NULL,
  machine_id TEXT NOT NULL,
  rpm DOUBLE PRECISION CHECK (rpm >= 0),
  feed_mm_min DOUBLE PRECISION CHECK (feed_mm_min >= 0),
  state TEXT CHECK (state IN ('running','stopped','idle')),
  sequence BIGINT,
  src TEXT DEFAULT 'mtconnect',
  ingested_at TIMESTAMPTZ DEFAULT NOW()
);

-- Convert to hypertable (partitioned by time)
SELECT create_hypertable('telemetry', 'ts', if_not_exists=>TRUE);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_machine_ts 
  ON telemetry(machine_id, ts DESC);

CREATE INDEX IF NOT EXISTS idx_state_ts 
  ON telemetry(state, ts DESC) 
  WHERE state != 'idle';

CREATE INDEX IF NOT EXISTS idx_sequence 
  ON telemetry(sequence) 
  WHERE sequence IS NOT NULL;

-- Retention policy (auto-delete data older than 30 days)
SELECT add_retention_policy('telemetry', INTERVAL '30 days', if_not_exists=>TRUE);

-- Compression policy (compress chunks older than 7 days, saves ~70% storage)
ALTER TABLE telemetry SET (
  timescaledb.compress,
  timescaledb.compress_segmentby = 'machine_id',
  timescaledb.compress_orderby = 'ts DESC'
);

SELECT add_compression_policy('telemetry', INTERVAL '7 days', if_not_exists=>TRUE);

-- Grant permissions
GRANT ALL ON telemetry TO cnc_user;
