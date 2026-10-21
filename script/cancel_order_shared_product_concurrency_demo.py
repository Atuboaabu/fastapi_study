from sqlmodel import create_engine, Session, select
# from threading import Thread, Barrier
from concurrent.futures import ThreadPoolExecutor

from config import settings
from models import Product, User, Order
from schemas import OrderCreate, OrderItemCreate, UserCreate
from services import orders, users
from exceptions import InvalidOrderStateTransitionException
# from enums import OrderStatus
# from order_state import ALLOWED_ORDER_TRANSITIONS

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
                stock = 20,
            )
            session.add(product)
            session.commit()
        except Exception:
            session.rollback()
            raise
    else:
        try:
            product.stock = 20
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

    order_data_1 = OrderCreate(
        items = [
            OrderItemCreate(
                product_id = product.id,
                quantity = 7
            )
        ]
    )

    order_1 = orders.create_order(
        order_data_1,
        user.id,
        session
    )
    assert order_1.id is not None
    print(f"Order 1 {order_1.id} created, status = {order_1.status}")
    order_1_id = order_1.id

    order_data_2 = OrderCreate(
        items = [
            OrderItemCreate(
                product_id = product.id,
                quantity = 9
            )
        ]
    )

    order_2 = orders.create_order(
        order_data_2,
        user.id,
        session
    )
    assert order_2.id is not None
    print(f"Order 2 {order_2.id} created, status = {order_2.status}")
    order_2_id = order_2.id

def worker(worker_name: str, order_id: int):
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
    future1 = executor.submit(worker, "thread-1", order_1_id)
    future2 = executor.submit(worker, "thread-2", order_2_id)

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

    order_1_after = session.get(Order, order_1_id)
    assert order_1_after is not None
    print(f"Order 1 {order_1_after.id} status = {order_1_after.status}")

    order_2_after = session.get(Order, order_2_id)
    assert order_2_after is not None
    print(f"Order 2 {order_2_after.id} status = {order_2_after.status}")
            