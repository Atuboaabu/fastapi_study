from dataclasses import dataclass
from typing import Any
from datetime import datetime

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

@dataclass(frozen=True)
class NotificationJobClaim:
    id: int
    event_id: int
    job_type: str
    payload: dict[str, Any]
    created_at: datetime
    processed_at: datetime | None
    retry_count: int
    next_attempt_at: datetime
    last_error: str | None
    failed_at: datetime | None
    lease_until: datetime | None
    claimed_by: str | None
    claim_version: int