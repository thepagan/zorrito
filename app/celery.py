from celery import Celery

def make_celery():
    return Celery(
        "zorrito",
        broker="redis://localhost:6379/0",
        backend="redis://localhost:6379/0",
        include=["nws_alert_poller"]
    )

app = make_celery()

from celery.schedules import crontab

app.conf.beat_schedule = {
    "poll-nws-every-1-minutes": {
        "task": "nws_alert_poller.poll_nws_alerts",
        "schedule": crontab(minute="*/1"),  # every 5 minutes
    },
}
app.conf.timezone = "UTC"