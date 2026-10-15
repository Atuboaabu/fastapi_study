from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import CheckConstraint

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
    status: str = Field(
        default="pending",
        max_length=20
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