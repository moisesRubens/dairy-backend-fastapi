import os
from fastapi import APIRouter, Depends, Response, status, UploadFile, File
from typing import List, Optional
from dependencies import make_session
from datetime import date
from products.product_schema import ProductRequestDTO
from sales_points.sale_point_dependencies import validate_token, require_admin
from products.product_controller import delete_product_controller, create_product_controller, get_all_products_controller, delete_all_products_controller, retirar_produtos_controller, get_products_by_sale_point_controller, return_products_to_storage_controller, get_product_controller, edit_product_controller, set_product_image_controller

product_router = APIRouter(prefix="/products", tags=["Product"])

@product_router.get("/")
async def index(user = Depends(validate_token), session = Depends(make_session)):
    # Antes era 100% aberto (sem token). Agora exige login (qualquer papel).
    products = await get_all_products_controller(session)
    return products


@product_router.post("/", status_code=201)
async def store(name: str, price: float, amount: int = None, kg: float = None, liters: float = None, user = Depends(require_admin), session = Depends(make_session)):
    product_data = await create_product_controller(name, price, amount, kg, liters,session)
    return product_data


@product_router.delete("/{id}")
async def destroy(id: int, user = Depends(require_admin), session = Depends(make_session)):
    product_data = await delete_product_controller(session, id)
    return product_data


@product_router.get("/{id}")
async def show(id: int, user = Depends(validate_token), session = Depends(make_session)):
    result = await get_product_controller(session, id)
    return result


@product_router.patch("/{id}")
async def edit(id: int, product_request: ProductRequestDTO, user = Depends(require_admin), session = Depends(make_session)):
    result = await edit_product_controller(session, id, product_request)
    return result


@product_router.post("/{id}/image")
async def upload_image(id: int, file: UploadFile = File(...), user = Depends(require_admin), session = Depends(make_session)):
    # Extensão vem do filename enviado; default .png se não houver.
    ext = os.path.splitext(file.filename or "")[1].lower() or ".png"
    file_bytes = await file.read()
    result = await set_product_image_controller(session, id, file_bytes, ext)
    return result


@product_router.delete("/")
async def delete_all(user = Depends(require_admin), session = Depends(make_session)):
    await delete_all_products_controller(session)
    return Response(status_code=status.HTTP_204_NO_CONTENT)