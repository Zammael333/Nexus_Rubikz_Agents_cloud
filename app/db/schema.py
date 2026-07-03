SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS nexus_migrations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    applied_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS worker_state (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_id       TEXT    NOT NULL UNIQUE,
    worker_type     TEXT    NOT NULL DEFAULT 'generic',
    status          TEXT    NOT NULL DEFAULT 'HEALTHY',
    consecutive_failures INTEGER NOT NULL DEFAULT 0,
    total_requests  INTEGER NOT NULL DEFAULT 0,
    total_failures  INTEGER NOT NULL DEFAULT 0,
    error_budget_consumed REAL NOT NULL DEFAULT 0.0,
    slo_real        REAL    NOT NULL DEFAULT 1.0,
    trust_score     REAL    NOT NULL DEFAULT 1.0,
    last_heartbeat  TEXT    NOT NULL DEFAULT '',
    recovery_epoch  TEXT    NOT NULL DEFAULT '',
    metadata_json   TEXT    NOT NULL DEFAULT '{}',
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS event_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_uuid      TEXT    NOT NULL,
    event_type      TEXT    NOT NULL,
    source          TEXT    NOT NULL DEFAULT '',
    payload_json    TEXT    NOT NULL DEFAULT '{}',
    priority        TEXT    NOT NULL DEFAULT 'NORMAL',
    status          TEXT    NOT NULL DEFAULT 'PROCESSED',
    error_message   TEXT    NOT NULL DEFAULT '',
    dlq_reason      TEXT    NOT NULL DEFAULT '',
    recovery_epoch  TEXT    NOT NULL DEFAULT '',
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS budget_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_id       TEXT    NOT NULL DEFAULT '__global__',
    total_requests  INTEGER NOT NULL DEFAULT 0,
    total_failures  INTEGER NOT NULL DEFAULT 0,
    error_rate      REAL    NOT NULL DEFAULT 0.0,
    budget_consumed REAL    NOT NULL DEFAULT 0.0,
    slo_target      REAL    NOT NULL DEFAULT 0.999973,
    status          TEXT    NOT NULL DEFAULT 'NOMINAL',
    recorded_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS scorpion_findings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id         TEXT    NOT NULL,
    worker_id       TEXT    NOT NULL DEFAULT '',
    vector_id       TEXT    NOT NULL,
    severity        TEXT    NOT NULL DEFAULT 'MEDIUM',
    description     TEXT    NOT NULL DEFAULT '',
    mitigated       INTEGER NOT NULL DEFAULT 0,
    mitigated_at    TEXT    NOT NULL DEFAULT '',
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

PG_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS nexus_migrations (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS worker_state (
    id              SERIAL PRIMARY KEY,
    worker_id       TEXT NOT NULL UNIQUE,
    worker_type     TEXT NOT NULL DEFAULT 'generic',
    status          TEXT NOT NULL DEFAULT 'HEALTHY',
    consecutive_failures INTEGER NOT NULL DEFAULT 0,
    total_requests  BIGINT NOT NULL DEFAULT 0,
    total_failures  BIGINT NOT NULL DEFAULT 0,
    error_budget_consumed DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    slo_real        DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    trust_score     DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    last_heartbeat  TIMESTAMPTZ,
    recovery_epoch  TEXT NOT NULL DEFAULT '',
    metadata_json   JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS event_log (
    id              SERIAL PRIMARY KEY,
    event_uuid      TEXT NOT NULL,
    event_type      TEXT NOT NULL,
    source          TEXT NOT NULL DEFAULT '',
    payload_json    JSONB NOT NULL DEFAULT '{}',
    priority        TEXT NOT NULL DEFAULT 'NORMAL',
    status          TEXT NOT NULL DEFAULT 'PROCESSED',
    error_message   TEXT NOT NULL DEFAULT '',
    dlq_reason      TEXT NOT NULL DEFAULT '',
    recovery_epoch  TEXT NOT NULL DEFAULT '',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS budget_snapshots (
    id              SERIAL PRIMARY KEY,
    worker_id       TEXT NOT NULL DEFAULT '__global__',
    total_requests  BIGINT NOT NULL DEFAULT 0,
    total_failures  BIGINT NOT NULL DEFAULT 0,
    error_rate      DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    budget_consumed DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    slo_target      DOUBLE PRECISION NOT NULL DEFAULT 0.999973,
    status          TEXT NOT NULL DEFAULT 'NOMINAL',
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scorpion_findings (
    id              SERIAL PRIMARY KEY,
    scan_id         TEXT NOT NULL,
    worker_id       TEXT NOT NULL DEFAULT '',
    vector_id       TEXT NOT NULL,
    severity        TEXT NOT NULL DEFAULT 'MEDIUM',
    description     TEXT NOT NULL DEFAULT '',
    mitigated       BOOLEAN NOT NULL DEFAULT FALSE,
    mitigated_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_worker_state_worker_id ON worker_state(worker_id);
CREATE INDEX IF NOT EXISTS idx_worker_state_status ON worker_state(status);
CREATE INDEX IF NOT EXISTS idx_event_log_uuid ON event_log(event_uuid);
CREATE INDEX IF NOT EXISTS idx_event_log_type ON event_log(event_type);
CREATE INDEX IF NOT EXISTS idx_event_log_status ON event_log(status);
CREATE INDEX IF NOT EXISTS idx_event_log_created ON event_log(created_at);
CREATE INDEX IF NOT EXISTS idx_budget_worker ON budget_snapshots(worker_id);
CREATE INDEX IF NOT EXISTS idx_budget_recorded ON budget_snapshots(recorded_at);
CREATE INDEX IF NOT EXISTS idx_scorpion_vector ON scorpion_findings(vector_id);
CREATE INDEX IF NOT EXISTS idx_scorpion_scan ON scorpion_findings(scan_id);
"""
