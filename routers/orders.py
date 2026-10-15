from typing import Annotated

from fastapi import Path, Query, status, APIRouter

from dependencies import SessionDep, ActiveUserDep
from schemas import OrderCreate, OrderListResponse, OrderPublic

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
    user: ActiveUserDep,
    session: SessionDep
):
    assert user.id is not None

    return orders.create_order(order_data, user.id, session)

# GET "/orders/{order_id}"
@router.get(
    "/{order_id}",
    response_model=OrderPublic
)
def get_order(
    order_id: Annotated[int, Path(gt=0)],
    user: ActiveUserDep,
    session: SessionDep
):
    assert user.id is not None

    return orders.get_order_for_user(order_id, user.id, session)

# GET "/orders/"
@router.get(
    "/",
    response_model=OrderListResponse
)
def get_orders(
    user: ActiveUserDep,
    session: SessionDep,
    product_id: Annotated[int | None, Query(gt=0)] = None,
    status_filter: Annotated[str | None, Query(alias="status", max_length=20)] = None,
    sort_order: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    assert user.id is not None

    order_list, count = orders.get_orders_for_user(
        session,
        user.id,
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