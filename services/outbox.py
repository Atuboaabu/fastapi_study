from sqlmodel import Session, select
from datetime import datetime, timezone

from models import OutboxEvent

external_messages = []
def fake_sender(
    msg: str
):
    global external_messages
    external_messages.append(msg)

def process_one_outbox_event_operation(
    session: Session,
    args: list
):
    
    statement = select(OutboxEvent).where(
        OutboxEvent.processed_at == None
    )
    outbox_event = session.exec(statement).first()
    if outbox_event is None:
        return 0
    
    msg = (f"event processed: event id: {outbox_event.id}, "
        + f"event type: {outbox_event.event_type}, "
        + f"aggregate type: {outbox_event.aggregate_type}, "
        + f"aggregate id: {outbox_event.aggregate_id}")
    
    fake_sender(msg)
    outbox_event.processed_at = datetime.now(timezone.utc)

    session.flush()
    return 1
