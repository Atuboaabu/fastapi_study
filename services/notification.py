from sqlmodel import Session, select
from datetime import datetime, timezone, timedelta

from models import NotificationJob
from exceptions import RetryableNotificationException, PermanentNotificationException

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
        NotificationJob.next_attempt_at <= datetime.now(timezone.utc)
    ).order_by(
        NotificationJob.id
    ).limit(1).with_for_update(skip_locked=True)
    notification = session.exec(statement).first()

    if notification is None:
        return 0
    
    try:
        processor(notification)
        notification.processed_at = datetime.now(timezone.utc)
    except RetryableNotificationException:
        notification.retry_count += 1
        if notification.retry_count <= max_attempts:
            notification.last_error = f"retryable failure"
            delay_seconds = base_delay_seconds * (2 ** (notification.retry_count - 1))
            notification.next_attempt_at = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
            session.flush()
            return "scheduled_delay"
        else:
            notification.last_error = f"retry max attempts failure"
            notification.failed_at = datetime.now(timezone.utc)
            session.flush()
            return "failed"
    except PermanentNotificationException:
        notification.retry_count += 1
        notification.last_error = f"unretryable exception failure"
        notification.failed_at = datetime.now(timezone.utc)
        session.flush()
        return "failed"

    session.flush()
    return "processed"
