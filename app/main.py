
from flask import Flask, request, render_template, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import os, csv, datetime, time
import sqlalchemy.exc

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

def setup_database_with_retry(retries=5, delay=2):
    for attempt in range(retries):
        try:
            db.create_all()
            if County.query.count() == 0:
                with open("counties.csv") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        county = County(county_name=row["county_name"], state=row["state"], fips=row["fips"])
                        db.session.add(county)
                db.session.commit()
            break
        except sqlalchemy.exc.OperationalError as e:
            print(f"[Zorrito] Database not ready yet... retrying ({attempt + 1}/{retries})")
            time.sleep(delay)
    else:
        raise Exception("❌ Failed to connect to database after several attempts.")

@app.route("/", methods=["GET", "POST"])
def register():
    states = sorted(set(c.state for c in County.query.all()))
    if request.method == "POST":
        phone = request.form.get("phone_number")
        fips = request.form.get("fips")
        language = request.form.get("language")
        subscribed = bool(request.form.get("subscribed"))
        user = User(phone_number=phone, fips=fips, language=language, subscribed=subscribed)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("thank_you"))
    return render_template("register.html", states=states)

@app.route("/counties/<state>")
def counties(state):
    counties = County.query.filter_by(state=state).order_by(County.county_name).all()
    return jsonify([{ "fips": c.fips, "name": c.county_name } for c in counties])

@app.route("/thank-you")
def thank_you():
    return "<h1>🦊 ¡Zorrito te ha registrado exitosamente!</h1>"

if __name__ == "__main__":
    with app.app_context():
        setup_database_with_retry()
    app.run(host="0.0.0.0", port=8181)
