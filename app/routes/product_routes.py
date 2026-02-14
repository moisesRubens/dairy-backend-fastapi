from fastapi import APIRouter, Depends
from dependecies import make_session, validate_token
from controllers.product_controller import delete_product_controller, create_product_controller, get_all_products_controller

product_router = APIRouter(prefix="/produto", tags=["Product"])

@product_router.get("/")
async def index(session = Depends(make_session)):
    products = get_all_products_controller(session)
    return {"products": products}

@product_router.post("/cadastrar")
async def store(name: str, price: float, amount: int = None, kg: float = None, liters: float = None, user = Depends(validate_token), session = Depends(make_session)):
    product_data = create_product_controller(name, price, amount, kg, liters,session)
    return {"product created": product_data}

@product_router.delete("/{id}")
async def destroy(id: int, user = Depends(validate_token), session = Depends(make_session)):
    product_data = delete_product_controller(session, id)
    return {"Produto excluido": product_data}