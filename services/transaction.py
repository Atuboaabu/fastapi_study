from sqlalchemy.exc import DBAPIError
from sqlmodel import Session

from session_factory import SessionFactory

def run_transaction_with_retry(
    session_factory: SessionFactory,
    operation,
    args,
    max_attempts: int = 3
):
    if max_attempts < 1:
        raise ValueError()

    for attempt in range(max_attempts):
        with session_factory() as session:
            try:
                result = operation(session, args)
                session.commit()
                return result

            except DBAPIError as exc:
                session.rollback()

                if getattr(exc.orig, 'sqlstate', None) != "40001":
                    raise
                if attempt == max_attempts - 1:
                    raise

                continue

            except Exception:
                session.rollback()
                raise

def run_transaction_once(
    session: Session,
    operation,
    args,
):
    try:
        result = operation(session, args)
        session.commit()
        return result

    except Exception:
        session.rollback()
        raise