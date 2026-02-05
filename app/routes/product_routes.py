from fastapi import APIRouter, Depends
from dependecies import make_session
from models.model import Product

product_router = APIRouter(prefix="/produto", tags=["Product"])

@product_router.get("/")
async def index():
    return {"message": "lista de produtos"}

@product_router.post("/cadastrar")
async def store(name: str, price: float, amount: int = None, kg: float = None, liters: float = None, session = Depends(make_session)):
    product = Product(name, price, amount, kg, liters)
    
    session.add(product)
    session.commit()
    session.refresh(product)
    
    return {"message": "cadastro de produto"}

@product_router.delete("/{id}")
async def destroy(id: int, session = Depends(make_session)):
    product = session.get(Product, id)
    
    if not product:
        raise HTTPException(status_code=404, detail="Product nao encontrado")

    session.delete(product)
    session.commit()

    return {"message": "Produto excluido"}