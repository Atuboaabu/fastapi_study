from sqlmodel import Session, create_engine, select, func
from sqlalchemy import text
from threading import Thread, Barrier

from services import orders, users
from config import settings
from models import Product, User, OrderItem
from schemas import OrderCreate, OrderItemCreate, UserCreate
from exceptions import InsufficientStockException

demo_engine = create_engine(
    url = settings.database_url,
    pool_size = 2,
    max_overflow = 0,
)

with Session(demo_engine) as session:
    print("=" * 20)
    res = session.execute(text("SHOW transaction_isolation")).scalar_one()
    print(f"transaction_isolation: {res}")

    statement = select(Product).where(
        Product.sku == "Test-SKU-01"
    )
    product = session.exec(statement).first()

    if product is None:
        product = Product(
            sku = "Test-SKU-01",
            name = "Test-Product-01",
            price = 99.9,
            stock = 10,
        )
        try:
            session.add(product)
            session.commit()
        except Exception:
            session.rollback()
            raise
        session.refresh(product)
        print(f"Add Product {product.sku} success:")
        print(f"Product name = {product.name}")
        print(f"Product stock = {product.stock}")
    else:
        try:
            product.stock = 10
            session.commit()
        except Exception:
            session.rollback()
            raise
        session.refresh(product)
        print(f"Get Product {product.sku} success:")
        print(f"Product id = {product.id}")
        print(f"Product name = {product.name}")
        print(f"Set Product stock = {product.stock}")
    
    product_id = product.id

    user = session.exec(select(User).where(User.username == "test-user-1")).first()
    if user is None:
        user_create = UserCreate(
            username = "test-user-1",
            password = "password123"
        )
        
        users.create_user(
            user_create,
            session
        )
    user = session.exec(select(User).where(User.username == "test-user-1")).first()
    user_id = user.id
    print("=" * 20)

    print("Before check:")
    orders_, count = orders.get_all_orders(session)
    print(f"orders count: {count}")

    order_items_count = session.exec(
        select(func.count()).select_from(OrderItem)
    ).one()
    print(f"order_items count: {order_items_count}")

    print("=" * 20)

barrier = Barrier(2)
def worker(
    worker_name: str
):
    print(f"{worker_name} start")
    barrier.wait()
    with Session(demo_engine) as session:    
        order_create = OrderCreate(
            items = [
                OrderItemCreate(
                    product_id = product_id,
                    quantity = 7
                )
            ]
        )

        try:
            order = orders.create_order(
                order_create,
                user_id,
                session
            )
            print(f"{worker_name} create order success")
            print(f"Order id: {order.id}")
            items = order.items
            print(f"Order items:")
            for item in items:
                print(f"item {item.id}: product {item.product_id}, quantity {item.quantity}")
        except InsufficientStockException:
            print(f"{worker_name} catch insufficient stock error")


t1 = Thread(
    target=worker,
    args=("thread-1",)
)
t2 = Thread(
    target=worker,
    args=("thread-2",)
)

t1.start()
t2.start()

t1.join()
t2.join()

with Session(demo_engine) as session:
    print("=" * 20)
    print("After check:")
    product = session.exec(
        select(Product).where(
            Product.sku == "Test-SKU-01"
        )
    ).first()
    assert product is not None

    print(f"product {product.sku} stock = {product.stock}")
    orders_, after_count = orders.get_all_orders(session)
    print(f"orders count: {after_count}")

    after_order_items_count = session.exec(
        select(func.count()).select_from(OrderItem)
    ).one()
    print(f"order_items count: {after_order_items_count}")

    assert after_count - count == 1
    assert after_order_items_count - order_items_count == 1

    print("=" * 20)

## 以上运行输出 ##
# uv run python -m script.create_order_concurrency_demo
# ====================
# transaction_isolation: read committed
# Get Product Test-SKU-01 success:
# Product id = 1
# Product name = Test-Product-01
# Set Product stock = 10
# ====================
# Before check:
# orders count: 0
# order_items count: 0
# ====================
# thread-1 start
# thread-2 start
# thread-2 create order success
# Order id: 10
# Order items:
# item 10: product 1, quantity 7
# thread-1 catch insufficient stock error
# ====================
# After check:
# product Test-SKU-01 stock = 3
# orders count: 1
# order_items count: 1
# ====================