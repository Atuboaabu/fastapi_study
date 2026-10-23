from sqlalchemy.exc import DBAPIError
from pydantic import Field

from session_factory import SessionFactory

def run_transaction(
    session_factory: SessionFactory,
    operation,
    args,
    max_attempts: int = Field(default=3, gt = 0)
):
    for attemp in range(max_attempts):
        with session_factory() as session:
            try:
                result = operation(session, args)
                session.commit()
                return result

            except DBAPIError as exc:
                session.rollback()

                if getattr(exc.orig, 'sqlstate', None) != "40001":
                    raise
                if attemp == max_attempts - 1:
                    raise

                continue

            except Exception:
                session.rollback()
                raise