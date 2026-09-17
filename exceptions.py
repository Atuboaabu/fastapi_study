from main_db import Product, ProductCreate, ProductUpdate


class ProductNotFoundException(Exception):
    def __init__(self, product_id: int)->None:
        self.product_id = product_id

class ProductSkuExistsException(Exception):
    def __init__(self, product_sku: str)->None:
        self.product_sku = product_sku

class ProductInUseException(Exception):
    def __init__(self, product_id: int) -> None:
        self.product_id = product_id

class DuplicateProductException(Exception):
    pass

class InsufficientStockException(Exception):
    def __init__(self, product_id: int):
        self.product_id = product_id

class OrderNotFoundException(Exception):
    def __init__(self, order_id: int):
        self.order_id = order_id



