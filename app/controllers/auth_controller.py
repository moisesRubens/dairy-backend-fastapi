from services.sale_point_service import get_sale_point_service, get_all_sales_points, login_service, create_sale_point, delete_sale_point_service
from fastapi.security import OAuth2PasswordRequestForm


async def create(name, email, password, session):
    sale_point = await create_sale_point(name, email, password, session)
    return sale_point

async def login_user(form_data: OAuth2PasswordRequestForm, session):
    user_data = await login_service(form_data, session)
    return user_data

async def logout_user(user, session):
    return None

async def get_all(session):
    sales_points = await get_all_sales_points(session)
    return sales_points

async def get_sale_point(id: int, session):
    sale_point = await get_sale_point_service(id, session)
    return sale_point

async def delete_sale_point(id: int, session):
    sale_point = await delete_sale_point_service(id, session)
    return sale_point
