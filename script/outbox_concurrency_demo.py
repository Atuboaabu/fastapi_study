from threading import Thread, Event
from sqlmodel import select

from script.test_utils import create_test_order
from services import transaction, orders, outbox
from session_factory import create_session
from models import OutboxEvent


order = create_test_order()

args = [order.id]
order_result = transaction.run_transaction(
    create_session,
    orders.mark_order_paid_operation,
    args,
    3
)

event1 = Event()
event2 = Event()
def sender(outbox_event: OutboxEvent):
    event2.set()
    event1.wait()
    print(f"send msg: event {outbox_event.aggregate_id} executed! aggregate_type: {outbox_event.aggregate_type}")

args = [sender]
def worker_1(
    worker_name: str
):
    print(f"{worker_name} start work")
    result = transaction.run_transaction(
        create_session,
        outbox.process_one_outbox_event_operation,
        args,
        3
    )

def worker_2(
    worker_name: str
):
    print(f"{worker_name} start work")
    result = transaction.run_transaction(
        create_session,
        outbox.process_one_outbox_event_operation,
        args,
        3
    )
    event1.set()

t1 = Thread(
    target=worker_1,
    args = ("worker-1", )
)
t2 = Thread(
    target=worker_2,
    args = ("worker-2", )
)
t1.start()
event2.wait()
t2.start()

t1.join()
t2.join()

with create_session() as session:
    event = session.exec(
        select(OutboxEvent).where(OutboxEvent.aggregate_id == order.id)
    ).first()

    assert event is not None
    assert event.event_type == "order.paid"
    assert event.aggregate_type == "order"
    assert event.created_at is not None
    assert event.processed_at is not None

    assert event.payload["order_id"] == order.id
    assert event.payload["status"] == "paid"

# 以上运行输出
# uv run python -m script.outbox_concurrency_demo
# 2026-10-28 15:05:47,199 INFO sqlalchemy.engine.Engine select pg_catalog.version()
# 2026-10-28 15:05:47,199 INFO sqlalchemy.engine.Engine [raw sql] {}
# 2026-10-28 15:05:47,202 INFO sqlalchemy.engine.Engine select current_schema()
# 2026-10-28 15:05:47,202 INFO sqlalchemy.engine.Engine [raw sql] {}
# 2026-10-28 15:05:47,205 INFO sqlalchemy.engine.Engine show standard_conforming_strings
# 2026-10-28 15:05:47,205 INFO sqlalchemy.engine.Engine [raw sql] {}
# 2026-10-28 15:05:47,212 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2026-10-28 15:05:47,236 INFO sqlalchemy.engine.Engine SELECT product.sku, product.name, product.price, product.stock, product.description, product.id 
# FROM product 
# WHERE product.sku = %(sku_1)s::VARCHAR
# 2026-10-28 15:05:47,236 INFO sqlalchemy.engine.Engine [generated in 0.00061s] {'sku_1': 'TEST-SKU-01'}
# 2026-10-28 15:05:47,244 INFO sqlalchemy.engine.Engine INSERT INTO product (sku, name, price, stock, description) VALUES (%(sku)s::VARCHAR, %(name)s::VARCHAR, %(price)s, %(stock)s::INTEGER, %(description)s::VARCHAR) RETURNING product.id
# 2026-10-28 15:05:47,244 INFO sqlalchemy.engine.Engine [generated in 0.00028s] {'sku': 'TEST-SKU-01', 'name': 'TEST-PRODUCT-01', 'price': 99.9, 'stock': 100, 'description': None}
# 2026-10-28 15:05:47,249 INFO sqlalchemy.engine.Engine COMMIT
# 2026-10-28 15:05:47,254 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2026-10-28 15:05:47,257 INFO sqlalchemy.engine.Engine SELECT product.sku, product.name, product.price, product.stock, product.description, product.id 
# FROM product 
# WHERE product.id = %(pk_1)s::INTEGER
# 2026-10-28 15:05:47,257 INFO sqlalchemy.engine.Engine [generated in 0.00034s] {'pk_1': 3}
# 2026-10-28 15:05:47,260 INFO sqlalchemy.engine.Engine ROLLBACK
# 2026-10-28 15:05:47,262 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2026-10-28 15:05:47,264 INFO sqlalchemy.engine.Engine SELECT users.id, users.username, users.hashed_password, users.is_active, users.role 
# FROM users 
# WHERE users.username = %(username_1)s::VARCHAR
# 2026-10-28 15:05:47,264 INFO sqlalchemy.engine.Engine [generated in 0.00045s] {'username_1': 'customer-user-01'}
# 2026-10-28 15:05:47,380 INFO sqlalchemy.engine.Engine INSERT INTO users (username, hashed_password, is_active, role) VALUES (%(username)s::VARCHAR, %(hashed_password)s::VARCHAR, %(is_active)s, %(role)s::VARCHAR) RETURNING users.id
# 2026-10-28 15:05:47,380 INFO sqlalchemy.engine.Engine [generated in 0.00058s] {'username': 'customer-user-01', 'hashed_password': '$argon2id$v=19$m=65536,t=3,p=4$VZ3L8U9pLJBdZygGoMbAdg$EA36CTj63G/OSvkSxWjlEoHcU0PqS1VMMX7v8wn396c', 'is_active': True, 'role': 'customer'}
# 2026-10-28 15:05:47,383 INFO sqlalchemy.engine.Engine COMMIT
# 2026-10-28 15:05:47,385 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2026-10-28 15:05:47,386 INFO sqlalchemy.engine.Engine SELECT users.id, users.username, users.hashed_password, users.is_active, users.role 
# FROM users 
# WHERE users.id = %(pk_1)s::INTEGER
# 2026-10-28 15:05:47,386 INFO sqlalchemy.engine.Engine [generated in 0.00024s] {'pk_1': 11}
# 2026-10-28 15:05:47,389 INFO sqlalchemy.engine.Engine ROLLBACK
# 2026-10-28 15:05:47,425 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2026-10-28 15:05:47,426 INFO sqlalchemy.engine.Engine SELECT orders.id, orders.user_id, orders.status 
# FROM orders 
# WHERE orders.user_id = %(user_id_1)s::INTEGER
# 2026-10-28 15:05:47,427 INFO sqlalchemy.engine.Engine [generated in 0.00031s] {'user_id_1': 11}
# 2026-10-28 15:05:47,431 INFO sqlalchemy.engine.Engine INSERT INTO orders (user_id, status) VALUES (%(user_id)s::INTEGER, %(status)s) RETURNING orders.id
# 2026-10-28 15:05:47,432 INFO sqlalchemy.engine.Engine [generated in 0.00024s] {'user_id': 11, 'status': 'pending'}
# 2026-10-28 15:05:47,436 INFO sqlalchemy.engine.Engine SELECT orders.id, orders.user_id, orders.status 
# FROM orders 
# WHERE orders.id = %(pk_1)s::INTEGER
# 2026-10-28 15:05:47,436 INFO sqlalchemy.engine.Engine [generated in 0.00024s] {'pk_1': 49}
# 2026-10-28 15:05:47,439 INFO sqlalchemy.engine.Engine INSERT INTO order_items (order_id, product_id, quantity) VALUES (%(order_id)s::INTEGER, %(product_id)s::INTEGER, %(quantity)s::INTEGER) RETURNING order_items.id
# 2026-10-28 15:05:47,439 INFO sqlalchemy.engine.Engine [generated in 0.00020s] {'order_id': 49, 'product_id': 3, 'quantity': 10}
# 2026-10-28 15:05:47,443 INFO sqlalchemy.engine.Engine COMMIT
# 2026-10-28 15:05:47,445 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2026-10-28 15:05:47,446 INFO sqlalchemy.engine.Engine SELECT orders.id, orders.user_id, orders.status 
# FROM orders 
# WHERE orders.id = %(pk_1)s::INTEGER
# 2026-10-28 15:05:47,446 INFO sqlalchemy.engine.Engine [cached since 0.009869s ago] {'pk_1': 49}
# 2026-10-28 15:05:47,448 INFO sqlalchemy.engine.Engine ROLLBACK
# 2026-10-28 15:05:47,449 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2026-10-28 15:05:47,450 INFO sqlalchemy.engine.Engine SELECT orders.id, orders.user_id, orders.status 
# FROM orders 
# WHERE orders.id = %(id_1)s::INTEGER FOR UPDATE
# 2026-10-28 15:05:47,450 INFO sqlalchemy.engine.Engine [generated in 0.00024s] {'id_1': 49}
# 2026-10-28 15:05:47,455 INFO sqlalchemy.engine.Engine UPDATE orders SET status=%(status)s WHERE orders.id = %(orders_id)s::INTEGER
# 2026-10-28 15:05:47,455 INFO sqlalchemy.engine.Engine [generated in 0.00035s] {'status': 'paid', 'orders_id': 49}
# 2026-10-28 15:05:47,459 INFO sqlalchemy.engine.Engine INSERT INTO outbox_events (event_type, aggregate_type, aggregate_id, payload, processed_at) VALUES (%(event_type)s::VARCHAR, %(aggregate_type)s::VARCHAR, %(aggregate_id)s::INTEGER, %(payload)s::JSONB, %(processed_at)s::TIMESTAMP WITH TIME ZONE) RETURNING outbox_events.id, outbox_events.created_at
# 2026-10-28 15:05:47,459 INFO sqlalchemy.engine.Engine [generated in 0.00053s] {'event_type': 'order.paid', 'aggregate_type': 'order', 'aggregate_id': 49, 'payload': Jsonb({'order_id': 49, 'user_id': 11, 'st ... (49 chars)), 'processed_at': None}
# 2026-10-28 15:05:47,469 INFO sqlalchemy.engine.Engine SELECT order_items.id AS order_items_id, order_items.order_id AS order_items_order_id, order_items.product_id AS order_items_product_id, order_items.quantity AS order_items_quantity 
# FROM order_items 
# WHERE %(param_1)s::INTEGER = order_items.order_id
# 2026-10-28 15:05:47,469 INFO sqlalchemy.engine.Engine [generated in 0.00048s] {'param_1': 49}
# 2026-10-28 15:05:47,471 INFO sqlalchemy.engine.Engine COMMIT
# worker-1 start work
# worker-2 start work
# 2026-10-28 15:05:47,474 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2026-10-28 15:05:47,477 INFO sqlalchemy.engine.Engine SELECT outbox_events.id, outbox_events.event_type, outbox_events.aggregate_type, outbox_events.aggregate_id, outbox_events.payload, outbox_events.created_at, outbox_events.processed_at 
# FROM outbox_events 
# WHERE outbox_events.processed_at IS NULL ORDER BY outbox_events.id 
#  LIMIT %(param_1)s::INTEGER
# 2026-10-28 15:05:47,477 INFO sqlalchemy.engine.Engine [generated in 0.00033s] {'param_1': 1}
# 2026-10-28 15:05:47,490 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2026-10-28 15:05:47,491 INFO sqlalchemy.engine.Engine SELECT outbox_events.id, outbox_events.event_type, outbox_events.aggregate_type, outbox_events.aggregate_id, outbox_events.payload, outbox_events.created_at, outbox_events.processed_at 
# FROM outbox_events 
# WHERE outbox_events.processed_at IS NULL ORDER BY outbox_events.id 
#  LIMIT %(param_1)s::INTEGER
# 2026-10-28 15:05:47,491 INFO sqlalchemy.engine.Engine [cached since 0.01398s ago] {'param_1': 1}
# send msg: event 49 executed! aggregate_type: order
# 2026-10-28 15:05:47,495 INFO sqlalchemy.engine.Engine UPDATE outbox_events SET processed_at=%(processed_at)s::TIMESTAMP WITH TIME ZONE WHERE outbox_events.id = %(outbox_events_id)s::INTEGER
# 2026-10-28 15:05:47,495 INFO sqlalchemy.engine.Engine [generated in 0.00017s] {'processed_at': datetime.datetime(2026, 10, 28, 7, 5, 47, 495359, tzinfo=datetime.timezone.utc), 'outbox_events_id': 1}
# send msg: event 49 executed! aggregate_type: order
# 2026-10-28 15:05:47,496 INFO sqlalchemy.engine.Engine UPDATE outbox_events SET processed_at=%(processed_at)s::TIMESTAMP WITH TIME ZONE WHERE outbox_events.id = %(outbox_events_id)s::INTEGER
# 2026-10-28 15:05:47,496 INFO sqlalchemy.engine.Engine [cached since 0.001103s ago] {'processed_at': datetime.datetime(2026, 10, 28, 7, 5, 47, 496238, tzinfo=datetime.timezone.utc), 'outbox_events_id': 1}
# 2026-10-28 15:05:47,497 INFO sqlalchemy.engine.Engine COMMIT
# 2026-10-28 15:05:47,499 INFO sqlalchemy.engine.Engine COMMIT
# 2026-10-28 15:05:47,501 INFO sqlalchemy.engine.Engine BEGIN (implicit)
# 2026-10-28 15:05:47,502 INFO sqlalchemy.engine.Engine SELECT outbox_events.id, outbox_events.event_type, outbox_events.aggregate_type, outbox_events.aggregate_id, outbox_events.payload, outbox_events.created_at, outbox_events.processed_at 
# FROM outbox_events 
# WHERE outbox_events.aggregate_id = %(aggregate_id_1)s::INTEGER
# 2026-10-28 15:05:47,502 INFO sqlalchemy.engine.Engine [generated in 0.00031s] {'aggregate_id_1': 49}
# 2026-10-28 15:05:47,505 INFO sqlalchemy.engine.Engine ROLLBACK
