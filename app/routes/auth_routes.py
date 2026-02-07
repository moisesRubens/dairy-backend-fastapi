from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from dependecies import make_session
from services.sale_point_service import create_sale_point, get_sale_point
from models.model import SalePoints
from controllers.auth_controller import get_all, login_user

auth_router = APIRouter(prefix="/auth", tags=["Auth"])


@auth_router.post("/cadastrar")
async def store(name: str, email:str, password: str, session = Depends(make_session)):
    sale_point = await create_sale_point(name, email, password, session)
    return {"sale_point": sale_point}


@auth_router.post("/login")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session = Depends(make_session)):
    sale_point = await login_user(form_data, session)
    return {"access_token": sale_point.name, "token_type": "bearer"}


@auth_router.get("/")
async def index(session = (Depends(make_session))):
    sales_points = await get_all(session)
    return sales_points


@auth_router.get("/{id}")
async def show(id: int, session = Depends(make_session)):
    sale_point = await get_sale_point(id, session)
    return {"sale_point": sale_point}    


@auth_router.post("/logout")
async def logout():
    return {"message": "logout"}





@auth_router.delete("/{id}")
async def destroy(id: int, session = Depends(make_session)):
    sale_point = session.get(SalePoints, id)

    if sale_point:
        session.delete(sale_point)
        session.commit()

    return {"sale_point": sale_point}
