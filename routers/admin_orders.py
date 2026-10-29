from fastapi import APIRouter, Query, Path
from typing import Annotated

from schemas import AdminOrderPublic, AdminOrderListResponse, OrderItemPublic
from services import orders, transaction
from services.result import OrderResult

from dependencies import SessionDep, AdminUserDep, SessionFactoryDep
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
    status_filter: Annotated[OrderStatus | None, Query(alias="status")] = None,
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

@router.post(
    "/{order_id}/pay",
    response_model = AdminOrderPublic
)
def mark_order_paid(
    order_id: Annotated[int, Path(gt = 0)],
    user: AdminUserDep,
    session_factory: SessionFactoryDep
):
    assert user.id is not None

    args = [order_id]
    order_result: OrderResult | None = transaction.run_transaction_with_retry(
        session_factory,
        orders.mark_order_paid_operation,
        args,
        3
    )
    assert order_result is not None

    return AdminOrderPublic(
        id = order_result.id,
        user_id = order_result.user_id,
        status = order_result.status,
        items = [
            OrderItemPublic(
                id = item.id,
                product_id = item.product_id,
                quantity = item.quantity
            )
            for item in order_result.items
        ]
    )

@router.post(
    "/{order_id}/ship",
    response_model = AdminOrderPublic
)
def mark_order_shipped(
    order_id: Annotated[int, Path(gt = 0)],
    user: AdminUserDep,
    session_factory: SessionFactoryDep
):
    assert user.id is not None

    args = [order_id]
    order_result: OrderResult | None = transaction.run_transaction_with_retry(
        session_factory,
        orders.mark_order_shipped_operation,
        args,
        3
    )
    assert order_result is not None

    return AdminOrderPublic(
        id = order_result.id,
        user_id = order_result.user_id,
        status = order_result.status,
        items = [
            OrderItemPublic(
                id = item.id,
                product_id = item.product_id,
                quantity = item.quantity
            )
            for item in order_result.items
        ]
    )