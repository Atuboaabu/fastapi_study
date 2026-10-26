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
    user_id: int
    status: OrderStatus
    items: list[OrderItemResult]

@dataclass(frozen=True)
class UserResult:
    id: int
    username: str
    hashed_password: str
    is_active: bool
    role: str