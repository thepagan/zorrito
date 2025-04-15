from flask import Flask, request, render_template, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import os, csv, datetime, time
import sqlalchemy.exc
from twilio.rest import Client
import logging
from registration_languages import registration_translations
import psycopg2

# Set up logging to /app/zorrito.log
log_path = "/app/zorrito.log"
logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("zorrito")

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

def setup_database_with_retry(retries=5, delay=2):
    for attempt in range(retries):
        try:
            db.create_all()

            import psycopg2

            try:
                conn = psycopg2.connect("dbname='zorrito' user='zorrito' host='db' password='password'")
                cur = conn.cursor()
                if os.path.exists("schema.sql"):
                    with open("schema.sql", "r") as f:
                        cur.execute(f.read())

                if os.path.exists("seed_counties.sql"):
                    cur.execute("SELECT COUNT(*) FROM county")
                    county_count = cur.fetchone()[0]
                    if county_count == 0:
                        with open("seed_counties.sql", "r") as f:
                            cur.execute(f.read())

                conn.commit()
                cur.close()
                conn.close()
            except Exception as e:
                print(f"[Zorrito] Failed to initialize from SQL files: {e}")

            break
        except sqlalchemy.exc.OperationalError as e:
            print(f"[Zorrito] Database not ready yet... retrying ({attempt + 1}/{retries})")
            time.sleep(delay)
    else:
        raise Exception("❌ Failed to connect to database after several attempts.")

@app.route("/", methods=["GET", "POST"])
def register():
    states = sorted(s[0] for s in db.session.query(db.func.distinct(County.state)).all())
    if request.method == "POST":
        phone = request.form.get("phone_number")
        fips = request.form.get("fips")
        language = request.form.get("language")
        subscribed = bool(request.form.get("subscribed"))
        existing_user = User.query.filter_by(phone_number=phone).first()
        if existing_user:
            existing_user.fips = fips
            existing_user.language = language
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
    return render_template("register.html", states=states)

@app.route("/counties/<state>")
def counties(state):
    counties = County.query.filter_by(state=state).order_by(County.county_name).all()
    return jsonify([{ "fips": c.fips, "name": c.county_name } for c in counties])

@app.route("/thank-you")
def thank_you():
    phone = request.args.get("phone")
    user = User.query.filter_by(phone_number=phone).order_by(User.created_at.desc()).first()
    lang = user.language if user else "en"
    message = registration_translations.get(lang, registration_translations["en"])["thank_you"]
    return f"<h1>{message}</h1>"

@app.route("/send-test-alert")
def send_test_alert():
    send_zorrito_alert(os.getenv("TWILIO_TEST_NUMBER"))
    return "<h2>🦊 Zorrito envió una alerta de prueba por SMS.</h2>"

def send_zorrito_alert(phone):
    user = User.query.filter_by(phone_number=phone).order_by(User.created_at.desc()).first()
    message = registration_translations.get(user.language, registration_translations["en"])

    try:
        client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
        sent = client.messages.create(
            body=message,
            from_=os.getenv("TWILIO_FROM_NUMBER"),
            to=phone
        )
        logger.info(f"✅ Alert sent to {phone}: SID {sent.sid}")
    except Exception as e:
        logger.error(f"❌ Failed to send alert to {phone}: {e}")

if __name__ == "__main__":
    with app.app_context():
        setup_database_with_retry()
    app.run(host="0.0.0.0", port=8181)
