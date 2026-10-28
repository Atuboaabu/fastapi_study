from sqlmodel import Session, select
from datetime import datetime, timezone

from models import OutboxEvent

def process_one_outbox_event_operation(
    session: Session,
    args: list
):
    assert len(args) == 1
    processer = args[0]
    
    statement = select(OutboxEvent).where(
        OutboxEvent.processed_at.is_(None)
    ).order_by(
        OutboxEvent.id
    ).limit(1).with_for_update(skip_locked=True)
    outbox_event = session.exec(statement).first()

    if outbox_event is None:
        return 0
    
    processer(outbox_event)

    outbox_event.processed_at = datetime.now(timezone.utc)

    session.flush()
    return 1
