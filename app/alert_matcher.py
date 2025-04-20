import os
from datetime import datetime
import psycopg2
from dotenv import load_dotenv
from logging_config import configure_logging

load_dotenv()
logger = configure_logging()

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB", "zorrito"),
        user=os.getenv("POSTGRES_USER", "zorrito"),
        password=os.getenv("POSTGRES_PASSWORD", "password"),
        host=os.getenv("POSTGRES_HOST", "db"),
        port=os.getenv("POSTGRES_PORT", "5432")
    )

def match_users_to_alerts():
    logger.info("Starting alert-to-user matching...")
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Match users to alerts by FIPS
                cur.execute("""
                    WITH new_matches AS (
                        SELECT af.alert_id, u.id AS user_id, %s AS matched_at, NULL::timestamp AS sent_at
                        FROM alert_fips af
                        JOIN "user" u ON af.fips = u.fips AND u.subscribed = TRUE
                        LEFT JOIN alert_delivery ad ON ad.alert_id = af.alert_id AND ad.user_id = u.id
                        WHERE ad.alert_id IS NULL
                    )
                    INSERT INTO alert_delivery (alert_id, user_id, matched_at, sent_at)
                    SELECT alert_id, user_id, matched_at, sent_at FROM new_matches
                    RETURNING alert_id, user_id;
                """, (datetime.utcnow(),))
                inserted = cur.fetchall()
                logger.debug(f"Matched alert-user rows: {inserted}")
                logger.info(f"Inserted {len(inserted)} alert-user match records.")
                conn.commit()
                logger.info("Committed alert-user match insert to database.")
                logger.info(f"Matched users to alerts successfully at {datetime.utcnow().isoformat()}")
    except Exception as e:
        logger.error(f"Error during user-alert matching: {e}")

from celery import Celery

celery_app = Celery("zorrito_tasks")

@celery_app.task
def run_alert_matcher(_=None):
    match_users_to_alerts()
