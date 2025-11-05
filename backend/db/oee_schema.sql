-- CNC Telemetry — OEE Schema
-- OEE = Availability × Performance × Quality

CREATE TABLE IF NOT EXISTS oee_daily (
  date DATE NOT NULL,
  machine_id TEXT NOT NULL,
  shift TEXT CHECK (shift IN ('morning','afternoon','night','daily')),
  planned_time_min INT NOT NULL,
  operating_time_min INT NOT NULL,
  availability FLOAT CHECK (availability >= 0 AND availability <= 1),
  performance FLOAT DEFAULT 1.0 CHECK (performance >= 0 AND performance <= 1),
  quality FLOAT DEFAULT 1.0 CHECK (quality >= 0 AND quality <= 1),
  oee FLOAT GENERATED ALWAYS AS (availability * performance * quality) STORED,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (date, machine_id, shift)
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_oee_date 
  ON oee_daily(date DESC);

CREATE INDEX IF NOT EXISTS idx_oee_machine 
  ON oee_daily(machine_id, date DESC);

CREATE INDEX IF NOT EXISTS idx_oee_value 
  ON oee_daily(oee DESC) 
  WHERE oee IS NOT NULL;

-- Grant permissions
GRANT ALL ON oee_daily TO cnc_user;
