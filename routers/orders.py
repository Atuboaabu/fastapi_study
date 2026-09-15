from typing import Annotated
from sqlmodel import select
from sqlalchemy.orm import selectinload
from sqlalchemy import distinct, func
from fastapi import Path, Query, HTTPException, status, APIRouter

from dependencies import SessionDep
from main_db import OrderItem, OrderCreate, OrderItemPublic, Order, OrderListResponse, OrderPublic, Product

router = APIRouter(
    prefix = "/orders",
    tags = ["orders"]
)

# POST "/orders/"
@router.post(
    "/",
    response_model=OrderPublic,
    status_code = status.HTTP_201_CREATED
)
def create_order(
    order_data: OrderCreate,
    session: SessionDep
):
    product_ids = [
        item.product_id
        for item in order_data.items
    ]
    if len(product_ids) != len(set(product_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate product in order"
        )
    products: dict[int, Product] = {}
    for item in order_data.items:
        product = session.get(Product, item.product_id)
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {item.product_id} not found"
            )
        if product.stock < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Insufficient stock for product {item.product_id}"
            )
        products[item.product_id] = product

    try:
        order = Order(
            status="pending"
        )
        session.add(order)
        # insert order 但不 commit, 得到 order_id
        session.flush()

        assert order.id is not None

        create_items = []
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
            create_items.append(order_item)
        session.commit()
    except Exception:
        session.rollback()
        raise

    session.refresh(order)
    for item in create_items:
        session.refresh(item)
    
    return OrderPublic(
        id = order.id,
        status = order.status,
        items = [
            OrderItemPublic(
                id = item.id,
                product_id=item.product_id,
                quantity = item.quantity
            )
            for item in create_items
        ]
    )

# GET "/orders/{order_id}"
@router.get(
    "/{order_id}",
    response_model=OrderPublic
)
def get_order(
    order_id: Annotated[int, Path(gt=0)],
    session: SessionDep
):
    order = session.get(Order, order_id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found"
        )
    return order

# GET "/orders/"
@router.get(
    "/",
    response_model=OrderListResponse
)
def get_orders(
    session: SessionDep,
    product_id: Annotated[int | None, Query(gt=0)] = None,
    status_filter: Annotated[str | None, Query(alias="status", max_length=20)] = None,
    sort_order: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
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
    return OrderListResponse(
        items=orders,
        total=count,
        offset=offset,
        limit=limit
    )