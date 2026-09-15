from sqlmodel import Field, SQLModel, Relationship, create_engine
from fastapi import FastAPI
from contextlib import asynccontextmanager
from sqlalchemy import event, CheckConstraint


########################################################
#########              ORDER ITEM              #########
########################################################
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

class OrderItemCreate(SQLModel):
    product_id: int = Field(gt = 0)
    quantity: int = Field(gt = 0)

class OrderItemPublic(SQLModel):
    id: int
    product_id: int
    quantity: int

class Order(SQLModel, table = True):
    __tablename__ = "orders"
    id: int | None = Field(
        default=None,
        primary_key = True
    )
    status: str = Field(
        default="pending",
        max_length=20
    )
    items: list["OrderItem"] = Relationship(
        back_populates="order"
    )

########################################################
#########              ORDER                   #########
########################################################
class OrderCreate(SQLModel):
    items: list[OrderItemCreate] = Field(min_length=1)

class OrderPublic(SQLModel):
    id: int
    status: str
    items: list[OrderItemPublic]

class OrderListResponse(SQLModel):
    items: list[OrderPublic]
    total: int
    offset: int
    limit: int

########################################################
#########            PRODUCT                   #########
########################################################

class ProductBase(SQLModel):
    sku: str = Field(min_length = 3, max_length = 50, unique = True)
    name: str = Field(min_length = 1, max_length = 100)
    price: float = Field(gt = 0)
    stock: int = Field(ge = 0)
    description: str | None =  Field(default = None, max_length=500)

class Product(ProductBase, table = True):
    id: int | None = Field(
        default=None,
        primary_key=True,
    )
    order_items: list["OrderItem"] = Relationship(
        back_populates="product"
    )

class ProductCreate(ProductBase):
    pass

class ProductPublic(ProductBase):
    id: int

class ProductUpdate(SQLModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100
    )
    price: float | None = Field(
        default=None,
        gt=0
    )
    stock: int | None = Field(
        default=None,
        ge=0
    )
    description: str | None =  Field(
        default=None,
        max_length=500
    )

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {
    "check_same_thread": False
}

engine = create_engine(
    sqlite_url,
    connect_args=connect_args,
    echo=True,
)

@event.listens_for(engine, "connect")
def enable_sqlite_foreign_keys(
    dbapi_connection,
    connection_record,
):
    cursor = dbapi_connection.cursor()
    cursor.execute(
        "PRAGMA foreign_keys=ON"
    )
    cursor.close()


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield