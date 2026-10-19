import pytest
from order_state import is_order_transition_allowed
from enums import OrderStatus

@pytest.mark.parametrize(
    "current_status, dest_status, expected_result",
    [
        (OrderStatus.PENDING, OrderStatus.PENDING, False),
        (OrderStatus.PENDING, OrderStatus.PAID, True),
        (OrderStatus.PENDING, OrderStatus.SHIPPED, False),
        (OrderStatus.PENDING, OrderStatus.COMPLETED, False),
        (OrderStatus.PENDING, OrderStatus.CANCELLED, True),
        (OrderStatus.PAID, OrderStatus.PENDING, False),
        (OrderStatus.PAID, OrderStatus.PAID, False),
        (OrderStatus.PAID, OrderStatus.SHIPPED, True),
        (OrderStatus.PAID, OrderStatus.COMPLETED, False),
        (OrderStatus.PAID, OrderStatus.CANCELLED, False),
        (OrderStatus.SHIPPED, OrderStatus.PENDING, False),
        (OrderStatus.SHIPPED, OrderStatus.PAID, False),
        (OrderStatus.SHIPPED, OrderStatus.SHIPPED, False),
        (OrderStatus.SHIPPED, OrderStatus.COMPLETED, True),
        (OrderStatus.SHIPPED, OrderStatus.CANCELLED, False),
        (OrderStatus.COMPLETED, OrderStatus.PENDING, False),
        (OrderStatus.COMPLETED, OrderStatus.PAID, False),
        (OrderStatus.COMPLETED, OrderStatus.SHIPPED, False),
        (OrderStatus.COMPLETED, OrderStatus.COMPLETED, False),
        (OrderStatus.COMPLETED, OrderStatus.CANCELLED, False),
        (OrderStatus.CANCELLED, OrderStatus.PENDING, False),
        (OrderStatus.CANCELLED, OrderStatus.PAID, False),
        (OrderStatus.CANCELLED, OrderStatus.SHIPPED, False),
        (OrderStatus.CANCELLED, OrderStatus.COMPLETED, False),
        (OrderStatus.CANCELLED, OrderStatus.CANCELLED, False),
    ]
)
def test_order_transition(
    current_status,
    dest_status,
    expected_result
):
    assert is_order_transition_allowed(current_status, dest_status) == expected_result