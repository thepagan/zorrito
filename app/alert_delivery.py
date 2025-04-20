import os
from celery import Celery
from logging_config import configure_logging
celery_app = Celery("zorrito_tasks")
import logging
from datetime import datetime
import psycopg2
from dotenv import load_dotenv
from twilio.rest import Client
from registration_languages import registration_translations

log_file_path = os.getenv("ZORRITO_LOG_FILE", "/app/zorrito.log")
logger = configure_logging()

load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB", "zorrito"),
        user=os.getenv("POSTGRES_USER", "zorrito"),
        password=os.getenv("POSTGRES_PASSWORD", "password"),
        host=os.getenv("POSTGRES_HOST", "db"),
        port=os.getenv("POSTGRES_PORT", "5432")
    )

@celery_app.task(name="deliver_alerts")
def deliver_alerts(*args, **kwargs):
    logger.info("🚀 Starting alert delivery process...")
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Fetch undelivered alert-user matches
                cur.execute("""
                    SELECT ad.alert_id, ad.user_id, a."event", a.description, u.phone_number, u.language
                    FROM alert_delivery ad
                    JOIN alerts a ON a.id = ad.alert_id
                    JOIN "user" u ON u.id = ad.user_id
                    WHERE ad.sent_at IS NULL AND ad.matched_at IS NOT NULL
                """)
                results = cur.fetchall()

                if results:
                    logger.debug("📝 Matched alerts to deliver:")
                    for r in results:
                        logger.debug(f"→ Alert ID: {r[0]}, User ID: {r[1]}, Phone: {r[4]}, Language: {r[5]}")

                logger.info(f"📬 Found {len(results)} pending alert deliveries.")

                if not results:
                    logger.info("📭 No pending alert deliveries.")
                    return

                client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
                from_number = os.getenv("TWILIO_FROM_NUMBER", "+18886064067")
                dev_mode = os.getenv("ZORRITO_DEV_MODE", "true").lower() == "true"

                for alert_id, user_id, title, description, phone, lang in results:
                    t = registration_translations.get(lang or "en", registration_translations["en"])
                    body = f"{title}\n\n{description}"

                    if dev_mode:
                        logger.info(f"🧪 DEV MODE: Would send alert to {phone}:\n{body}")
                    else:
                        try:
                            client.messages.create(
                                body=body,
                                from_=from_number,
                                to=phone
                            )
                            logger.info(f"✅ Alert sent to {phone}:\n{body}")
                        except Exception as e:
                            logger.error(f"❌ Failed to send alert to {phone}: {e}")
                            continue

                    # Update sent_at
                    cur.execute("UPDATE alert_delivery SET sent_at = %s WHERE alert_id = %s AND user_id = %s", (datetime.utcnow(), alert_id, user_id))

                conn.commit()
                logger.info(f"🚚 Alert delivery completed for {len(results)} users.")

    except Exception as e:
        logger.error(f"Error during alert delivery: {e}")