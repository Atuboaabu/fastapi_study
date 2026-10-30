from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import CheckConstraint, DateTime, Column, func, JSON, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from typing import Any
from datetime import datetime

from enums import OrderStatus

class OrderItem(SQLModel, table = True):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="ck_order_items_quantity_positive",
        ),
    )

    id: int | None = Field(
        default = None,
        primary_key = True
    )
    order_id: int = Field(
        foreign_key = "orders.id",
        index=True
    )
    product_id: int = Field(
        foreign_key="product.id",
        index=True
    )
    quantity: int = Field(gt=0)
    order: "Order" = Relationship(
        back_populates="items"
    )
    product: "Product" = Relationship(
        back_populates="order_items"
    )

class Order(SQLModel, table = True):
    __tablename__ = "orders"
    id: int | None = Field(
        default=None,
        primary_key = True
    )
    user_id: int = Field(
        foreign_key = "users.id",
        index = True
    )
    status: OrderStatus = Field(
        default=OrderStatus.PENDING,
        sa_column=Column(
            SAEnum(
                OrderStatus,
                values_callable = lambda enum_cls: [
                    item.value
                    for item in enum_cls
                ],
                native_enum = False,
                create_constraint = True,
                name = "ck_orders_status_valid",
                length = 20
            ),
            nullable = False
        )
    )
    user: "User" = Relationship(
        back_populates = "orders"
    )
    items: list["OrderItem"] = Relationship(
        back_populates="order"
    )

class Product(SQLModel, table = True):
    sku: str = Field(
        min_length = 3,
        max_length = 50,
        unique = True
    )

    name: str = Field(
        min_length = 1,
        max_length = 100
    )

    price: float = Field(gt = 0)

    stock: int = Field(ge = 0)

    description: str | None =  Field(
        default = None,
        max_length=500
    )

    id: int | None = Field(
        default=None,
        primary_key=True,
    )

    order_items: list["OrderItem"] = Relationship(
        back_populates="product"
    )

class User(SQLModel, table = True):
    __tablename__ = "users"
    id: int | None = Field(
        default = None,
        primary_key = True
    )

    username: str = Field(
        min_length = 3,
        max_length = 50,
        unique = True,
        index = True
    )

    hashed_password: str

    is_active: bool = Field(
        default = True
    )

    role: str = Field(
        default = "customer",
        max_length = 20
    )

    orders: list["Order"] = Relationship(
        back_populates = "user"
    )

class OutboxEvent(SQLModel, table = True):
    __tablename__ = "outbox_events"
    id: int | None = Field(
        default = None,
        primary_key = True
    )

    event_type: str = Field(
        min_length = 1,
        max_length = 50
    )

    aggregate_type: str = Field(
        min_length = 1,
        max_length = 50
    )

    aggregate_id: int = Field(
        gt = 0
    )

    payload: dict[str, Any] = Field(
        default_factory = dict,
        sa_column = Column(
            JSON().with_variant(
                JSONB(),
                "postgresql"
            ),
            nullable = False
        )
    )

    created_at: datetime = Field(
        sa_column = Column(
            DateTime(timezone = True),
            server_default = func.now(),
            nullable = False
        )
    )

    processed_at: datetime | None = Field(
        default = None,
        sa_column = Column(
            DateTime(timezone = True),
            nullable = True,
            index = True
        ),
    )

class InboxEvent(SQLModel, table = True):
    __tablename__ = "inbox_events"

    id: int | None = Field(
        default=None,
        primary_key=True
    )

    event_id: int = Field(
        nullable=False,
        unique=True
    )

    event_type: str = Field(
        max_length=50,
        nullable=False
    )

    processed_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone = True),
            server_default = func.now(),
            nullable = False
        )
    )

class NotificationJob(SQLModel, table = True):
    __tablename__ = "notification_jobs"

    __table_args__ = (
        UniqueConstraint(
            "event_id",
            "job_type",
            name = "uq_notification_jobs_event_id_job_type"
        ),
        CheckConstraint(
            "retry_count >= 0",
            name = "ck_notification_jobs_retry_count_nonnegative"
        ),
        CheckConstraint(
            "NOT (processed_at IS NOT NULL AND failed_at IS NOT NULL)",
            name = "ck_notification_jobs_processed_failed_not_null_together"
        ),
        CheckConstraint(
            "(lease_until IS NULL AND claimed_by IS NULL) OR (claimed_by IS NOT NULL AND lease_until IS NOT NULL)",
            name = "ck_notification_jobs_lease_until_claimed_by_synchronized"
        ),
    )

    id: int | None = Field(
        default = None,
        primary_key = True
    )

    event_id: int = Field(
        nullable = False
    )

    job_type: str = Field(
        max_length = 50,
        nullable = False
    )

    payload: dict[str, Any] = Field(
        default_factory = dict,
        sa_column = Column(
            JSON().with_variant(
                JSONB(),
                "postgresql"
            ),
            nullable = False
        )
    )

    created_at: datetime = Field(
        sa_column = Column(
            DateTime(timezone = True),
            server_default = func.now(),
            nullable = False
        )
    )

    processed_at: datetime | None = Field(
        default = None,
        sa_column = Column(
            DateTime(timezone = True),
            nullable = True,
            index = True
        ),
    )

    retry_count: int = Field(
        default = 0,
        nullable = False
    )

    next_attempt_at: datetime = Field(
        sa_column = Column(
            DateTime(timezone = True),
            server_default = func.now(),
            nullable = False,
        )
    )

    last_error: str | None = Field(
        default = None,
        max_length = 500,
        nullable = True
    )

    failed_at: datetime | None = Field(
        default = None,
        sa_column = Column(
            DateTime(timezone = True),
            nullable = True,
        ),
    )

    lease_until: datetime = Field(
        default = None,
        sa_column = Column(
            DateTime(timezone = True),
            nullable = True,
        )
    )

    claimed_by: str = Field(
        default = None,
        max_length = 100,
        nullable = True
    )

    claim_version: int = Field(
        default=0,
        nullable=False
    )