-- USERS
CREATE TABLE IF NOT EXISTS "user" (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(15) NOT NULL,
    fips VARCHAR(5) NOT NULL,
    language VARCHAR(5) DEFAULT 'en',
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

-- ALERT DELIVERY LOG
CREATE TABLE IF NOT EXISTS alert_delivery (
    user_id INTEGER REFERENCES "user"(id) ON DELETE CASCADE,
    alert_id TEXT REFERENCES alerts(id) ON DELETE CASCADE,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT,
    PRIMARY KEY (user_id, alert_id)
);