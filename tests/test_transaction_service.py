from sqlmodel import Session, select, func
import pytest

from services import transaction, users, orders, outbox
from services.result import UserResult, OrderResult
from schemas import UserCreate
from models import User, Product, Order, OrderItem, OutboxEvent
from security import verify_password, hash_password
from exceptions import UsernameExistsException
from enums import OrderStatus
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

    with create_session() as session:
        user = session.get(User, user_result.id)
        assert user is not None
        assert user.username == user_data.username
        assert verify_password(user_data.password, user.hashed_password)
        assert user.is_active == True
        assert user.role == "customer"

def test_run_transaction_domain_except(
    engine
):
    user_data = UserCreate(
        username = "customer",
        password = "password123"
    )

    create_session_count = 0

    def create_session():
        nonlocal create_session_count
        create_session_count += 1
        return Session(engine)
    
    args = [user_data]

    user_result: UserResult | None = transaction.run_transaction(
        create_session,
        users.create_user_operation,
        args,
        3
    )
    assert create_session_count == 1
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
    assert create_session_count == 2

def test_run_transaction_dbapi_except_no_40001(
    engine,
    monkeypatch
):
    user_data = UserCreate(
        username = "customer",
        password = "password123"
    )

    create_session_count = 0

    def create_session():
        nonlocal create_session_count
        create_session_count += 1

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
    assert create_session_count == 1
    
def test_run_transaction_dbapi_except_40001_success(
    engine,
    monkeypatch
):
    user_data = UserCreate(
        username = "customer",
        password = "password123"
    )

    create_session_count = 0
    def create_session():
        nonlocal create_session_count
        create_session_count += 1

        session = Session(engine)

        if create_session_count == 1:
            def fail_flush_once():
                    raise DBAPIError(
                        statement=None,
                        params=None,
                        orig=SerializationFailure())


            monkeypatch.setattr(
                session,
                "flush",
                fail_flush_once
            )

        return session
    
    args = [user_data]

    user_result: UserResult | None = transaction.run_transaction(
        create_session,
        users.create_user_operation,
        args,
        3
    )
    assert create_session_count == 2
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

    create_session_count = 0
    def create_session():
        nonlocal create_session_count
        create_session_count += 1

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
    assert create_session_count == 3

def prepare_order_for_test(
    session: Session
):
    product = Product(
        sku = "TEST-SKU-01",
        name = "TEST-PRODUCT-01",
        price = 99.9,
        stock = 100,
        description = "Test Product 01"
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    assert product.id is not None

    customer = User(
        username = "Bob",
        hashed_password = hash_password("password123"),
        role = "customer"
    )
    session.add(customer)

    session.commit()
    session.refresh(customer)

    assert customer.id is not None

    order = Order(
        user_id = customer.id,
        status=OrderStatus.PENDING,
    )
    session.add(order)
    session.flush()
    assert order.id is not None

    items = [
        OrderItem(
            order_id = order.id,
            product_id = product.id,
            quantity = 10
        )
    ]

    for item in items:
        session.add(item)
    
    session.commit()
    return product, customer, order

def test_run_transaction_mark_order_paid_success(
    engine
):
    session_created_count = 0
    def create_session():
        nonlocal session_created_count
        session_created_count += 1
        return Session(engine)
    
    with create_session() as session:
        event_count_old = session.exec(
            select(func.count()).select_from(OutboxEvent)
        ).one()
    assert session_created_count == 1
    
    with create_session() as session:
        _, customer, order = prepare_order_for_test(session)
        order_id = order.id
        user_id = customer.id
    assert session_created_count == 2

    args = [order_id]
    order_result: OrderResult | None = transaction.run_transaction(
        create_session,
        orders.mark_order_paid_operation,
        args,
        3
    )
    assert session_created_count == 3

    assert order_result is not None
    assert order_result.id == order_id
    assert order_result.status == OrderStatus.PAID
    
    with create_session() as session:
        event_count_new = session.exec(
            select(func.count()).select_from(OutboxEvent)
        ).one()

        assert event_count_new - event_count_old == 1

        event = session.exec(
            select(OutboxEvent).where(OutboxEvent.aggregate_id == order_id)
        ).first()

        assert event is not None
        assert event.event_type == "order.paid"
        assert event.aggregate_type == "order"
        assert event.created_at is not None
        assert event.processed_at is None

        assert event.payload["order_id"] == order_id
        assert event.payload["user_id"] == user_id
        assert event.payload["status"] == "paid"

        order_db = session.get(Order, order_id)
        assert order_db is not None
        assert order_db.status == OrderStatus.PAID

    assert session_created_count == 4

def test_run_transaction_mark_order_paid_exception(
    engine
):
    session_created_count = 0
    def create_session():
        nonlocal session_created_count
        session_created_count += 1
        return Session(engine)
    
    with create_session() as session:
        event_count_old = session.exec(
            select(func.count()).select_from(OutboxEvent)
        ).one()
    assert session_created_count == 1
    
    with create_session() as session:
        _, customer, order = prepare_order_for_test(session)
        order_id = order.id
        user_id = customer.id
    assert session_created_count == 2

    def mark_order_paid_except_operation(
        session: Session,
        args: list
    ):
        result = orders.mark_order_paid_operation(session, args)
        raise RuntimeError()
    
    args = [order_id]
    with pytest.raises(
        RuntimeError
    ):
        order_result: OrderResult | None = transaction.run_transaction(
            create_session,
            mark_order_paid_except_operation,
            args,
            3
        )               
    assert session_created_count == 3

    with create_session() as session:
        event_count_new = session.exec(
            select(func.count()).select_from(OutboxEvent)
        ).one()

        assert event_count_new - event_count_old == 0

        event = session.exec(
            select(OutboxEvent).where(OutboxEvent.aggregate_id == order_id)
        ).first()

        assert event is None

        order_db = session.get(Order, order_id)
        assert order_db is not None
        assert order_db.status == OrderStatus.PENDING

    assert session_created_count == 4
    

def test_run_transaction_mark_order_paid_fail_first_attempt(
    engine
):
    session_created_count = 0
    def create_session():
        nonlocal session_created_count
        session_created_count += 1
        return Session(engine)
    
    with create_session() as session:
        event_count_old = session.exec(
            select(func.count()).select_from(OutboxEvent)
        ).one()
    assert session_created_count == 1
    
    with create_session() as session:
        _, customer, order = prepare_order_for_test(session)
        order_id = order.id
        user_id = customer.id
    assert session_created_count == 2

    operation_exec_count = 0
    def mark_order_paid_except_operation(
        session: Session,
        args: list
    ):
        nonlocal operation_exec_count
        operation_exec_count += 1

        result = orders.mark_order_paid_operation(session, args)
        if operation_exec_count == 1:
            raise DBAPIError(
                statement = None,
                params = None,
                orig = SerializationFailure()
            )
        return result

    args = [order_id]
    order_result: OrderResult | None = transaction.run_transaction(
        create_session,
        mark_order_paid_except_operation,
        args,
        3
    )               
    assert session_created_count == 4
    assert operation_exec_count == 2

    assert order_result is not None
    assert order_result.id == order_id
    assert order_result.status == OrderStatus.PAID

    with create_session() as session:
        event_count_new = session.exec(
            select(func.count()).select_from(OutboxEvent)
        ).one()

        assert event_count_new - event_count_old == 1

        event = session.exec(
            select(OutboxEvent).where(OutboxEvent.aggregate_id == order_id)
        ).first()

        assert event is not None
        assert event.event_type == "order.paid"
        assert event.aggregate_type == "order"
        assert event.created_at is not None
        assert event.processed_at is None

        assert event.payload["order_id"] == order_id
        assert event.payload["user_id"] == user_id
        assert event.payload["status"] == "paid"

        order_db = session.get(Order, order_id)
        assert order_db is not None
        assert order_db.status == OrderStatus.PAID

    assert session_created_count == 5

def test_run_transaction_process_outboxevent_success(
    engine
):
    session_created_count = 0
    def create_session():
        nonlocal session_created_count
        session_created_count += 1
        return Session(engine)
    
    with create_session() as session:
        _, customer, order = prepare_order_for_test(session)
        order_id = order.id
        user_id = customer.id

    args = [order_id]
    order_result: OrderResult | None = transaction.run_transaction(
        create_session,
        orders.mark_order_paid_operation,
        args,
        3
    )

    assert order_result is not None
    assert order_result.id == order_id
    assert order_result.status == OrderStatus.PAID
    
    with create_session() as session:
        event = session.exec(
            select(OutboxEvent).where(OutboxEvent.aggregate_id == order_id)
        ).first()

        assert event is not None
        assert event.event_type == "order.paid"
        assert event.aggregate_type == "order"
        assert event.created_at is not None
        assert event.processed_at is None

        assert event.payload["order_id"] == order_id
        assert event.payload["user_id"] == user_id
        assert event.payload["status"] == "paid"
    
    external_messages = []
    def fake_sender(
        outbox_event: OutboxEvent
    ):
        nonlocal external_messages
        external_messages.append(f"event: {outbox_event}")
        return True
    
    external_messages.clear()
    
    assert len(external_messages) == 0

    args = [fake_sender]
    event_result: int | None = transaction.run_transaction(
        create_session,
        outbox.process_one_outbox_event_operation,
        args,
        3
    )
    assert event_result == 1
    assert len(external_messages) == 1

    with create_session() as session:
        event = session.exec(
            select(OutboxEvent).where(OutboxEvent.aggregate_id == order_id)
        ).first()

        assert event is not None
        assert event.event_type == "order.paid"
        assert event.aggregate_type == "order"
        assert event.created_at is not None
        assert event.processed_at is not None

        assert event.payload["order_id"] == order_id
        assert event.payload["user_id"] == user_id
        assert event.payload["status"] == "paid"
    
def test_run_transaction_process_outboxevent_noevent(
    engine
):
    session_created_count = 0
    def create_session():
        nonlocal session_created_count
        session_created_count += 1
        return Session(engine)
    
    with create_session() as session:
        _, customer, order = prepare_order_for_test(session)
        order_id = order.id
        user_id = customer.id
    
    external_messages = []
    def fake_sender(
        outbox_event: OutboxEvent
    ):
        nonlocal external_messages
        external_messages.append(f"event: {outbox_event}")
        return True
    
    external_messages.clear()
    
    assert len(external_messages) == 0

    args = [fake_sender]
    event_result: int | None = transaction.run_transaction(
        create_session,
        outbox.process_one_outbox_event_operation,
        args,
        3
    )
    assert event_result == 0
    assert len(external_messages) == 0

def test_run_transaction_process_outboxevent_exception(
    engine
):
    session_created_count = 0
    def create_session():
        nonlocal session_created_count
        session_created_count += 1
        return Session(engine)
    
    with create_session() as session:
        _, customer, order = prepare_order_for_test(session)
        order_id = order.id
        user_id = customer.id

    args = [order_id]
    order_result: OrderResult | None = transaction.run_transaction(
        create_session,
        orders.mark_order_paid_operation,
        args,
        3
    )

    assert order_result is not None
    assert order_result.id == order_id
    assert order_result.status == OrderStatus.PAID
    
    with create_session() as session:
        event = session.exec(
            select(OutboxEvent).where(OutboxEvent.aggregate_id == order_id)
        ).first()

        assert event is not None
        assert event.event_type == "order.paid"
        assert event.aggregate_type == "order"
        assert event.created_at is not None
        assert event.processed_at is None

        assert event.payload["order_id"] == order_id
        assert event.payload["user_id"] == user_id
        assert event.payload["status"] == "paid"
    
    external_messages = []
    def fake_sender(
        outbox_event: OutboxEvent
    ):
        raise RuntimeError()
    
    external_messages.clear()
    
    assert len(external_messages) == 0

    args = [fake_sender]

    with pytest.raises(
        RuntimeError
    ):
        event_result: int | None = transaction.run_transaction(
            create_session,
            outbox.process_one_outbox_event_operation,
            args,
            3
        )

    assert len(external_messages) == 0

    with create_session() as session:
        event = session.exec(
            select(OutboxEvent).where(OutboxEvent.aggregate_id == order_id)
        ).first()

        assert event is not None
        assert event.event_type == "order.paid"
        assert event.aggregate_type == "order"
        assert event.created_at is not None
        assert event.processed_at is None

        assert event.payload["order_id"] == order_id
        assert event.payload["user_id"] == user_id
        assert event.payload["status"] == "paid"

def test_run_transaction_process_outboxevent_exception_after(
    engine
):
    session_created_count = 0
    def create_session():
        nonlocal session_created_count
        session_created_count += 1
        return Session(engine)
    
    with create_session() as session:
        _, customer, order = prepare_order_for_test(session)
        order_id = order.id
        user_id = customer.id

    args = [order_id]
    order_result: OrderResult | None = transaction.run_transaction(
        create_session,
        orders.mark_order_paid_operation,
        args,
        3
    )

    assert order_result is not None
    assert order_result.id == order_id
    assert order_result.status == OrderStatus.PAID
    
    with create_session() as session:
        event = session.exec(
            select(OutboxEvent).where(OutboxEvent.aggregate_id == order_id)
        ).first()

        assert event is not None
        assert event.event_type == "order.paid"
        assert event.aggregate_type == "order"
        assert event.created_at is not None
        assert event.processed_at is None

        assert event.payload["order_id"] == order_id
        assert event.payload["user_id"] == user_id
        assert event.payload["status"] == "paid"
    
    def process_one_outbox_event_operation_except(
        session: Session,
        args: list
    ):
        result = outbox.process_one_outbox_event_operation(
            session,
            args
        )
        raise RuntimeError()
    
    external_messages = []
    def fake_sender(
        outbox_event: OutboxEvent
    ):
        nonlocal external_messages
        external_messages.append(f"event: {outbox_event}")
        return True
    
    external_messages.clear()
    
    assert len(external_messages) == 0

    args = [fake_sender]
    with pytest.raises(
        RuntimeError
    ):
        event_result: int | None = transaction.run_transaction(
            create_session,
            process_one_outbox_event_operation_except,
            args,
            3
        )

    assert len(external_messages) == 1

    with create_session() as session:
        event = session.exec(
            select(OutboxEvent).where(OutboxEvent.aggregate_id == order_id)
        ).first()

        assert event is not None
        assert event.event_type == "order.paid"
        assert event.aggregate_type == "order"
        assert event.created_at is not None
        assert event.processed_at is None

        assert event.payload["order_id"] == order_id
        assert event.payload["user_id"] == user_id
        assert event.payload["status"] == "paid"
    
