from typing import Annotated
from fastapi import Path, Depends, status, APIRouter, Response

from dependencies import SessionDep

from models import Product
from schemas import ProductCreate, ProductPublic, ProductUpdate
from services import products

router = APIRouter(
    prefix = "/products",
    tags = ["products"]
)

# product 内部 dependencies
def get_product_or_404(product_id: Annotated[int, Path(gt=0)], session: SessionDep):
    return products.get_product(product_id, session)

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
    return products.create_product(
        product,
        session
    )

# GET "/products/"
@router.get(
    "/",
    response_model = list[ProductPublic]
)
def get_products(
    session: SessionDep
):
    return products.get_products(session)

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
    products.del_product(product, session)
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
    return products.patch_product(
        update_product,
        product,
        session
    )

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
    product = products.put_product(
        update_product,
        product,
        session
    )
    return product
