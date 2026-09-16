from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from main_db import Product, ProductCreate, ProductUpdate

# procudt services excetion 定义
class ProductNotFoundException(Exception):
    pass

class ProductSkuExistsException(Exception):
    pass

class ProductIntergrityException(Exception):
    pass

def get_product(
    product_id: int,
    session: Session
) -> Product:
    product = session.get(Product, product_id)
    
    if product is None:
        raise ProductNotFoundException()
    
    return product

def create_product(
    product: ProductCreate,
    session: Session
) -> Product:
    statement = select(Product).where(Product.sku == product.sku)
    existing_product = session.exec(statement).first()
    if existing_product is not None:
        raise ProductSkuExistsException()

    db_product = Product.model_validate(product)
    session.add(db_product)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise ProductIntergrityException()
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
    session.delete(product)
    session.commit()

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
    session.commit()
    session.refresh(product)
    return product