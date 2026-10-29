from sqlmodel import Session, select
from datetime import datetime, timezone

from models import NotificationJob

def process_one_notification_operation(
    session: Session,
    args: list
):
    assert len(args) == 1
    processer = args[0]
    
    statement = select(NotificationJob).where(
        NotificationJob.processed_at.is_(None)
    ).order_by(
        NotificationJob.id
    ).limit(1).with_for_update(skip_locked=True)
    notification = session.exec(statement).first()

    if notification is None:
        return 0
    
    processer(notification)

    notification.processed_at = datetime.now(timezone.utc)

    session.flush()
    return 1
