from sqlmodel import Session, create_engine, select, update
from threading import Thread, Barrier

from config import settings
from models import Product

demo_engine = create_engine(
    url = settings.database_url,
    pool_size = 2,
    max_overflow = 0,
)

with Session(demo_engine) as session:
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

barrier = Barrier(2)
def worker(worker_name: str):
    with Session(demo_engine) as session:
        try:
            barrier.wait()
            statement = update(Product).where(
                Product.sku == "Test-SKU-01",
                Product.stock >= 7
            ).values(
                stock = Product.stock - 7
            )

            result = session.exec(statement)
            print(f"{worker_name} exec result rowcount = {result.rowcount}")

            session.commit()

            if result.rowcount == 0:
                print(f"{worker_name} change product stock failed")
            else:
                print(f"{worker_name} change product stock")

        except Exception as exc:
            print(f"{worker_name} except: {exc}")
            session.rollback()
            raise

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
    product = session.exec(
        select(Product).where(
            Product.sku == "Test-SKU-01"
        )
    ).first()
    assert product is not None

    print(f"After Check: product {product.sku} stock = {product.stock}")