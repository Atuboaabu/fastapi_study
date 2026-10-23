from sqlmodel import Session
from psycopg.errors import SerializationFailure

from database import engine

def run_transaction(
    operation,
    args,
    max_attemps
):
    for attemp in range(max_attemps):
        with Session(engine) as session:
            try:
                result = operation(session, args)
                session.commit()
            except SerializationFailure:
                session.rollback()
                continue
            except Exception:
                session.rollback()
                raise
            break

        return result