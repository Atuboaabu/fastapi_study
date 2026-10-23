from dataclasses import dataclass

from enums import OrderStatus

@dataclass(frozen=True)
class OrderItemResult:
    id: int
    product_id: int
    quantity: int

@dataclass(frozen=True)
class OrderResult:
    id: int
    status: OrderStatus
    items: list[OrderItemResult]