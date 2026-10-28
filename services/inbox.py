from sqlmodel import Session, select
from datetime import datetime, timezone

from models import InboxEvent

def process_inbox_event_operation(
    session: Session,
    args: list
):
    assert len(args) == 2
    event_id = args[0]
    event_type = args[1]
    
    inbox_event = InboxEvent(
        event_id=event_id,
        event_type=event_type,
    )
    session.add(inbox_event)
    session.flush()
