from fastapi import FastAPI
from main_db import lifespan
from routers import products, orders

app = FastAPI(lifespan = lifespan)

app.include_router(products.router)
app.include_router(orders.router)
