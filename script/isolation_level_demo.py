from sqlmodel import Session, create_engine, select, update
from sqlalchemy import text
from threading import Thread, Barrier

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
        print(f"Product id = {product.id}")
        print(f"Product name = {product.name}")
        print(f"Set Product stock = {product.stock}")

barrier = Barrier(2)
def worker_1(worker_name: str):
    with Session(demo_engine) as session:
        try:
            stock = session.execute(
                text("SELECT stock FROM product WHERE sku = :sku"),
                {
                    "sku": "Test-SKU-01"
                }
            ).scalar_one()
            assert stock is not None
            print(f"{worker_name} 1st get product stock = {stock}")
            barrier.wait()

            stock = session.execute(
                text("SELECT stock FROM product WHERE sku = :sku"),
                {
                    "sku": "Test-SKU-01"
                }
            ).scalar_one()
            assert stock is not None
            print(f"{worker_name} 2nd get product stock = {stock}")

        except Exception as exc:
            print(f"{worker_name} except: {exc}")
            session.rollback()
            raise

def worker_2(worker_name: str):
    with Session(demo_engine) as session:
        try:
            statement = update(Product).where(
                Product.sku == "Test-SKU-01"
            ).values(
                stock = Product.stock + 10
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
        barrier.wait()

t1 = Thread(
    target=worker_1,
    args=("thread-1",)
)
t2 = Thread(
    target=worker_2,
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

# 以上运行输出
# transaction_isolation: read committed
# Get Product Test-SKU-01 success:
# Product id = 1
# Product name = Test-Product-01
# Set Product stock = 10
# thread-1 1st get product stock = 10
# thread-2 exec result rowcount = 1
# thread-2 change product stock
# thread-1 2nd get product stock = 20
# After Check: product Test-SKU-01 stock = 20