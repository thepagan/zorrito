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
    logger.debug("🧭 Connecting to database to fetch pending alert-user matches...")
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Fetch undelivered alert-user matches
                cur.execute("""
                    SELECT ad.alert_id, ad.user_id, a."event", a.description, a.instruction, u.phone_number, u.language
                    FROM alert_delivery ad
                    JOIN alerts a ON a.id = ad.alert_id
                    JOIN "user" u ON u.id = ad.user_id
                    WHERE ad.sent_at IS NULL AND ad.matched_at IS NOT NULL
                """)
                results = cur.fetchall()
                logger.debug(f"🔎 Retrieved {len(results)} alert-user match records from database.")

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

                for alert_id, user_id, title, description, instruction, phone, lang in results:
                    lang = lang or "en"
                    translated_title = title
                    translated_description = description

                    if lang != "en":
                        cur.execute("SELECT translated_title, translated_description, translated_instruction FROM translations WHERE alert_id = %s AND language = %s", (alert_id, lang))
                        row = cur.fetchone()
                        if row:
                            translated_title, translated_description, translated_instruction = row
                            logger.debug(f"🎯 Used cached translation for alert {alert_id} in '{lang}'")
                        else:
                            import requests
                            payload = {
                                "q": f"{title}\n\n{description}\n\n{instruction or ''}",
                                "source": "en",
                                "target": lang,
                                "format": "text"
                            }
                            logger.debug(f"🌐 Requesting translation for alert {alert_id} into '{lang}' via LibreTranslate...")
                            try:
                                response = requests.post("http://libretranslate:5000/translate", data=payload, timeout=10)
                                if response.ok:
                                    translated = response.json()["translatedText"]
                                    parts = translated.split("\n\n")
                                    translated_title = parts[0] if len(parts) > 0 else ""
                                    translated_description = parts[1] if len(parts) > 1 else ""
                                    translated_instruction = parts[2] if len(parts) > 2 else ""
                                    cur.execute("INSERT INTO translations (alert_id, language, translated_title, translated_description, translated_instruction) VALUES (%s, %s, %s, %s, %s)", (alert_id, lang, translated_title, translated_description, translated_instruction))
                                    logger.debug(f"🆕 Stored new translation for alert {alert_id} in '{lang}'")
                                else:
                                    logger.warning(f"⚠️ Translation API failed for alert {alert_id} in '{lang}'")
                            except Exception as e:
                                logger.warning(f"⚠️ Exception during translation for alert {alert_id} in '{lang}': {e}")

                    t = registration_translations.get(lang, registration_translations["en"])
                    body = f"{translated_title}\n\n{translated_description}\n\n{translated_instruction or ''}"

                    if dev_mode:
                        logger.info(f"🧪 DEV MODE: Would send alert to {phone}:\n{body}")
                    else:
                        logger.debug(f"📨 Sending SMS to {phone} via Twilio...")
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
                logger.debug("💾 Database commit completed after alert delivery.")
                logger.info(f"🚚 Alert delivery completed for {len(results)} users.")

    except Exception as e:
        logger.error(f"Error during alert delivery: {e}")