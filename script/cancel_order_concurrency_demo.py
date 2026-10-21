from sqlmodel import create_engine, Session, select
from threading import Thread, Barrier
from concurrent.futures import ThreadPoolExecutor

from config import settings
from models import Product, User, Order
from schemas import OrderCreate, OrderItemCreate, UserCreate
from services import orders, users
from exceptions import InvalidOrderStateTransitionException
from enums import OrderStatus
from order_state import ALLOWED_ORDER_TRANSITIONS

demo_engine = create_engine(
    url = settings.database_url,
    pool_size = 2,
    max_overflow = 0
)

with Session(demo_engine) as session:
    product = session.exec(
        select(Product).where(
            Product.sku == "Test-SKU-01"
        )
    ).first()

    if product is None:
        try:
            product = Product(
                sku = "Test-SKU-01",
                name = "Test-Product-01",
                price = 99.9,
                stock = 10,
            )
            session.add(product)
            session.commit()
        except Exception:
            session.rollback()
            raise
    else:
        try:
            product.stock = 10
            session.commit()
        except Exception:
            session.rollback()
            raise
    session.refresh(product)

    assert product.id is not None

    user = session.exec(
        select(User).where(
            User.username == "test-user-1"
        )
    ).first()

    if user is None:
        user_data = UserCreate(
            username = "test-user-1",
            password = "password123"
        )
        user = users.create_user(
            user_data,
            session
        )
    assert user.id is not None
    user_id = user.id

    order_data = OrderCreate(
        items = [
            OrderItemCreate(
                product_id = product.id,
                quantity = 7
            )
        ]
    )

    order = orders.create_order(
        order_data,
        user.id,
        session
    )
    assert order.id is not None
    print(f"Order {order.id} created, status = {order.status}")
    order_id = order.id

# 替换 is_order_transition_allowed 接口，构造cancel_order接口的concurrency场景
barrier = Barrier(2)
def is_order_transition_allowed_synchronized(
    current_status: OrderStatus,
    dest_status: OrderStatus
)->bool:
    barrier.wait()
    return dest_status in ALLOWED_ORDER_TRANSITIONS[current_status]

orders.is_order_transition_allowed = is_order_transition_allowed_synchronized

def worker(worker_name: str):
    print(f"{worker_name} start")

    with Session(demo_engine) as session:
        try:
            orders.cancel_order_for_user(
                order_id,
                user_id,
                session
            )
            return "success"
        except InvalidOrderStateTransitionException:
            return "invalid_transition"

with ThreadPoolExecutor(max_workers=2) as executor:
    future1 = executor.submit(worker, "thread-1")
    future2 = executor.submit(worker, "thread-2")

    results = [
        future1.result(),
        future2.result()
    ]
    
    print(results)

with Session(demo_engine) as session:
    print("After Check:")
    product_after = session.exec(
        select(Product).where(
            Product.sku == "Test-SKU-01"
        )
    ).first()
    assert product_after is not None
    print(f"Product {product_after.sku} stock = {product_after.stock}")

    order_after = session.get(Order, order_id)
    assert order_after is not None
    print(f"Order {order_after.id} status = {order_after.status}")

## 以上运行输出 ##
# uv run python -m script.cancel_order_concurrency_demo
# Order 20 created, status = OrderStatus.PENDING
# thread-1 start
# thread-2 start
# ['success', 'success']
# After Check:
# Product Test-SKU-01 stock = 10
# Order 20 status = OrderStatus.CANCELLED

            