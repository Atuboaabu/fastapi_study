from fastapi import APIRouter, status, Query, Path
from typing import Annotated

from schemas import AdminOrderPublic, AdminOrderListResponse
from services import orders

from dependencies import SessionDep, AdminUserDep
from enums import OrderStatus

router = APIRouter(
    prefix = "/admin/orders",
    tags = ["admin-orders"]
)

@router.get(
    "/{order_id}",
    response_model =  AdminOrderPublic
)
def get_order(
    order_id: Annotated[int, Path(gt=0)],
    user: AdminUserDep,
    session: SessionDep,
):
    return orders.get_order_by_id(
        order_id,
        session,
    )

@router.get(
    "/",
    response_model =  AdminOrderListResponse
)
def get_all_orders(
    user: AdminUserDep,
    session: SessionDep,
    product_id: Annotated[int | None, Query(gt=0)] = None,
    status_filter: Annotated[OrderStatus | None, Query(alias="status", max_length=20)] = None,
    sort_order: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    order_list, count = orders.get_all_orders(
        session,
        product_id,
        status_filter,
        sort_order,
        offset,
        limit
    )
    return AdminOrderListResponse(
        items=order_list,
        total=count,
        offset=offset,
        limit=limit
    )