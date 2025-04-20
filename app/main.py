from flask import Flask, request, render_template, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import os, csv, datetime, time
import sqlalchemy.exc
import sqlalchemy
from twilio.rest import Client
from logging_config import logger
from registration_languages import registration_translations

def send_zorrito_alert(phone):
    test_number = os.getenv("TWILIO_TEST_NUMBER")
    user = User.query.filter_by(phone_number=phone).first()
    dev_mode = os.getenv("ZORRITO_DEV_MODE", "true").lower() == "true"
    if user:
        lang = user.language or "en"
        translations = registration_translations.get(lang, registration_translations["en"])
        message = translations["welcome_sms"] if user.subscribed else translations["goodbye_sms"]

        client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
        from_number = os.getenv("TWILIO_FROM_NUMBER")
        if not from_number:
            from_number = "+18886064067"
            logger.warning("TWILIO_FROM_NUMBER was not set. Using fallback number for dev mode.")

        if dev_mode:
            logger.info(f"🧪 DEV MODE: Would send SMS to {phone} from {from_number}")
            logger.info(f"📨 SMS Content: {message}")
            logger.info(f"🔕 SMS send skipped. Would send from {from_number} to {phone} with body: {message}")
        else:
            logger.info(f"🚀 Sending real SMS to {phone} from {from_number}")
            client.messages.create(
                body=message,
                from_=from_number,
                to=phone
            )
    else:
        logger.warning(f"📨 Tried to send alert to unknown user {phone}")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://zorrito:password@db:5432/zorrito'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class County(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    county_name = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(2), nullable=False)
    fips = db.Column(db.String(10), nullable=False, unique=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), nullable=False)
    fips = db.Column(db.String(10), nullable=False)
    language = db.Column(db.String(5), nullable=False)
    subscribed = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    sub_on = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    unsub_on = db.Column(db.DateTime, nullable=True)

@app.route("/", methods=["GET", "POST"])
def register():
    states = sorted(s[0] for s in db.session.query(db.func.distinct(County.state)).all())
    already_registered = False
    if request.method == "POST":
        phone = request.form.get("phone_number")
        fips = request.form.get("fips")
        language = request.form.get("language")
        subscribed = bool(request.form.get("subscribed"))
        existing_user = User.query.filter_by(phone_number=phone).first()
        already_registered = existing_user is not None and existing_user.subscribed
        if existing_user:
        #    existing_user.fips = fips
        #    existing_user.language = language
            existing_user.subscribed = subscribed
            if subscribed:
                existing_user.sub_on = datetime.datetime.utcnow()
                existing_user.unsub_on = None
            else:
                existing_user.unsub_on = datetime.datetime.utcnow()
            user = existing_user
        else:
            user = User(
                phone_number=phone,
                fips=fips,
                language=language,
                subscribed=subscribed,
                sub_on=datetime.datetime.utcnow() if subscribed else None,
                unsub_on=datetime.datetime.utcnow() if not subscribed else None
            )
            db.session.add(user)
        db.session.commit()
        send_zorrito_alert(phone)
        return redirect(url_for("thank_you", phone=phone))
    log_file_path = "/app/zorrito.log"
    recent_log_lines = []
    try:
        with open(log_file_path, "r") as f:
            lines = f.readlines()
        # Only include lines with "delivered"
        filtered = [line for line in lines if "delivered" in line]
        recent_log_lines = filtered[-50:]
    except Exception as e:
        logger.error(f"Failed to load log lines for frontend: {e}")
    return render_template("register.html", states=states, already_registered=already_registered, recent_logs=recent_log_lines)

@app.route("/counties/<state>")
def counties(state):
    counties = County.query.filter_by(state=state).order_by(County.county_name).all()
    return jsonify([{ "fips": c.fips, "name": c.county_name } for c in counties])

@app.route("/thank-you")
def thank_you():
    phone = request.args.get("phone")
    user = User.query.filter_by(phone_number=phone).order_by(User.created_at.desc()).first()
    lang = user.language if user else "en"
    if user and not user.subscribed:
        message = registration_translations.get(lang, registration_translations["en"])["unsubscribed"]
    else:
        message = registration_translations.get(lang, registration_translations["en"])["thank_you"]
    return f"<h1>{message}</h1>"

@app.route("/send-test-alert")
def send_test_alert():
    send_zorrito_alert(os.getenv("TWILIO_TEST_NUMBER"))
    return "<h2>🦊 Zorrito envió una alerta de prueba por SMS.</h2>"

@app.route("/sms-webhook", methods=["POST"])
def sms_webhook():
    from twilio.twiml.messaging_response import MessagingResponse
    incoming_number = request.form.get("From")
    incoming_body = request.form.get("Body", "").strip().lower()

    response = MessagingResponse()
    user = User.query.filter_by(phone_number=incoming_number).order_by(User.created_at.desc()).first()
    if user:
        lang = user.language or "en"
        t = registration_translations.get(lang, registration_translations["en"])

    if user:
        if incoming_body in ["stop", "unsubscribe", "cancel"]:
            if user.subscribed:
                user.subscribed = False
                user.unsub_on = datetime.datetime.utcnow()
                db.session.commit()
                logger.info(f"📴 User {incoming_number} unsubscribed via SMS.")
                response.message(t["goodbye_sms"] + " " + t.get("resubscribe_tip", "Reply START to rejoin."))
            else:
                response.message(t.get("already_unsubscribed", "You’re already unsubscribed from Zorrito alerts."))
        elif incoming_body in ["start", "subscribe"]:
            if not user.subscribed:
                user.subscribed = True
                user.sub_on = datetime.datetime.utcnow()
                user.unsub_on = None
                db.session.commit()
                logger.info(f"📲 User {incoming_number} resubscribed via SMS.")
                response.message(t["welcome_sms"])
            else:
                response.message(t.get("already_subscribed", "You’re already subscribed to Zorrito alerts."))
        else:
            response.message(t.get("unknown_command", "Reply STOP to unsubscribe or START to subscribe."))
    else:
        logger.warning(f"⚠️ Received SMS from unknown number {incoming_number}.")
        t = registration_translations.get("en", registration_translations["en"])
        response.message(t.get("not_found", "Your number is not registered with Zorrito."))

    return str(response)

@app.route("/check-phone")
def check_phone():
    number = request.args.get("number")
    user = User.query.filter_by(phone_number=number).first()
    exists = user is not None and user.subscribed
    return jsonify({ "exists": exists })

@app.route("/logs/recent")
def recent_logs():
    log_file_path = "/app/logs/zorrito.log"
    try:
        with open(log_file_path, "r") as f:
            lines = f.readlines()
        return jsonify({"log": lines[-50:]})
    except Exception as e:
        logger.error(f"Failed to read logs: {e}")
        return jsonify({"log": [], "error": str(e)}), 500
