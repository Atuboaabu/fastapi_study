from sqlmodel import create_engine, Session, select
from sqlalchemy import text
from threading import Barrier, Thread

from config import settings
from models import Product

demo_engine = create_engine(
    url = settings.database_url,
    pool_size = 2,
    max_overflow = 0,
)

with Session(demo_engine) as session:
    res = session.execute(text("SHOW transaction_isolation")).scalars().all()
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
        print(f"Get Product {product.sku} success:")
        print(f"Product name = {product.name}")
        print(f"Product stock = {product.stock}")

barrier = Barrier(2) 
def buy_product_test(worker_name: str):
    with Session(demo_engine) as session:
        product = session.exec(
            select(Product).where(
                Product.sku == "Test-SKU-01"
            )
        ).first()
        assert product is not None

        print(f"{worker_name} ready, get product {product.sku} stock = {product.stock}")
        barrier.wait()

        print(f"{worker_name} start work")
        try:
            if product.stock >= 7:
                product.stock -= 7

            session.commit()
        except Exception:
            session.rollback()
            raise
        
        session.refresh(product)
        print(f"{worker_name} commited, product {product.sku} stock = {product.stock}")

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

## 以上运行输出 ##
# uv run python -m script.transiaction_demo
# transaction_isolation: ['read committed']
# Get Product Test-SKU-01 success:
# Product name = Test-Product-01
# Product stock = 10
# thread-1 ready, get product Test-SKU-01 stock = 10
# thread-2 ready, get product Test-SKU-01 stock = 10
# thread-2 start work
# thread-1 start work
# thread-2 commited, product Test-SKU-01 stock = 3
# thread-1 commited, product Test-SKU-01 stock = 3

