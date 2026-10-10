import pytest
from models import Product, Order, OrderItem
from schemas import OrderCreate, OrderItemCreate
from services import orders
from sqlmodel import select

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

    product_id = product.id

    def fail_commit():
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

        orders.create_order(order_data, session)

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
