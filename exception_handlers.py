from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from exceptions import (
    ProductNotFoundException,
    DuplicateProductException,
    InsufficientStockException,
    OrderNotFoundException,
    ProductSkuExistsException,
    ProductInUseException)

def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DuplicateProductException)
    async def duplicate_product_handle(
        request: Request,
        exc: DuplicateProductException
    ):
        return JSONResponse(
            status_code = status.HTTP_400_BAD_REQUEST,
            content = {
                "code": "PRODUCT_DUPLICATE",
                "detail": "Duplicate product in order" 
            }
        )
    
    @app.exception_handler(ProductNotFoundException)
    async def product_not_found_handle(
        request: Request,
        exc: ProductNotFoundException
    ):
        return JSONResponse(
            status_code = status.HTTP_404_NOT_FOUND,
            content = {
                "code": "PRODUCT_NOT_FOUND",
                "detail": f"Product {exc.product_id} not found" 
            }
        )
    
    @app.exception_handler(InsufficientStockException)
    async def insufficient_stock_handle(
        request: Request,
        exc: InsufficientStockException
    ):
        return JSONResponse(
            status_code = status.HTTP_409_CONFLICT,
            content = {
                "code": "PRODUCT_STOCK_INSUFFICIENT",
                "detail": f"Insufficient stock for product {exc.product_id}" 
            }
        )
    
    @app.exception_handler(OrderNotFoundException)
    async def order_not_found_handle(
        request: Request,
        exc: OrderNotFoundException
    ):
        return JSONResponse(
            status_code = status.HTTP_404_NOT_FOUND,
            content = {
                "code": "ORDER_NOT_FOUND",
                "detail": f"Order {exc.order_id} not found" 
            }
        )
    
    @app.exception_handler(ProductSkuExistsException)
    async def product_sku_exists_handle(
        request: Request,
        exc: ProductSkuExistsException
    ):
        return JSONResponse(
            status_code = status.HTTP_409_CONFLICT,
            content = {
                "code": "PRODUCT_SKU_EXISTS",
                "detail": f"Product sku {exc.product_sku} already exists" 
            }
        )
    
    @app.exception_handler(ProductInUseException)
    async def product_in_use_handle(
        request: Request,
        exc: ProductInUseException
    ):
        return JSONResponse(
            status_code = status.HTTP_409_CONFLICT,
            content = {
                "code": "PRODUCT_IN_USE",
                "detail": f"Product {exc.product_id} in use" 
            }
        )