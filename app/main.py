from fastapi import FastAPI
from sales_points.auth_routes import auth_router
from orders.order_routes import order_router
from products.product_routes import product_router

app = FastAPI()
app.include_router(auth_router)
app.include_router(order_router)
app.include_router(product_router)