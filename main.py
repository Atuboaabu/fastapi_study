from fastapi import FastAPI
from routers import products, orders, auth, users, admin_orders
from exception_handlers import register_exception_handlers

app = FastAPI()

register_exception_handlers(app)

app.include_router(products.router)
app.include_router(orders.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin_orders.router)
