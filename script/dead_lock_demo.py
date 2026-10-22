from sqlmodel import create_engine, Session, select
from threading import Thread, Barrier

from config import settings
from models import Product

demo_engine = create_engine(
    url = settings.database_url,
    pool_size = 2,
    max_overflow = 0
)

with Session(demo_engine) as session:
    for id in (1,2):
        product = session.exec(
            select(Product)
            .where(Product.sku == f"Test-SKU-0{id}")
        ).first()

        if product is None:
            product = Product(
                sku = f"Test-SKU-0{id}",
                name = f"Test-Product-0{id}",
                price = id * 99.9,
                stock = id * 10,
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
                product.stock = id * 10
                session.commit()
            except Exception:
                session.rollback()
                raise
            session.refresh(product)

barrier = Barrier(2)
def worker_1(worker_name: str):
    print(f"{worker_name} statr")
    with Session(demo_engine) as session:
        product = session.exec(
            select(Product)
            .where(Product.sku == "Test-SKU-01")
            .with_for_update()
        ).first()

        assert product is not None
        product.stock += 20
        print(f"{worker_name} changed Test-SKU-01 stock")

        barrier.wait()

        product = session.exec(
            select(Product)
            .where(Product.sku == "Test-SKU-02")
            .with_for_update()
        ).first()
        assert product is not None

        
        product.stock += 20
        print(f"{worker_name} changed Test-SKU-02 stock")
        session.commit()

def worker_2(worker_name: str):
    print(f"{worker_name} statr")
    with Session(demo_engine) as session:
        product = session.exec(
            select(Product)
            .where(Product.sku == "Test-SKU-02")
            .with_for_update()
        ).first()

        assert product is not None
        product.stock += 20
        print(f"{worker_name} changed Test-SKU-02 stock")

        barrier.wait()

        product = session.exec(
            select(Product)
            .where(Product.sku == "Test-SKU-01")
            .with_for_update()
        ).first()
        assert product is not None

        
        product.stock += 20
        print(f"{worker_name} changed Test-SKU-01 stock")
        session.commit()


t1 = Thread(
    target=worker_1,
    args=("thread-1",)
)

t2 = Thread(
    target=worker_2,
    args=("Thread-2",)
)

t1.start()
t2.start()

t1.join()
t2.join()

with Session(demo_engine) as session:
    product = session.exec(
        select(Product).where(
            Product.sku == "Test-SKU-01"
        )
    ).first()
    assert product is not None

    print(f"After Check: product {product.sku} stock = {product.stock}")

    product = session.exec(
        select(Product).where(
            Product.sku == "Test-SKU-02"
        )
    ).first()
    assert product is not None

    print(f"After Check: product {product.sku} stock = {product.stock}")

##  运行输出  ##
# ...
# sqlalchemy.exc.OperationalError: (psycopg.errors.DeadlockDetected) deadlock detected
# ...