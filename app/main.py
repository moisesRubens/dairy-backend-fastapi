import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sales_points.auth_routes import auth_router
from outbounds.outbound_routes import outbound_router
from orders.order_routes import order_router
from products.product_routes import product_router
from stock_requests.stock_request_routes import stock_request_router
from metrics.metrics_routes import metrics_router
from clients.client_routes import client_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.include_router(auth_router)
app.include_router(order_router)
app.include_router(product_router)
app.include_router(outbound_router)
app.include_router(stock_request_router)
app.include_router(metrics_router)
app.include_router(client_router)

# Serve os arquivos estáticos (fotos de produto). O diretório é resolvido a
# partir da raiz do repo, onde o uvicorn é iniciado. Garante que exista.
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

origins = [
    "http://localhost:5173", 
    "http://127.0.0.1:5173",
    "http://localhost:8080", 
    "http://127.0.0.1:8080",
    "http://localhost:58000",
    "http://127.0.0.1:58000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  
    allow_methods=["*"],
    allow_headers=["*"],  
    expose_headers=["*"]  
)