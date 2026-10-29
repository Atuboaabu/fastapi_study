from typing import Any
from sqlmodel import Session

from models import NotificationJob

def order_paid_handler(
    session: Session,
    event_id: int,
    payload: dict[str, Any]
):
    job = NotificationJob(
        event_id = event_id,
        job_type = "send_email",
        payload = payload
    )
    session.add(job)
    session.flush()