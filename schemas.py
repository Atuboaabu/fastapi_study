from sqlmodel import SQLModel, Field

class OrderItemCreate(SQLModel):
    product_id: int = Field(gt = 0)
    quantity: int = Field(gt = 0)

class OrderItemPublic(SQLModel):
    id: int
    product_id: int
    quantity: int

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

class ProductCreate(SQLModel):
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

class ProductPublic(SQLModel):
    id: int

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