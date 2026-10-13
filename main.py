from fastapi import FastAPI
from database import lifespan
from routers import products, orders, auth
from exception_handlers import register_exception_handlers

app = FastAPI(lifespan = lifespan)

register_exception_handlers(app)

app.include_router(products.router)
app.include_router(orders.router)
app.include_router(auth.router)
