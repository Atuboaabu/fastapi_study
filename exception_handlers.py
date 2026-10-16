from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from exceptions import (
    ProductNotFoundException,
    DuplicateProductException,
    InsufficientStockException,
    OrderNotFoundException,
    ProductSkuExistsException,
    ProductInUseException,
    UsernameExistsException,
    InvalidCredentialsException,
    InvalidTokenException,
    InactiveUserException,
    ForbiddenException,
    InvalidOrderStateTransitionException,
)

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
    
    @app.exception_handler(UsernameExistsException)
    async def username_exists_handle(
        request: Request,
        exc: UsernameExistsException
    ):
        return JSONResponse(
            status_code = status.HTTP_409_CONFLICT,
            content = {
                "code": "USERNAME_EXISTS",
                "detail": f"Username {exc.username} already exists"
            }
        )
    
    @app.exception_handler(InvalidCredentialsException)
    async def invalid_credentials_handle(
        request: Request,
        exc: InvalidCredentialsException
    ):
        return JSONResponse(
            status_code = status.HTTP_401_UNAUTHORIZED,
            content = {
                "code": "INVALID_CREDENTIALS",
                "detail": "Invalid username or password"
            },
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )
    
    @app.exception_handler(InvalidTokenException)
    async def invalid_token_handle(
        request: Request,
        exc: InvalidTokenException
    ):
        return JSONResponse(
            status_code = status.HTTP_401_UNAUTHORIZED,
            content = {
                "code": "INVALID_TOKEN",
                "detail": "Token is invalid"
            },
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )
    
    @app.exception_handler(InactiveUserException)
    async def inactive_user_handle(
        request: Request,
        exc: InactiveUserException
    ):
        return JSONResponse(
            status_code = status.HTTP_403_FORBIDDEN,
            content = {
                "code": "USER_INACTIVE",
                "detail": "User is inactive"
            }
        )
    
    @app.exception_handler(ForbiddenException)
    async def forbidden_handle(
        request: Request,
        exc: ForbiddenException
    ):
        return JSONResponse(
            status_code = status.HTTP_403_FORBIDDEN,
            content = {
                "code": "FORBIDDEN",
                "detail": "Insufficient permissions"
            }
        )
    
    @app.exception_handler(InvalidOrderStateTransitionException)
    async def invalid_orderstatus_transition_handle(
        request: Request,
        exc: InvalidOrderStateTransitionException
    ):
        return JSONResponse(
            status_code = status.HTTP_409_CONFLICT,
            content = {
                "code": "INVALID_STATUS_TRANSITION",
                "detail": f"Invalid status transition: {exc.current_status.value} -> {exc.dest_status.value}"
            }
        )
        
    