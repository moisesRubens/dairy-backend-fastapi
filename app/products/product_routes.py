from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from dependecies import make_session
from datetime import date
from products.product_schema import RetirarProdutosRequestDTO, ItemRetiradaDTO, ReturnToStorageRequestDTO, ItemToReturnToStorageDTO
from sales_points.sale_point_dependencies import validate_token
from products.product_controller import delete_product_controller, create_product_controller, get_all_products_controller, delete_all_products_controller, retirar_produtos_controller, get_products_by_sale_point_controller, return_products_to_storage_controller

product_router = APIRouter(prefix="/produto", tags=["Product"])

@product_router.get("/")
async def index(user = Depends(validate_token), session = Depends(make_session)):
    products = get_all_products_controller(session)
    return {"products": products}

@product_router.post("/retirar")
async def retirar_produtos(
    request: RetirarProdutosRequestDTO,
    user = Depends(validate_token),
    session = Depends(make_session)
):
    result = retirar_produtos_controller(session, user['sub'], request.produtos)
    return result

@product_router.get("/retiradas")
async def list_all(sale_point_id: Optional[int] = None, date: Optional[date] = None,  user = Depends(validate_token), session = Depends(make_session)):
    result = get_products_by_sale_point_controller(sale_point_id, date, session, user)
    return {"retiradas": result}

@product_router.post("/retornar-ao-estoque")
async def subtrair_estoque(
    sale_point_id: Optional[int] = None, 
    user = Depends(validate_token),
    session = Depends(make_session)
):
    return return_products_to_storage_controller(session, user, sale_point_id)

@product_router.post("/cadastrar")
async def store(name: str, price: float, amount: int = None, kg: float = None, liters: float = None, user = Depends(validate_token), session = Depends(make_session)):
    product_data = create_product_controller(name, price, amount, kg, liters,session)
    return {"product created": product_data}

@product_router.delete("/{id}")
async def destroy(id: int, user = Depends(validate_token), session = Depends(make_session)):
    product_data = delete_product_controller(session, id)
    return {"Produto excluido": product_data}


@product_router.delete("/")
async def delete_all(user = Depends(validate_token), session = Depends(make_session)):
    delete_all_products_controller(session)
    return {"message": "Excluded products"}