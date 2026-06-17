from sales_points.sale_point_service import get_sale_point_service, get_all_sales_points_service, login_service, create_sale_point_service, logout_service, delete_sale_point_service, delete_all_sales_points_service, create_outbound_service, return_outbounds_service, delete_orders_service, delete_outbounds_service
from fastapi.security import OAuth2PasswordRequestForm
from sales_points.sale_point_exceptions import ExistingSalePointException, SalePointNotFound
from fastapi import HTTPException
from sales_points.sale_point_schema import SalePointRequestDTO
from exceptions import ExpiredTokenException
from datetime import date
from sqlalchemy.orm import Session
from products.product_service import get_products_by_sale_point_service
from products.product_schema import RetirarProdutosRequestDTO


async def create_sale_point_controller(name, email, password, session):
    try:
        sale_point_request = SalePointRequestDTO(name=name, email=email, password=password)
        sale_point_data = await create_sale_point_service(sale_point_request, session)
        return sale_point_data
    except ExistingSalePointException as e:
        raise HTTPException(409, detail=str(e))

async def login_controller(form_data: OAuth2PasswordRequestForm, session):
    try:
        token = login_service(form_data, session)
        return token
    except SalePointNotFound as e:
        raise HTTPException(404, detail=str(e))
    except Exception as e:
        raise e

async def logout_controller(token, session):
    try:
        message = await logout_service(token, session)
        return message
    except ExpiredTokenException as e:
        raise HTTPException(409, detail=str(e))

async def get_all_sales_points_controller(session):
    try:
        sales_points_response = get_all_sales_points_service(session)
        return sales_points_response
    except SalePointNotFound as e:
        raise HTTPException(200, detail=str(e))

async def get_sale_point(id: int, session):
    try:
        sale_point = await get_sale_point_service(id, session)
        return sale_point
    except SalePointNotFound as e:
        raise HTTPException(404, detail=str(e))

async def delete_sale_point_controller(id: int, token, session):
    try:
        sale_point_request = SalePointRequestDTO(id=id)
        sale_point_response = await delete_sale_point_service(sale_point_request, token, session)
        return sale_point_response
    except SalePointNotFound as e:
        raise HTTPException(200, detail=str(e))

async def delete_all_sales_points_controller(session):
    try:
        delete_all_sales_points_service(session)
    except Exception as e:
        raise HTTPException(500, detail=str(e))
    
async def get_outbounds_controller(id: int, date: date, session: Session):
    try:
        return await get_products_by_sale_point_service(id, session, date, False)
    except Exception as e:
        raise e
    
async def create_outbound_controller(session: Session, id: int, outbound_request: RetirarProdutosRequestDTO):
    try:
        return await create_outbound_service(session, id, outbound_request)
    except SalePointNotFound as e:
        raise HTTPException(404, detail=str(e))
    except Exception as e:
        raise HTTPException(500, "Internal server error")
    
async def delete_outbounds_controller(session: Session, id: int):
    return await delete_outbounds_service(session, id)

async def return_outbounds_controller(session: Session, id: int):
    try:
        return await return_outbounds_service(session, id)
    except Exception:
        raise
    
async def delete_orders_controller(session: Session, id: int):
    try:
        return await delete_orders_service(session, id)
    except Exception:
        raise