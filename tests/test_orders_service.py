import pytest
from models import Product, Order, OrderItem, User
from schemas import OrderCreate, OrderItemCreate
from services import orders
from sqlmodel import select
from security import hash_password

def test_order_rollback_when_commit_fails(
    session,
    monkeypatch
):
    product = Product(
        sku="TEST-01",
        name="KeyBoard",
        price=99.9,
        stock=10,
    )

    session.add(product)
    session.commit()
    session.refresh(product)

    assert product.id is not None
    product_id = product.id

    user = User(
        username = "customer",
        hashed_password = hash_password("password123"),
        role = "customer"
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    assert user.id is not None
    user_id = user.id

    def fail_commit():
        session.flush()

        raise RuntimeError(
            "simulated commit failure"
        )
    
    monkeypatch.setattr(
        session,
        "commit",
        fail_commit
    )

    with pytest.raises(
        RuntimeError,
        match="simulated commit failure"
    ):
        order_data = OrderCreate(
            items=[
                OrderItemCreate(
                    product_id=product_id,
                    quantity=2
                )
            ]
        )

        orders.create_order(order_data, user_id, session)

    product_after = session.get(Product, product_id)

    assert product_after is not None
    assert product_after.stock == 10

    created_orders = session.exec(
        select(Order)
    ).all()
    assert created_orders == []

    created_items = session.exec(
        select(OrderItem)
    ).all()
    assert created_items == []
