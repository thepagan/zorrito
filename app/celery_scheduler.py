from celery import Celery
from celery.schedules import crontab
from celery import chain
from logging_config import configure_logging

configure_logging()

from alert_matcher import celery_app, run_alert_matcher
from nws_alert_poller import poll_nws_alerts
from alert_delivery import deliver_alerts

@celery_app.task(name="poll_then_match")
def poll_then_match():
    return chain(
        poll_nws_alerts.s(),
        run_alert_matcher.s(),
        deliver_alerts.s()
    )()

celery_app.conf.beat_schedule = {
    "poll-then-match-every-minute": {
        "task": "poll_then_match",
        "schedule": crontab(minute="*"),
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

celery_app.conf.timezone = "UTC"
