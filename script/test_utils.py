from sqlmodel import select
from typing import Any

from session_factory import create_session

from models import Product, Order, User, OrderItem
from security import hash_password
from enums import OrderStatus

def create_test_product(
    sku: str = "TEST-SKU-01",
    name: str = "TEST-PRODUCT-01",
    price: float = 99.9,
    stock: int = 100
) -> Product:
    with create_session() as session:
        product = session.exec(
            select(Product).where(
                Product.sku == sku
            )
        ).first()

        if product is not None:
            return product

        product = Product(
            sku = sku,
            name = name,
            price = price,
            stock = stock
        )
        session.add(product)
        session.commit()
        session.refresh(product)
        assert product.id is not None

        return product

default_test_product = create_test_product()

def create_test_user(
    username: str = "customer-user-01",
    password: str = "password123",
    role: str = "customer"
) -> User:
    with create_session() as session:
        user = session.exec(
            select(User).where(
                User.username == username
            )
        ).first()

        if user is not None:
            return user
        
        user = User(
            username = username,
            hashed_password = hash_password(password),
            is_active = True,
            role = role
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        assert user.id is not None

        return user
    
default_test_user = create_test_user()

def create_test_order(
    user_id: int = default_test_user.id,
    items: list[dict[str, Any]] = [
        {
            "product_id": default_test_product.id,
            "quantity": 10
        }
    ]
) -> Order:
    with create_session() as session:
        order = session.exec(
            select(Order).where(
                Order.user_id == user_id
            )
        ).first()

        if order is not None:
            return order

        order = Order(
            user_id = user_id,
            status = OrderStatus.PENDING,
        )
        session.add(order)
        session.flush()

        session.refresh(order)
        assert order.id is not None

        for item in items:
            order_item = OrderItem(
                order_id = order.id,
                product_id = item["product_id"],
                quantity = item["quantity"]
            )
            session.add(order_item)
        
        session.commit()
        session.refresh(order)
        return order