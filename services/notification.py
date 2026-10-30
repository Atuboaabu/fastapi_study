from sqlmodel import Session, select, func
from sqlalchemy import or_
from datetime import datetime, timezone, timedelta

from models import NotificationJob
from exceptions import RetryableNotificationException, PermanentNotificationException
from services.result import NotificationJobClaim

def process_one_notification_operation(
    session: Session,
    args: list
):
    assert len(args) == 3
    processor = args[0]
    max_attempts = args[1]
    base_delay_seconds = args[2]
    
    statement = select(NotificationJob).where(
        NotificationJob.processed_at.is_(None),
        NotificationJob.failed_at.is_(None),
        NotificationJob.next_attempt_at <= func.now()
    ).order_by(
        NotificationJob.id
    ).limit(1).with_for_update(skip_locked=True)
    notification = session.exec(statement).first()

    if notification is None:
        return 0
    
    try:
        processor(notification)
        notification.processed_at = datetime.now(timezone.utc)
    except RetryableNotificationException as exc:
        notification.retry_count += 1
        notification.last_error = str(exc)
        if notification.retry_count < max_attempts:
            delay_seconds = base_delay_seconds * (2 ** (notification.retry_count - 1))
            notification.next_attempt_at = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
            session.flush()
            return "scheduled_delay"
        else:
            notification.failed_at = datetime.now(timezone.utc)
            session.flush()
            return "failed"
    except PermanentNotificationException as exc:
        notification.retry_count += 1
        notification.last_error = str(exc)
        notification.failed_at = datetime.now(timezone.utc)
        session.flush()
        return "failed"

    session.flush()
    return "processed"

def claim_one_notification_operation(
    session: Session,
    args: list
):
    assert len(args) == 2
    worker_id = args[0]
    lease_seconds = args[1]
    
    statement = select(NotificationJob).where(
        NotificationJob.processed_at.is_(None),
        NotificationJob.failed_at.is_(None),
        NotificationJob.next_attempt_at <= func.now(),
        or_(
            NotificationJob.lease_until.is_(None),
            NotificationJob.lease_until <= func.now()
        )
    ).order_by(
        NotificationJob.id
    ).limit(1).with_for_update(skip_locked=True)
    notification = session.exec(statement).first()

    if notification is None:
        return None
    
    notification.lease_until = datetime.now(timezone.utc) + timedelta(seconds=lease_seconds)
    notification.claimed_by = worker_id

    assert notification.id is not None

    session.flush()
    return NotificationJobClaim(
        id=notification.id,
        event_id=notification.event_id,
        job_type=notification.job_type,
        payload=notification.payload,
        created_at=notification.created_at,
        processed_at=notification.processed_at,
        retry_count=notification.retry_count,
        next_attempt_at=notification.next_attempt_at,
        last_error=notification.last_error,
        failed_at=notification.failed_at,
        lease_until=notification.lease_until,
        claimed_by=notification.claimed_by,
        claim_version=notification.claim_version
    )
