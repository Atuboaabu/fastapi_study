from sqlmodel import Session, create_engine, select
from sqlalchemy.orm import selectinload

from config import settings
from models import Order

demo_engine = create_engine(
    url = settings.database_url,
    pool_size = 2,
    max_overflow = 0,
)

# with Session(demo_engine) as session:
#     orders = session.exec(
#         select(Order)
#     ).all()

# print("Orders Info")
# for order in orders:
#     print(f"Order id = {order.id}")
#     for item in order.items:
#         print(f"product {item.product_id} stock = {item.quantity}")

## 运行输出：
# uv run python -m script.orm_life_time_d
# emo
# Orders Info
# Order id = 47
# Traceback (most recent call last):
# ...
# raise orm_exc.DetachedInstanceError(
# sqlalchemy.orm.exc.DetachedInstanceError: Parent instance <Order at 0x780b7c7b5e00> is not bound to a Session; lazy load operation of attribute 'items' cannot proceed (Background on this error at: https://sqlalche.me/e/20/bhk3)

# with Session(demo_engine) as session:
#     orders = session.exec(
#         select(Order).options(
#             selectinload(Order.items)
#         )
#     ).all()

# print("Orders Info")
# for order in orders:
#     print(f"Order id = {order.id}")
#     for item in order.items:
#         print(f"product {item.product_id} stock = {item.quantity}")

# 以上运行输出
# uv run python -m script.orm_life_time_demo
# Orders Info
# Order id = 47
# product 1 stock = 7
# Order id = 48
# product 1 stock = 9

# with Session(demo_engine) as session:
#     orders = session.exec(
#         select(Order).options(
#             selectinload(Order.items)
#         )
#     ).all()
#     session.commit()

# print("Orders Info")
# for order in orders:
#     print(f"Order id = {order.id}")
#     for item in order.items:
#         print(f"product {item.product_id} stock = {item.quantity}")

# 以上输出
# Orders Info
# Traceback (most recent call last):

# raise orm_exc.DetachedInstanceError(
# sqlalchemy.orm.exc.DetachedInstanceError: Instance <Order at 0x75c680fddd60> is not bound to a Session; attribute refresh operation cannot proceed (Background on this error at: https://sqlalche.me/e/20/bhk3)

with Session(demo_engine, expire_on_commit=False) as session:
    orders = session.exec(
        select(Order).options(
            selectinload(Order.items)
        )
    ).all()
    session.commit()

print("Orders Info")
for order in orders:
    print(f"Order id = {order.id}")
    for item in order.items:
        print(f"product {item.product_id} stock = {item.quantity}")

# 以上运行输出
# uv run python -m script.orm_life_time_demo
# Orders Info
# Order id = 47
# product 1 stock = 7
# Order id = 48
# product 1 stock = 9