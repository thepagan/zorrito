import os
import requests
import logging
from datetime import datetime
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logging setup
logging.basicConfig(
    filename=os.getenv("ZORRITO_ALERT_LOG", "zorrito_alerts.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Constants
NWS_API_ENDPOINT = "https://api.weather.gov/alerts/active"

# Database connection
def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB", "zorrito"),
        user=os.getenv("POSTGRES_USER", "zorrito"),
        password=os.getenv("POSTGRES_PASSWORD", "password"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432")
    )

def fetch_active_alerts():
    try:
        response = requests.get(NWS_API_ENDPOINT, headers={"User-Agent": "Zorrito/0.10"})
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Failed to fetch NWS alerts: {e}")
        return None

def main():
    logging.info("Starting NWS alert polling...")
    data = fetch_active_alerts()
    if not data:
        return

    # Future steps:
    # - Parse alert features
    # - Check DB for existing alert ID
    # - Insert into alerts and alert_fips
    features = data.get("features", [])
    if not features:
        logging.info("No active alerts found.")
        return

    conn = get_db_connection()
    cur = conn.cursor()

    inserted = 0
    for feature in features:
        props = feature.get("properties", {})
        alert_id = feature.get("id")
        area_desc = props.get("areaDesc", "")
        onset = props.get("onset")
        ends = props.get("ends")
        event = props.get("event")
        headline = props.get("headline")
        description = props.get("description")
        instruction = props.get("instruction")
        severity = props.get("severity")
        certainty = props.get("certainty")
        urgency = props.get("urgency")
        sender = props.get("sender")
        sent = props.get("sent")
        effective = props.get("effective")
        fips_list = props.get("geocode", {}).get("FIPS6", [])

        # Check for duplicate alert ID
        cur.execute("SELECT id FROM alerts WHERE id = %s;", (alert_id,))
        if cur.fetchone():
            continue

        cur.execute("""
            INSERT INTO alerts (id, event, severity, certainty, urgency, headline, description, instruction,
                                area_desc, sender, onset, ends, sent, effective)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (
            alert_id, event, severity, certainty, urgency, headline, description, instruction,
            area_desc, sender, onset, ends, sent, effective
        ))

        for fips in fips_list:
            cur.execute("INSERT INTO alert_fips (alert_id, fips) VALUES (%s, %s);", (alert_id, fips))

        inserted += 1

    conn.commit()
    cur.close()
    conn.close()
    logging.info(f"Inserted {inserted} new alerts into database.")

if __name__ == "__main__":
    main()
