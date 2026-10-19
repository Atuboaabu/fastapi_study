from enums import OrderStatus

ALLOWED_ORDER_TRANSITIONS = {
    OrderStatus.PENDING: frozenset(
        {
            OrderStatus.PAID,
            OrderStatus.CANCELLED
        }
    ),
    OrderStatus.PAID: frozenset(
        {
            OrderStatus.SHIPPED
        }
    ),
    OrderStatus.SHIPPED: frozenset(
        {
            OrderStatus.COMPLETED
        }
    ),
    OrderStatus.COMPLETED: frozenset(),
    OrderStatus.CANCELLED: frozenset(),
}

def is_order_transition_allowed(
    current_status: OrderStatus,
    dest_status: OrderStatus
)->bool:
    return dest_status in ALLOWED_ORDER_TRANSITIONS[current_status]