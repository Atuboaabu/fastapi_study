from typing import Annotated

from fastapi import Path, Query, HTTPException, status, APIRouter

from dependencies import SessionDep
from main_db import OrderCreate, OrderListResponse, OrderPublic

from services import orders

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
    try:
        return orders.create_order(order_data, session)

    except orders.DuplicateProductException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate product in order"
        )

    except orders.ProductNotFoundException as exc:
        raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {exc.product_id} not found"
            )

    except orders.InsufficientStockException as exc:
        raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Insufficient stock for product {exc.product_id}"
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
    try:
        return orders.get_order(order_id, session)

    except orders.OrderNotFoundException as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {exc.order_id} not found"
        )

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
    order_list, count = orders.get_orders(
        session,
        product_id,
        status_filter,
        sort_order,
        offset,
        limit
    )
    return OrderListResponse(
        items=order_list,
        total=count,
        offset=offset,
        limit=limit
    )