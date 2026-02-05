from fastapi import FastAPI
from routes.auth_routes import auth_router
from routes.order_routes import order_router
from routes.product_routes import product_router

app = FastAPI()
app.include_router(auth_router)
app.include_router(order_router)
app.include_router(product_router)