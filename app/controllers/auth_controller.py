
from services.sale_point_service import get_all_sales_points, make_login
from models.model import SalePoints
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from dependecies import validate_token

async def login_user(form_data: OAuth2PasswordRequestForm, session):
    return await make_login(form_data, session)

async def get_all(session, status = Depends(validate_token)):
    if not status: 
        raise Exception("Token invalido")
    
    sales_points = await get_all_sales_points(session)
    return sales_points