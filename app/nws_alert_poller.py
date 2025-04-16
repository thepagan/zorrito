import os
import requests
import logging
from datetime import datetime
import psycopg2
from dotenv import load_dotenv
from celery import Celery, shared_task
from celery.schedules import crontab
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()
app = Celery("nws_alert_poller", broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"))

app.conf.beat_schedule = {
    "poll-nws-every-1-minute": {
        "task": "nws_alert_poller.poll_nws_alerts",
        "schedule": crontab(minute="*/1"),
    },
    "refresh-user-alerts-view-every-2-minutes": {
        "task": "nws_alert_poller.refresh_user_alerts_view",
        "schedule": crontab(minute="*/2"),
    },
    "prune-expired-alerts-daily": {
        "task": "nws_alert_poller.prune_expired_alerts",
        "schedule": crontab(hour=3, minute=30),
    },
}
app.conf.timezone = "UTC"

# Logging setup
logging.basicConfig(
    filename=os.getenv("ZORRITO_ALERT_LOG", "/tmp/zorrito_polling.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

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
        logging.error(f"Database connection failed: {e}")
        raise

def fetch_active_alerts():
    try:
        response = requests.get(NWS_API_ENDPOINT, headers={"User-Agent": "Zorrito/0.10"}, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Failed to fetch NWS alerts: {e}")
        return None

@app.task
def poll_nws_alerts():
    logging.info("Starting NWS alert polling...")
    data = fetch_active_alerts()
    if not data:
        return

    features = data.get("features", [])
    if not features:
        logging.info("No active alerts found.")
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
                    fips_list = [f for f in props.get("geocode", {}).get("FIPS6", []) if f.isdigit()]

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
                    logging.info(f"Alert {alert_id} delivered at {delivery_time.isoformat()}")

                    inserted += 1
            conn.commit()
            logging.info(f"Inserted {inserted} new alerts into database.")
            logging.debug(f"Poll completed at {datetime.utcnow().isoformat()} with {inserted} inserts.")
    except Exception as e:
        logging.error(f"Error during database insert: {e}")

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
            logging.info(f"user_alerts_view refreshed at {datetime.utcnow().isoformat()}")
    except Exception as e:
        logging.error(f"Failed to refresh materialized view: {e}")

@shared_task
def prune_expired_alerts():
    try:
        with db_engine.begin() as conn:
            result = conn.execute(text("""
                DELETE FROM alerts
                WHERE expires < (now() - interval '1 day')
            """))
            logging.info(f"Pruned {result.rowcount} expired alerts at {datetime.utcnow().isoformat()}")
    except Exception as e:
        logging.error(f"Error pruning expired alerts: {e}")
