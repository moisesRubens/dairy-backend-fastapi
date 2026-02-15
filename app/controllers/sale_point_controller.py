from services.sale_point_service import get_sale_point_service, get_all_sales_points_service, login_service, create_sale_point_service, logout_service, delete_sale_point_service
from fastapi.security import OAuth2PasswordRequestForm
from exceptions.SalePointExceptions import ExistingSalePointException, SalePointNotFound
from fastapi import HTTPException
from schemas.schema import SalePointRequestDTO


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
    return await logout_service(token, session)

def get_all_sales_points_controller(session):
    try:
        sales_points_response = get_all_sales_points_service(session)
        return sales_points_response
    except SalePointNotFound as e:
        raise HTTPException(200, detail=str(e))

async def get_sale_point(id: int, session):
    sale_point = await get_sale_point_service(id, session)
    return sale_point

def delete_sale_point_controller(id: int, session):
    try:
        sale_point_request = SalePointRequestDTO(id=id)
        sale_point_response = delete_sale_point_service(sale_point_request, session)
        return sale_point_response
    except SalePointNotFound as e:
        raise HTTPException(200, detail=str(e))
