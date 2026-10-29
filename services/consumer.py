from typing import Any
from sqlmodel import Session

from models import NotificationJob

def order_paid_handler(
    session: Session,
    payload: dict[str, Any]
):
    job = NotificationJob(
        event_id = payload["event_id"],
        job_type = "send_email",
        payload = payload
    )
    session.add(job)
    session.flush()