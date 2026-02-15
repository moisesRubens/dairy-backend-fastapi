from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from dependecies import make_session, validate_token, oauth2_scheme
from controllers.sale_point_controller import get_all_sales_points_controller, login_controller, create_sale_point_controller, get_sale_point, delete_sale_point_controller, logout_controller

auth_router = APIRouter(prefix="/auth", tags=["Auth"])

@auth_router.post("/cadastrar")
async def store(name: str, password: str, email:str = None, session = Depends(make_session)):
    sale_point_data = await create_sale_point_controller(name, email, password, session)
    return {"sale point": sale_point_data}

@auth_router.post("/login")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session = Depends(make_session)):
    token = await login_controller(form_data, session)
    return {"access_token": token, "token_type": "bearer"}


@auth_router.get("/")
async def index(user = Depends(validate_token), session = (Depends(make_session))):
    return get_all_sales_points_controller(session)

@auth_router.get("/{id}")
async def show(id: int, user = Depends(validate_token), session = Depends(make_session)):
    sale_point = await get_sale_point(id, session)
    return {"sale_points": sale_point}    


@auth_router.post("/logout")
async def logout(token: Annotated[str, Depends(oauth2_scheme)], user_data = Depends(validate_token), session = Depends(make_session)):
    message = await logout_controller(token, session)
    return {"message": message}


@auth_router.delete("/{id}")
async def destroy(id: int, user = Depends(validate_token), session = Depends(make_session)):
    sale_point_response = delete_sale_point_controller(id, session)
    return {"sale point deleted": sale_point_response}
