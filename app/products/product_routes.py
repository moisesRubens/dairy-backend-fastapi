from fastapi import APIRouter, Depends, Response, status
from typing import List, Optional
from dependecies import make_session
from datetime import date
from products.product_schema import ProductRequestDTO
from sales_points.sale_point_dependencies import validate_token
from products.product_controller import delete_product_controller, create_product_controller, get_all_products_controller, delete_all_products_controller, retirar_produtos_controller, get_products_by_sale_point_controller, return_products_to_storage_controller, get_product_controller, edit_product_controller

product_router = APIRouter(prefix="/products", tags=["Product"])

@product_router.get("/")
async def index(user = Depends(validate_token), session = Depends(make_session)):
    products = await get_all_products_controller(session)
    return products


@product_router.post("/", status_code=201)
async def store(name: str, price: float, amount: int = None, kg: float = None, liters: float = None, user = Depends(validate_token), session = Depends(make_session)):
    product_data = await create_product_controller(name, price, amount, kg, liters,session)
    return product_data, 


@product_router.delete("/{id}")
async def destroy(id: int, user = Depends(validate_token), session = Depends(make_session)):
    product_data = await delete_product_controller(session, id)
    return product_data


@product_router.get("/{id}")
async def show(id: int, user = Depends(validate_token), session = Depends(make_session)):
    result = await get_product_controller(session, id)
    return result


@product_router.patch("/{id}")
async def edit(id: int, product_request: ProductRequestDTO, user = Depends(validate_token), session = Depends(make_session)):
    result = await edit_product_controller(session, id, product_request)
    return result


@product_router.delete("/")
async def delete_all(user = Depends(validate_token), session = Depends(make_session)):
    await delete_all_products_controller(session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)