from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from dependecies import make_session
from services.sale_point_service import create_sale_point, get_sale_point, get_all_sales_points
from services.sale_point_service import fake_hash_password
from models.model import SalePoints

auth_router = APIRouter(prefix="/auth", tags=["Auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@auth_router.post("/cadastrar")
async def store(name: str, email:str, password: str, session = Depends(make_session)):
    sale_point = await create_sale_point(name, email, password, session)
    
    return {"sale_point": sale_point}

@auth_router.get("/")
async def index(session = Depends(make_session)):
    sales_points = await get_all_sales_points(sessqueryion)

    return sales_points

@auth_router.get("/{id}")
async def show(id: int, session = Depends(make_session)):
    sale_point = await get_sale_point(id, session)

    return {"sale_point": sale_point}    
        


@auth_router.post("/logout")
async def logout():
    return {"message": "logout"}


@auth_router.post("/login")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session = Depends(make_session)):
    sale_point = session.query(SalePoints).filter(SalePoints.name == form_data.username).first()

    if not sale_point:
        return {"message": "usuario nao encontrado"}
    
    hashed_password = fake_hash_password(form_data.password)

    if not hashed_password == sale_point.hashed_password:
        return {"message": "without password"}
    
    return {"access_token": sale_point.name, "token_type": "bearer"}
