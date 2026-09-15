from typing import Annotated
from sqlmodel import select
from sqlalchemy.exc import IntegrityError
from fastapi import Path, Depends, status, HTTPException, APIRouter, Response

from dependencies import SessionDep

from main_db import Product, ProductCreate, ProductPublic, ProductUpdate

router = APIRouter(
    prefix = "/products",
    tags = ["products"]
)

# product 内部 dependencies
def get_product_or_404(product_id: Annotated[int, Path(gt=0)], session: SessionDep):
    product = session.get(Product, product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return product
ProductDep = Annotated[Product, Depends(get_product_or_404)]

# POST "/products/"
@router.post(
    "/",
    response_model=ProductPublic,
    status_code=status.HTTP_201_CREATED
)
def create_product(
    product: ProductCreate,
    session: SessionDep
):
    statement = select(Product).where(Product.sku == product.sku)
    existing_product = session.exec(statement).first()
    if existing_product is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product sku already exists"
        )

    db_product = Product.model_validate(product)
    session.add(db_product)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product sku already exists"
        )
    session.refresh(db_product)

    return db_product

# GET "/products/"
@router.get(
    "/",
    response_model = list[ProductPublic]
)
def get_products(
    session: SessionDep
):
    statement = select(Product)
    products = session.exec(statement).all()
    return products

# GET "/products/{product_id}"
@router.get(
    "/{product_id}",
    response_model = ProductPublic
)
def get_product(product: ProductDep):
    return product

# DELETE "/products/{product_id}"
@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def del_product(
    product: ProductDep,
    session: SessionDep
):
    session.delete(product)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# PATCH "/products/{product_id}"
@router.patch(
    "/{product_id}",
    response_model = ProductPublic
)
def patch_product(
    update_product: ProductUpdate,
    product: ProductDep,
    session: SessionDep
):
    update_data = update_product.model_dump(
        exclude_unset=True
    )
    product.sqlmodel_update(
        update_data
    )
    session.commit()
    session.refresh(product)
    return product

# PUT "/products/{product_id}"
@router.put(
    "/{product_id}",
    response_model = ProductPublic
)
def put_product(
    update_product: ProductCreate,
    product: ProductDep,
    session: SessionDep
):
    update_data = update_product.model_dump()
    product.sqlmodel_update(
        update_data
    )
    session.commit()
    session.refresh(product)
    return product

