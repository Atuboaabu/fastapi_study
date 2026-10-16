from enum import Enum

class OrderStatus(str, Enum):
    PENDING   = "pending"
    PAID      = "paid"
    SHIPPED   = "shipped"
    COMPLETED = "completed"
    CANCELLED = "cancelled"