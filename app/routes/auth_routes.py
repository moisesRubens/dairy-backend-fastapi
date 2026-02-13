from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from dependecies import make_session, validate_token
from controllers.auth_controller import get_all, login_user, create, get_sale_point, delete_sale_point, logout_controller

auth_router = APIRouter(prefix="/auth", tags=["Auth"])

@auth_router.post("/cadastrar")
async def store(name: str, email:str, password: str, session = Depends(make_session)):
    sale_point = await create(name, email, password, session)
    return {"novo ponto de venda cadastrado": sale_point}


@auth_router.post("/login")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session = Depends(make_session)):
    token = await login_user(form_data, session)
    return {"access_token": token, "token_type": "bearer"}


@auth_router.get("/")
async def index(user = Depends(validate_token), session = (Depends(make_session))):
    sales_points = await get_all(session)
    return sales_points


@auth_router.get("/{id}")
async def show(id: int, user = Depends(validate_token), session = Depends(make_session)):
    sale_point = await get_sale_point(id, session)
    return {"sale_points": sale_point}    


@auth_router.post("/logout")
async def logout(token = Depends(validate_token), session = Depends(make_session)):
    message = await logout_controller(token, session)
    return {"message": message}


@auth_router.delete("/{id}")
async def destroy(id: int, user = Depends(validate_token), session = Depends(make_session)):
    sale_point = await delete_sale_point(id, session)
    return {"sale_point": sale_point}
