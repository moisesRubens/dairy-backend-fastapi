from fastapi import FastAPI
from sales_points.auth_routes import auth_router
from orders.order_routes import order_router
from products.product_routes import product_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.include_router(auth_router)
app.include_router(order_router)
app.include_router(product_router)

origins = [
    "http://localhost:5173", 
    "http://127.0.0.1:5173",
    "http://localhost:8080", 
    "http://127.0.0.1:8080"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  # Mantenha True para cookies/auth
    allow_methods=["*"],
    allow_headers=["*"],  # Permite todos os cabeçalhos
    expose_headers=["*"]  # Importante para erros
)