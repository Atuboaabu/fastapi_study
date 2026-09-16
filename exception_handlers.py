from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from services import orders
from services import products

def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(orders.DuplicateProductException)
    async def duplicate_product_handle(
        request: Request,
        exc: orders.DuplicateProductException
    ):
        return JSONResponse(
            status_code = status.HTTP_400_BAD_REQUEST,
            content = {
                "detail": "Duplicate product in order" 
            }
        )
    
    @app.exception_handler(orders.ProductNotFoundException)
    async def product_not_found_handle(
        request: Request,
        exc: orders.ProductNotFoundException
    ):
        return JSONResponse(
            status_code = status.HTTP_404_NOT_FOUND,
            content = {
                "detail": f"Product {exc.product_id} not found" 
            }
        )
    
    @app.exception_handler(orders.InsufficientStockException)
    async def insufficient_stock_handle(
        request: Request,
        exc: orders.InsufficientStockException
    ):
        return JSONResponse(
            status_code = status.HTTP_409_CONFLICT,
            content = {
                "detail": f"Insufficient stock for product {exc.product_id}" 
            }
        )
    
    @app.exception_handler(orders.OrderNotFoundException)
    async def order_not_found_handle(
        request: Request,
        exc: orders.OrderNotFoundException
    ):
        return JSONResponse(
            status_code = status.HTTP_404_NOT_FOUND,
            content = {
                "detail": f"Order {exc.order_id} not found" 
            }
        )
    
    @app.exception_handler(products.ProductNotFoundException)
    async def product_not_found_handle_1(
        request: Request,
        exc: products.ProductNotFoundException
    ):
        return JSONResponse(
            status_code = status.HTTP_404_NOT_FOUND,
            content = {
                "detail": f"Product not found" 
            }
        )
    
    @app.exception_handler(products.ProductSkuExistsException)
    async def product_sku_exists_handle(
        request: Request,
        exc: products.ProductSkuExistsException
    ):
        return JSONResponse(
            status_code = status.HTTP_409_CONFLICT,
            content = {
                "detail": f"Product sku already exists" 
            }
        )
    
    @app.exception_handler(products.ProductInUseException)
    async def product_in_use_handle(
        request: Request,
        exc: products.ProductInUseException
    ):
        return JSONResponse(
            status_code = status.HTTP_409_CONFLICT,
            content = {
                "detail": f"Product {exc.product_id} in use" 
            }
        )