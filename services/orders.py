from typing import Literal

from sqlmodel import Session, select
from sqlalchemy import func, distinct
from sqlalchemy.orm import selectinload

from models import Order, OrderItem, Product
from schemas import OrderCreate
from exceptions import (
    ProductNotFoundException,
    DuplicateProductException,
    InsufficientStockException,
    OrderNotFoundException,
    InvalidOrderStateTransitionException
)
from enums import OrderStatus
from order_state import is_order_transition_allowed
from services.result import OrderItemResult, OrderResult

def create_order_operation(
    session: Session,
    args: list,
) -> OrderResult:
    [order_data, user_id] = args

    product_ids = [
        item.product_id
        for item in order_data.items
    ]
    if len(product_ids) != len(set(product_ids)):
        raise DuplicateProductException()

    statement = (
        select(Product)
        .where(Product.id.in_(product_ids))
        .order_by(Product.id)
        .with_for_update()
    )
    lock_products = session.exec(statement).all()

    products: dict[int, Product] = {
        product.id: product
        for product in lock_products
    }
    
    for item in order_data.items:
        if item.product_id not in products:
            raise ProductNotFoundException(item.product_id)

        product = products[item.product_id]

        if product.stock < item.quantity:
            raise InsufficientStockException(item.product_id)

    order = Order(
        status=OrderStatus.PENDING,
        user_id = user_id
    )
    session.add(order)
    # insert order 但不 commit, 得到 order_id
    session.flush()

    assert order.id is not None

    for item in order_data.items:
        product = products[item.product_id]
        product.stock -= item.quantity

        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity
        )

        session.add(order_item)
        order.items.append(order_item)
    session.flush()

    return OrderResult(
        id = order.id,
        status = order.status,
        items = [
            OrderItemResult(
                item.id,
                item.product_id,
                item.quantity
            )
            for item in order.items
        ]
    )

def create_order(
    order_data: OrderCreate,
    user_id: int,
    session: Session
) -> Order:
    product_ids = [
        item.product_id
        for item in order_data.items
    ]

    if len(product_ids) != len(set(product_ids)):
        raise DuplicateProductException()
    
    try:
        statement = (
            select(Product)
            .where(Product.id.in_(product_ids))
            .order_by(Product.id)
            .with_for_update()
        )

        lock_products = session.exec(statement).all()

        products: dict[int, Product] = {
            product.id: product
            for product in lock_products
        }
        
        for item in order_data.items:
            if item.product_id not in products:
                raise ProductNotFoundException(item.product_id)

            product = products[item.product_id]

            if product.stock < item.quantity:
                raise InsufficientStockException(item.product_id)
    
        order = Order(
            status=OrderStatus.PENDING,
            user_id = user_id
        )
        session.add(order)
        # insert order 但不 commit, 得到 order_id
        session.flush()

        assert order.id is not None

        for item in order_data.items:
            product = products[item.product_id]
            product.stock -= item.quantity

            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity
            )

            session.add(order_item)
            order.items.append(order_item)

        session.commit()
    except Exception:
        session.rollback()
        raise

    session.refresh(order)
    
    return order

def get_order_for_user(
    order_id: int,
    user_id: int,
    session: Session
) -> Order:
    statement = select(Order).where(
        Order.id == order_id
    ).where(
        Order.user_id == user_id
    )
    order = session.exec(statement).first()

    if order is None:
        raise OrderNotFoundException(order_id)

    return order

def get_order_by_id(
    order_id: int,
    session: Session
) -> Order:
    statement = select(Order).where(
        Order.id == order_id
    )

    order = session.exec(statement).first()

    if order is None:
        raise OrderNotFoundException(order_id)

    return order

def mark_order_paid(
    order_id: int,
    session: Session
):
    try:
        order = session.exec(
            select(Order)
            .where(Order.id == order_id)
            .with_for_update()
        ).first()

        if order is None:
            raise OrderNotFoundException(order_id)
        
        if not is_order_transition_allowed(order.status, OrderStatus.PAID):
            raise InvalidOrderStateTransitionException(order.status, OrderStatus.PAID)

        order.status = OrderStatus.PAID
        session.commit()
    except Exception:
        session.rollback()
        raise

    session.refresh(order)
    return order

def mark_order_shipped(
    order_id: int,
    session: Session
):
    try:
        order = session.exec(
            select(Order)
            .where(Order.id == order_id)
            .with_for_update()
        ).first()

        if order is None:
            raise OrderNotFoundException(order_id)
        
        if not is_order_transition_allowed(order.status, OrderStatus.SHIPPED):
            raise InvalidOrderStateTransitionException(order.status, OrderStatus.SHIPPED)

        order.status = OrderStatus.SHIPPED
        session.commit()
    except Exception:
        session.rollback()
        raise

    session.refresh(order)
    return order

def cancel_order_for_user(
    order_id: int,
    user_id: int,
    session: Session
) -> Order:
    try:
        statement = select(Order).where(
            Order.id == order_id,
            Order.user_id == user_id
        ).with_for_update()
        order = session.exec(statement).first()

        if order is None:
            raise OrderNotFoundException(order_id)
        
        if not is_order_transition_allowed(order.status, OrderStatus.CANCELLED):
            raise InvalidOrderStateTransitionException(order.status, OrderStatus.CANCELLED)
        
        product_ids = [
            item.product_id
            for item in order.items
        ]

        lock_products = session.exec(
            select(Product)
            .where(
                Product.id.in_(product_ids)
            )
            .order_by(Product.id)
            .with_for_update()
        ).all()

        products_dict = {
            product.id: product
            for product in lock_products
        }

        for item in order.items:
            products_dict[item.product_id].stock += item.quantity
        order.status = OrderStatus.CANCELLED
        session.commit()
    except Exception:
        session.rollback()
        raise

    return order

def complete_order_for_user(
    order_id: int,
    user_id: int,
    session: Session
)->Order:
    try:
        statement = select(Order).where(
            Order.id == order_id,
            Order.user_id == user_id
        ).with_for_update()
        order = session.exec(statement).first()

        if order is None:
            raise OrderNotFoundException(order_id)
        
        if not is_order_transition_allowed(order.status, OrderStatus.COMPLETED):
            raise InvalidOrderStateTransitionException(order.status, OrderStatus.COMPLETED)
    
        order.status = OrderStatus.COMPLETED
        session.commit()
    except Exception:
        session.rollback()
        raise

    session.refresh(order)
    return order

def get_orders_for_user(
    session: Session,
    user_id: int,
    product_id: int | None = None,
    status_filter: OrderStatus | None = None,
    sort_order: Literal["asc", "desc"] = "desc",
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Order], int]:
    statement = select(Order)
    count_statement = select(
        func.count(distinct(Order.id))
    ).select_from(Order)

    statement = statement.where(Order.user_id == user_id)
    count_statement = count_statement.where(Order.user_id == user_id)

    if product_id is not None:
        statement = statement.join(OrderItem).where(OrderItem.product_id == product_id).distinct()
        count_statement = count_statement.join(OrderItem).where(OrderItem.product_id == product_id)
    
    if status_filter is not None:
        statement = statement.where(Order.status == status_filter)
        count_statement = count_statement.where(Order.status == status_filter)
    
    if sort_order == "asc":
        statement = statement.order_by(Order.id.asc())
    else:
        statement = statement.order_by(Order.id.desc())
    
    statement = (statement
                 .offset(offset)
                 .limit(limit)
                 .options(
                    selectinload(Order.items)
        )
    )
    orders = session.exec(statement).all()
    count = session.exec(count_statement).one()
    return list(orders), count

def get_all_orders(
    session: Session,
    product_id: int | None = None,
    status_filter: OrderStatus | None = None,
    sort_order: Literal["asc", "desc"] = "desc",
    offset: int = 0,
    limit: int = 20,
) -> tuple[list[Order], int]:
    statement = select(Order)
    count_statement = select(
        func.count(distinct(Order.id))
    ).select_from(Order)

    if product_id is not None:
        statement = statement.join(OrderItem).where(OrderItem.product_id == product_id).distinct()
        count_statement = count_statement.join(OrderItem).where(OrderItem.product_id == product_id)
    
    if status_filter is not None:
        statement = statement.where(Order.status == status_filter)
        count_statement = count_statement.where(Order.status == status_filter)
    
    if sort_order == "asc":
        statement = statement.order_by(Order.id.asc())
    else:
        statement = statement.order_by(Order.id.desc())
    
    statement = (statement
                 .offset(offset)
                 .limit(limit)
                 .options(
                    selectinload(Order.items)
        )
    )
    orders = session.exec(statement).all()
    count = session.exec(count_statement).one()
    return list(orders), count