import os
import requests
import logging
from datetime import datetime
import psycopg2
from dotenv import load_dotenv
from celery import Celery, shared_task
from sqlalchemy import create_engine, text
from logging_config import configure_logging

logger = configure_logging()

# Constants
NWS_API_ENDPOINT = "https://api.weather.gov/alerts/active"

# Database connection
def get_db_connection():
    try:
        return psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB", "zorrito"),
            user=os.getenv("POSTGRES_USER", "zorrito"),
            password=os.getenv("POSTGRES_PASSWORD", "password"),
            host=os.getenv("POSTGRES_HOST", "db"),
            port=os.getenv("POSTGRES_PORT")
        )
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

def fetch_active_alerts():
    try:
        response = requests.get(NWS_API_ENDPOINT, headers={"User-Agent": "Zorrito/0.10"}, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch NWS alerts: {e}")
        return None

@shared_task
def poll_nws_alerts():
    logger.info("📡 Starting NWS alert polling...")
    data = fetch_active_alerts()
    if not data:
        return

    features = data.get("features", [])
    if not features:
        logger.info("No active alerts found.")
        return

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                inserted = 0
                for feature in features:
                    props = feature.get("properties", {})
                    severity = props.get("severity")
                    if severity is None or severity.strip().title() not in {"Moderate", "Severe", "Extreme"}:
                        continue

                    alert_id = feature.get("id")
                    area_desc = props.get("areaDesc", "")
                    onset = props.get("onset")
                    ends = props.get("ends")
                    event = props.get("event")
                    headline = props.get("headline")
                    description = props.get("description", "").encode("utf-8", errors="replace").decode("utf-8")
                    instruction = props.get("instruction")
                    certainty = props.get("certainty")
                    urgency = props.get("urgency")
                    sender = props.get("sender")
                    sent = props.get("sent")
                    effective = props.get("effective")
                    fips_list = props.get("geocode", {}).get("FIPS6", [])
                    if not fips_list:
                        fips_list = props.get("geocode", {}).get("SAME", [])
                    fips_list = [f.lstrip("0") for f in fips_list if f.isdigit()]

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

                    delivery_time = datetime.utcnow()
                    logger.info(f"✅ Alert delivered\n• ID: {alert_id}\n• Event: {event}\n• Severity: {severity}\n• Time: {delivery_time.isoformat()}")

                    inserted += 1
            conn.commit()
            logger.info(f"📥 Inserted {inserted} new alerts into database at {datetime.utcnow().isoformat()}")
    except Exception as e:
        logger.error(f"Error during database insert: {e}")

db_url = (
    f"postgresql+psycopg2://{os.getenv('POSTGRES_USER', 'zorrito')}:"
    f"{os.getenv('POSTGRES_PASSWORD', 'password')}@"
    f"{os.getenv('POSTGRES_HOST', 'db')}:"
    f"{os.getenv('POSTGRES_PORT', '5432')}/"
    f"{os.getenv('POSTGRES_DB', 'zorrito')}"
)
db_engine = create_engine(db_url)

@shared_task
def refresh_user_alerts_view():
    try:
        with db_engine.begin() as conn:
            conn.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY user_alerts_view"))
            logger.info(f"🔄 user_alerts_view refreshed at {datetime.utcnow().isoformat()}")
    except Exception as e:
        logger.error(f"Failed to refresh materialized view: {e}")

@shared_task
def prune_expired_alerts():
    try:
        with db_engine.begin() as conn:
            delivery_result = conn.execute(text("""
                DELETE FROM alert_delivery
                WHERE alert_id IN (
                    SELECT id FROM alerts WHERE expires < (now() - interval '1 day')
                ) AND sent_at IS NOT NULL
            """))

            fips_result = conn.execute(text("""
                DELETE FROM alert_fips
                WHERE alert_id IN (
                    SELECT id FROM alerts WHERE expires < (now() - interval '1 day')
                )
            """))

            alerts_result = conn.execute(text("""
                DELETE FROM alerts
                WHERE expires < (now() - interval '1 day')
            """))

            logger.info(
                f"🧹 Pruned expired alerts at {datetime.utcnow().isoformat()}:\n"
                f"• alert_delivery: {delivery_result.rowcount}\n"
                f"• alert_fips: {fips_result.rowcount}\n"
                f"• alerts: {alerts_result.rowcount}"
            )

    except Exception as e:
        logger.error(f"Error pruning expired alerts: {e}")
