-- USERS
CREATE TABLE IF NOT EXISTS "user" (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(15) NOT NULL,
    fips VARCHAR(5) NOT NULL,
    language VARCHAR(5) DEFAULT 'en',
    CONSTRAINT chk_user_language CHECK (language IN (
        'en', 'es', 'so', 'ar', 'mm', 'sw', 'fr', 'rw', 'vi', 'ne', 'te', 'tr', 'ps'
    )),
    subscribed BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sub_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    unsub_on TIMESTAMP
);

-- COUNTIES
CREATE TABLE IF NOT EXISTS county (
    id SERIAL PRIMARY KEY,
    county_name VARCHAR(100) NOT NULL,
    state VARCHAR(2) NOT NULL,
    fips VARCHAR(5) UNIQUE NOT NULL
);

-- ALERTS
CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY,
    event TEXT,
    headline TEXT,
    description TEXT,
    instruction TEXT,
    severity TEXT,
    urgency TEXT,
    certainty TEXT,
    category TEXT,
    message_type TEXT,
    sender TEXT,
    sender_name TEXT,
    area_desc TEXT,
    sent TIMESTAMP,
    effective TIMESTAMP,
    onset TIMESTAMP,
    expires TIMESTAMP,
    ends TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ALERT-FIPS LINKING
CREATE TABLE IF NOT EXISTS alert_fips (
    alert_id TEXT REFERENCES alerts(id) ON DELETE CASCADE,
    fips VARCHAR(5),
    PRIMARY KEY (alert_id, fips)
);

ALTER TABLE alert_fips
ADD CONSTRAINT fk_alert_fips_county
FOREIGN KEY (fips) REFERENCES county(fips) ON DELETE CASCADE;

-- ALERT DELIVERY LOG
CREATE TABLE IF NOT EXISTS alert_delivery (
    user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE,
    alert_id TEXT REFERENCES alerts(id) ON DELETE CASCADE,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT,
    matched_at TIMESTAMP,
    PRIMARY KEY (user_id, alert_id)
);

-- TRANSLATIONS CACHE
CREATE TABLE IF NOT EXISTS translations (
    id SERIAL PRIMARY KEY,
    alert_id TEXT REFERENCES alerts(id) ON DELETE CASCADE,
    user_language VARCHAR(5) NOT NULL,
    translated_headline TEXT,
    translated_description TEXT,
    translated_instruction TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(alert_id, user_language)
);

-- Index to speed up searching for alerts by FIPS or ID
CREATE INDEX IF NOT EXISTS idx_alert_fips_composite ON alert_fips(alert_id, fips);

-- Index to speed up matching users to alerts by FIPS
CREATE INDEX IF NOT EXISTS idx_user_fips ON "user"(fips);

-- Index to improve performance of cleanup queries on expired alerts
CREATE INDEX IF NOT EXISTS idx_alerts_expires ON alerts(expires);

-- Index to improve lookup speed on delivery logs
CREATE INDEX IF NOT EXISTS idx_alert_delivery_sent_at ON alert_delivery(sent_at);

-- Safe conditional block to ensure only specific severities are stored
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'chk_alerts_severity'
          AND conrelid = 'alerts'::regclass
    ) THEN
        ALTER TABLE alerts
        ADD CONSTRAINT chk_alerts_severity
        CHECK (severity IN ('Moderate', 'Severe', 'Extreme'));
    END IF;
END
$$;

-- Materialized view to speed up alert-to-user matching
CREATE MATERIALIZED VIEW IF NOT EXISTS user_alerts_view AS
SELECT
    u.id AS user_id,
    u.phone_number,
    u.language,
    a.id AS alert_id,
    a.event,
    a.headline,
    a.description,
    a.severity,
    a.expires
FROM "user" u
JOIN alert_fips af ON u.fips = af.fips
JOIN alerts a ON af.alert_id = a.id
WHERE a.severity IN ('Moderate', 'Severe', 'Extreme');

-- Index to speed up querying the materialized view by user_id
CREATE INDEX IF NOT EXISTS idx_user_alerts_user_id ON user_alerts_view(user_id);

-- Index to speed up querying the materialized view by alert_id
CREATE INDEX IF NOT EXISTS idx_user_alerts_alert_id ON user_alerts_view(alert_id);

-- Composite index for efficient matching of users and alerts
CREATE UNIQUE INDEX IF NOT EXISTS user_alerts_view_id_idx
ON user_alerts_view(user_id, alert_id);

-- View for translatable alerts
DROP VIEW IF EXISTS translatable_alerts;
CREATE VIEW translatable_alerts AS
SELECT id, headline, description, instruction, severity
FROM alerts
WHERE severity = 'Extreme';

-- Normalization table for alert event metadata
CREATE TABLE IF NOT EXISTS alert_event (
    event TEXT PRIMARY KEY,
    category TEXT,
    description TEXT
);