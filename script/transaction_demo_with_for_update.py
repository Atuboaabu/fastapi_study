from sqlmodel import create_engine, Session, select
from sqlalchemy import text
from threading import Event, Thread
import time

from config import settings
from models import Product

demo_engine = create_engine(
    url = settings.database_url,
    pool_size = 2,
    max_overflow = 0,
)

with Session(demo_engine) as session:
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
        print(f"Product name = {product.name}")
        print(f"Set Product stock = {product.stock}")

lock_event = Event()
def buy_product_test(worker_name: str):
    print(f"{worker_name} in")
    if worker_name == "thread-2":
        lock_event.wait()

    with Session(demo_engine) as session:
        start = time.perf_counter()
        product = session.exec(
            select(Product).where(
                Product.sku == "Test-SKU-01"
            ).with_for_update()
        ).first()
        elapsed = time.perf_counter() - start
        print(f"{worker_name} exec time cost: {elapsed}")
        assert product is not None

        if worker_name == "thread-1":
            lock_event.set()
            time.sleep(2)

        print(f"{worker_name} ready, get product {product.sku} stock = {product.stock}")

        print(f"{worker_name} start work")
        if product.stock >= 7:
            try:
                product.stock -= 7
                session.commit()
            except Exception:
                session.rollback()
                raise
        else:
            print(f"{worker_name} product {product.sku} stock insufficient")
            return
        
        session.refresh(product)
        print(f"{worker_name} commited, product {product.sku} stock = {product.stock}")
        elapsed = time.perf_counter() - start
        print(f"{worker_name} time cost: {elapsed}")

thread1 = Thread(
    target = buy_product_test,
    args = ("thread-1",)
)

thread2 = Thread(
    target = buy_product_test,
    args = ("thread-2",)
)

thread1.start()
thread2.start()

thread1.join()
thread2.join()

with Session(demo_engine) as session:
    product = session.exec(
        select(Product).where(
            Product.sku == "Test-SKU-01"
        )
    ).first()
    assert product is not None

    print(f"After Check: product {product.sku} stock = {product.stock}")

## 以上运行输出 ##
# uv run python -m script.transaction_demo_with_for_update
# transaction_isolation: read committed
# Get Product Test-SKU-01 success:
# Product name = Test-Product-01
# Set Product stock = 10
# thread-1 in
# thread-2 in
# thread-1 ready, get product Test-SKU-01 stock = 10
# thread-1 start work
# thread-2 ready, get product Test-SKU-01 stock = 3
# thread-2 start work
# thread-2 product Test-SKU-01 stock insufficient
# thread-2 time cost: 2.0124724190100096
# thread-1 commited, product Test-SKU-01 stock = 3
# thread-1 time cost: 2.0170802479842678
# After Check: product Test-SKU-01 stock = 3
