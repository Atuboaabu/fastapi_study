from sqlmodel import Session
from sqlalchemy.dialects.postgresql import insert
from models import InboxEvent

def process_inbox_event_operation(
    session: Session,
    args: list
):
    assert len(args) == 4
    event_id = args[0]
    event_type = args[1]
    handler = args[2]
    payload = args[3]

    statement = insert(InboxEvent).values(
        event_id=event_id,
        event_type=event_type,
    ).on_conflict_do_nothing(
        index_elements = [InboxEvent.event_id]
    ).returning(InboxEvent.id)

    inbox_event_id = session.exec(statement).one_or_none()

    if inbox_event_id is None:
        return "already_processed"
    
    handler_payload = payload
    handler_payload["event_id"] = event_id
    handler(session, handler_payload)
    return "processed"
    