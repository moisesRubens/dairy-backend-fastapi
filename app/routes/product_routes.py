from fastapi import APIRouter, Depends
from dependecies import make_session
from models.model import Product
from controllers.product_controller import delete_product_controller

product_router = APIRouter(prefix="/produto", tags=["Product"])

@product_router.get("/")
async def index(session = Depends(make_session)):
    products = await get_all_products(session)
    
    return {"products": products}

@product_router.post("/cadastrar")
async def store(name: str, price: float, amount: int = None, kg: float = None, liters: float = None, session = Depends(make_session)):
    product = Product()
    product.name = name
    product.price = price
    product.amount = amount
    product.kg = kg
    session.add(product)
    session.commit()
    
    return {"message": "cadastro de produto"}

@product_router.delete("/{id}")
async def destroy(id: int, session = Depends(make_session)):
    try:
        product_data = delete_product_controller(session, id)
        return {"Produto excluido": product_data}
    except Exception as e:
        raise e