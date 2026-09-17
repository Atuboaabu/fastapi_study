from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from main_db import Product, ProductCreate, ProductUpdate
from exceptions import ProductNotFoundException, ProductSkuExistsException, ProductInUseException

def get_product(
    product_id: int,
    session: Session
) -> Product:
    product = session.get(Product, product_id)
    
    if product is None:
        raise ProductNotFoundException(product_id)
    
    return product

def create_product(
    product: ProductCreate,
    session: Session
) -> Product:
    statement = select(Product).where(Product.sku == product.sku)
    existing_product = session.exec(statement).first()
    if existing_product is not None:
        raise ProductSkuExistsException(product.sku)

    db_product = Product.model_validate(product)
    session.add(db_product)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise ProductSkuExistsException(product.sku)
    session.refresh(db_product)

    return db_product

def get_products(
    session: Session
) -> list[Product]:
    statement = select(Product)
    products = session.exec(statement).all()
    return products

def del_product(
    product: Product,
    session: Session
) -> None:
    try:
        session.delete(product)
        session.commit()
    except IntegrityError:
        session.rollback()
        raise ProductInUseException(product.id)

def patch_product(
    update_product: ProductUpdate,
    product: Product,
    session: Session
) -> Product:
    update_data = update_product.model_dump(
        exclude_unset=True
    )
    product.sqlmodel_update(
        update_data
    )
    session.commit()
    session.refresh(product)
    return product

def put_product(
    update_product: ProductCreate,
    product: Product,
    session: Session
) -> Product:
    update_data = update_product.model_dump()
    product.sqlmodel_update(
        update_data
    )
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise ProductSkuExistsException(product.sku)
    session.refresh(product)
    return product