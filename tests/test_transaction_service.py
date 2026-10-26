from sqlmodel import Session
import pytest

from services import transaction, users
from services.result import UserResult
from schemas import UserCreate
from security import verify_password
from exceptions import UsernameExistsException
from sqlalchemy.exc import DBAPIError
from psycopg.errors import DeadlockDetected, SerializationFailure

def test_run_transaction_success(
    engine
):
    user_data = UserCreate(
        username = "customer",
        password = "password123"
    )

    def create_session():
        return Session(engine)
    
    args = [user_data]

    user_result: UserResult | None = transaction.run_transaction(
        create_session,
        users.create_user_operation,
        args,
        3
    )
    assert user_result is not None
    assert user_result.id is not None
    assert user_result.username == user_data.username
    assert verify_password(user_data.password, user_result.hashed_password)
    assert user_result.is_active == True
    assert user_result.role == "customer"

def test_run_transaction_domain_except(
    engine
):
    user_data = UserCreate(
        username = "customer",
        password = "password123"
    )

    def create_session():
        return Session(engine)
    
    args = [user_data]

    user_result: UserResult | None = transaction.run_transaction(
        create_session,
        users.create_user_operation,
        args,
        3
    )
    assert user_result is not None
    assert user_result.id is not None
    assert user_result.username == user_data.username
    assert verify_password(user_data.password, user_result.hashed_password)
    assert user_result.is_active == True
    assert user_result.role == "customer"

    with pytest.raises(
        UsernameExistsException
    ):
        user_result_dup: UserResult | None = transaction.run_transaction(
            create_session,
            users.create_user_operation,
            args,
            3
        )
        assert user_result_dup is None

def test_run_transaction_dbapi_except_no_40001(
    engine,
    monkeypatch
):
    user_data = UserCreate(
        username = "customer",
        password = "password123"
    )

    def create_session():
        session = Session(engine)

        def fail_flush():
            raise DBAPIError(
                statement=None,
                params=None,
                orig=DeadlockDetected())

        monkeypatch.setattr(
            session,
            "flush",
            fail_flush
        )

        return session
    
    args = [user_data]

    with pytest.raises(
        DBAPIError
    ):
        user_result: UserResult | None = transaction.run_transaction(
            create_session,
            users.create_user_operation,
            args,
            3
        )
        assert user_result is None
    
def test_run_transaction_dbapi_except_40001_success(
    engine,
    monkeypatch
):
    user_data = UserCreate(
        username = "customer",
        password = "password123"
    )

    def create_session():
        session = Session(engine)

        class Counter:
            count = 0

        def fail_flush_once():
            if Counter.count < 1:
                Counter.count += 1
                raise DBAPIError(
                    statement=None,
                    params=None,
                    orig=SerializationFailure())

            session.flush()

        monkeypatch.setattr(
            session,
            "flush",
            fail_flush_once
        )

        return session
    
    args = [user_data]

    with pytest.raises(
        DBAPIError
    ):
        user_result: UserResult | None = transaction.run_transaction(
            create_session,
            users.create_user_operation,
            args,
            3
        )
        assert user_result is not None
        assert user_result.id is not None
        assert user_result.username == user_data.username
        assert verify_password(user_data.password, user_result.hashed_password)
        assert user_result.is_active == True
        assert user_result.role == "customer"

def test_run_transaction_dbapi_except_40001_failed(
    engine,
    monkeypatch
):
    user_data = UserCreate(
        username = "customer",
        password = "password123"
    )

    def create_session():
        session = Session(engine)

        def fail_flush():
            raise DBAPIError(
                statement=None,
                params=None,
                orig=SerializationFailure())

        monkeypatch.setattr(
            session,
            "flush",
            fail_flush
        )

        return session
    
    args = [user_data]

    with pytest.raises(
        DBAPIError
    ):
        user_result: UserResult | None = transaction.run_transaction(
            create_session,
            users.create_user_operation,
            args,
            3
        )
        assert user_result is None