from sqlalchemy.exc import DatabaseError

from session_factory import SessionFactory

def run_transaction(
    session_factory: SessionFactory,
    operation,
    args,
    max_attemps = 3
):
    for attemp in range(max_attemps):
        with session_factory() as session:
            try:
                result = operation(session, args)
                session.commit()
                return result

            except DatabaseError as exc:
                session.rollback()

                if getattr(exc.orig, 'sqlstate', None) != 4001:
                    raise
                if attemp == max_attemps - 1:
                    raise

                continue

            except Exception:
                session.rollback()
                raise