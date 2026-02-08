
from services.sale_point_service import get_sale_point_service, get_all_sales_points, make_login, create_sale_point, delete_sale_point_service
from fastapi.security import OAuth2PasswordRequestForm

async def login_user(form_data: OAuth2PasswordRequestForm, session):
    return await make_login(form_data, session)

async def get_all(session):
    
    sales_points = await get_all_sales_points(session)
    return sales_points

async def create(name, email, password, session):
    sale_point = await create_sale_point(name, email, password, session)
    return sale_point

async def get_sale_point(id: int, session):
    sale_point = await get_sale_point_service(id, session)
    return sale_point

async def delete_sale_point(id: int, session):
    sale_point = await delete_sale_point_service(id, session)
    return sale_point
