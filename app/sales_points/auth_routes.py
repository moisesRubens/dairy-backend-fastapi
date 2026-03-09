from typing import Annotated
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sales_points.sale_point_dependencies import make_session, validate_token, oauth2_scheme
from sales_points.sale_point_controller import get_all_sales_points_controller, login_controller, create_sale_point_controller, get_sale_point, delete_sale_point_controller, logout_controller, delete_all_sales_points_controller
from orders.order_controller import get_orders_by_sale_point_id_controller

auth_router = APIRouter(prefix="/auth", tags=["Auth"])

@auth_router.get("/pedidos") 
async def get_orders_by_sale_point_id(
    sale_point_id: int, 
    date: Optional[str] = None, 
    user = Depends(validate_token), 
    session = Depends(make_session)
):
    result = get_orders_by_sale_point_id_controller(session, date, sale_point_id)
    return result

@auth_router.get("/sales_points")  # /auth/sales_points
async def get_sales_points_controller(
    user = Depends(validate_token), 
    session = Depends(make_session)
):
    result = []
    return result

@auth_router.post("/cadastrar")  # /auth/cadastrar
async def store(name: str, password: str, email: str = None, session = Depends(make_session)):
    sale_point_data = await create_sale_point_controller(name, email, password, session)
    return {"sale point": sale_point_data}

@auth_router.post("/login")  # /auth/login
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session = Depends(make_session)):
    token = await login_controller(form_data, session)
    return {"access_token": token, "token_type": "bearer"}

@auth_router.post("/logout")  # /auth/logout
async def logout(
    token: Annotated[str, Depends(oauth2_scheme)], 
    user_data = Depends(validate_token), 
    session = Depends(make_session)
):
    message = await logout_controller(token, session)
    return {"message": message}

# 🟡 DEPOIS: rotas GENÉRICAS (com parâmetros dinâmicos)
@auth_router.get("/")  # /auth/
async def index(user = Depends(validate_token), session = (Depends(make_session))):
    return get_all_sales_points_controller(session)

@auth_router.get("/{id}")  # /auth/1 (DEVE VIR POR ÚLTIMO!)
async def show(id: int, user = Depends(validate_token), session = Depends(make_session)):
    sale_point = await get_sale_point(id, session)
    return {"sale_points": sale_point}

@auth_router.delete("/{id}")  # /auth/1
async def destroy(
    id: int, 
    token: Annotated[str, Depends(oauth2_scheme)], 
    user = Depends(validate_token), 
    session = Depends(make_session)
):
    sale_point_response = await delete_sale_point_controller(id, token, session)
    return {"sale point deleted": sale_point_response}

@auth_router.delete("/")  # /auth/
async def delete_all(user = Depends(validate_token), session = Depends(make_session)):
    delete_all_sales_points_controller(session)
    return {"message": "Sales points excluded"}