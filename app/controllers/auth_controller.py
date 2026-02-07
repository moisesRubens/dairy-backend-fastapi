from typing import Annotated
from services.sale_point_service import get_all_sales_points, validate_token
from models.model import SalePoints
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from dependecies import make_session


async def get_all(status = Depends(validate_token), session = Depends(make_session)):
    if not status: 
        raise Exception("Token invalido")
    
    sales_points = await get_all_sales_points(session)
    return sales_points