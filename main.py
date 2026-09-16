from fastapi import FastAPI
from main_db import lifespan
from routers import products, orders
from exception_handlers import register_exception_handlers

app = FastAPI(lifespan = lifespan)

register_exception_handlers(app)

app.include_router(products.router)
app.include_router(orders.router)
