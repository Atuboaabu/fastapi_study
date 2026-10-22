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
                stock = 1,
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
                product.stock = 1
                session.commit()
            except Exception:
                session.rollback()
                raise

barrier = Barrier(2)
def worker_1(worker_name: str):
    with Session(demo_engine) as session:
        session.execute(text("SET transaction_isolation = 'repeatable read'"))
        res = session.execute(text("SHOW transaction_isolation")).scalar_one()
        print(f"transaction_isolation: {res}")

        try:
            stock_1 = session.execute(
                text("SELECT stock FROM product WHERE sku = :sku"),
                {
                    "sku": "Test-SKU-01"
                }
            ).scalar_one()
            assert stock_1 is not None
            print(f"{worker_name} get product Test-SKU-01 stock = {stock_1}")

            stock_2 = session.execute(
                text("SELECT stock FROM product WHERE sku = :sku"),
                {
                    "sku": "Test-SKU-02"
                }
            ).scalar_one()
            assert stock_2 is not None
            print(f"{worker_name} get product Test-SKU-02 stock = {stock_2}")

            barrier.wait()

            if stock_2 > 0:
                statement = update(Product).where(
                    Product.sku == "Test-SKU-02"
                ).values(
                    stock = 0
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

def worker_2(worker_name: str):
    with Session(demo_engine) as session:
        session.execute(text("SET transaction_isolation = 'repeatable read'"))
        res = session.execute(text("SHOW transaction_isolation")).scalar_one()
        print(f"transaction_isolation: {res}")

        try:
            stock_1 = session.execute(
                text("SELECT stock FROM product WHERE sku = :sku"),
                {
                    "sku": "Test-SKU-01"
                }
            ).scalar_one()
            assert stock_1 is not None
            print(f"{worker_name} get product Test-SKU-01 stock = {stock_1}")

            stock_2 = session.execute(
                text("SELECT stock FROM product WHERE sku = :sku"),
                {
                    "sku": "Test-SKU-02"
                }
            ).scalar_one()
            assert stock_2 is not None
            print(f"{worker_name} get product Test-SKU-02 stock = {stock_2}")

            barrier.wait()

            if stock_1 > 0:
                statement = update(Product).where(
                    Product.sku == "Test-SKU-01"
                ).values(
                    stock = 0
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

    product = session.exec(
        select(Product).where(
            Product.sku == "Test-SKU-02"
        )
    ).first()
    assert product is not None

    print(f"After Check: product {product.sku} stock = {product.stock}")

# 以上运行输出
# transaction_isolation: repeatable read
# thread-1 get product Test-SKU-01 stock = 1
# thread-1 get product Test-SKU-02 stock = 1
# transaction_isolation: repeatable read
# thread-2 get product Test-SKU-01 stock = 1
# thread-2 get product Test-SKU-02 stock = 1
# thread-2 exec result rowcount = 1
# thread-1 exec result rowcount = 1
# thread-2 change product stock
# thread-1 change product stock
# After Check: product Test-SKU-01 stock = 0
# After Check: product Test-SKU-02 stock = 0

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
                stock = 1,
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
                product.stock = 1
                session.commit()
            except Exception:
                session.rollback()
                raise

barrier = Barrier(2)
def worker_1(worker_name: str):
    with Session(demo_engine) as session:
        session.execute(text("SET transaction_isolation = 'serializable'"))
        res = session.execute(text("SHOW transaction_isolation")).scalar_one()
        print(f"transaction_isolation: {res}")

        try:
            stock_1 = session.execute(
                text("SELECT stock FROM product WHERE sku = :sku"),
                {
                    "sku": "Test-SKU-01"
                }
            ).scalar_one()
            assert stock_1 is not None
            print(f"{worker_name} get product Test-SKU-01 stock = {stock_1}")

            stock_2 = session.execute(
                text("SELECT stock FROM product WHERE sku = :sku"),
                {
                    "sku": "Test-SKU-02"
                }
            ).scalar_one()
            assert stock_2 is not None
            print(f"{worker_name} get product Test-SKU-02 stock = {stock_2}")

            barrier.wait()

            if stock_2 > 0:
                statement = update(Product).where(
                    Product.sku == "Test-SKU-02"
                ).values(
                    stock = 0
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

def worker_2(worker_name: str):
    with Session(demo_engine) as session:
        session.execute(text("SET transaction_isolation = 'serializable'"))
        res = session.execute(text("SHOW transaction_isolation")).scalar_one()
        print(f"transaction_isolation: {res}")

        try:
            stock_1 = session.execute(
                text("SELECT stock FROM product WHERE sku = :sku"),
                {
                    "sku": "Test-SKU-01"
                }
            ).scalar_one()
            assert stock_1 is not None
            print(f"{worker_name} get product Test-SKU-01 stock = {stock_1}")

            stock_2 = session.execute(
                text("SELECT stock FROM product WHERE sku = :sku"),
                {
                    "sku": "Test-SKU-02"
                }
            ).scalar_one()
            assert stock_2 is not None
            print(f"{worker_name} get product Test-SKU-02 stock = {stock_2}")

            barrier.wait()

            if stock_1 > 0:
                statement = update(Product).where(
                    Product.sku == "Test-SKU-01"
                ).values(
                    stock = 0
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

    product = session.exec(
        select(Product).where(
            Product.sku == "Test-SKU-02"
        )
    ).first()
    assert product is not None

    print(f"After Check: product {product.sku} stock = {product.stock}")

# 以上运行输出
# transaction_isolation: serializable
# transaction_isolation: serializable
# thread-1 get product Test-SKU-01 stock = 1
# thread-2 get product Test-SKU-01 stock = 1
# thread-1 get product Test-SKU-02 stock = 1
# thread-2 get product Test-SKU-02 stock = 1
# thread-2 exec result rowcount = 1
# thread-1 exec result rowcount = 1
# thread-2 change product stock
# thread-1 except: (psycopg.errors.SerializationFailure) could not serialize access due to read/write dependencies among transactions
# ...
# After Check: product Test-SKU-01 stock = 0
# After Check: product Test-SKU-02 stock = 1