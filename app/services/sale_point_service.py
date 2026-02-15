from fastapi import HTTPException, status
from models.model import SalePoints, Token
from schemas.schema import SalePointResponseDTO, SalePointRequestDTO
from pwdlib import PasswordHash
from fastapi.security import OAuth2PasswordRequestForm
from jwt import encode
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from decouple import config
from exceptions.SalePointExceptions import ExistingSalePointException, SalePointNotFound

pwd_context = PasswordHash.recommended()

async def create_sale_point_service(sale_point_request: SalePointRequestDTO, session):
    sale_point = session.query(SalePoints).filter(SalePoints.name.upper() == sale_point_request.name.upper()).first()
    if(sale_point):
        raise ExistingSalePointException()
    
    sale_point = SalePoints()
    hashed_pw = pwd_context.hash(sale_point_request.password)
    sale_point.password = hashed_pw
    sale_point.name = sale_point_request.name
    sale_point.email = sale_point_request.email
    session.add(sale_point)
    session.commit()
    return SalePointResponseDTO.model_validate(sale_point)

def login_service(form_data: OAuth2PasswordRequestForm, session):
    SECRET_KEY = config('SECRET_KEY')
    EXPIRE_TOKEN = int(config('EXPIRE_TIME_TOKEN'))
    ALGORITHM = config('ALGORITHM')

    sale_point = session.query(SalePoints).filter(SalePoints.name == form_data.username).first()
    if not sale_point:
        raise SalePointNotFound()
    if not pwd_context.verify(form_data.password, sale_point.password):
        raise HTTPException(401, "invalid credentials")
    to_encode = {"sub": sale_point.name, "id": sale_point.id}
    expire = datetime.now(tz=ZoneInfo("America/Sao_Paulo")) + timedelta(minutes=EXPIRE_TOKEN)
    to_encode.update({'exp': expire})
    token = encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token
    

def get_all_sales_points_service(session):
    sales_points = session.query(SalePoints).all()
    if not sales_points:
        raise SalePointNotFound("Empty storage")
    
    result = []
    for sale_point in sales_points:
        result.append(SalePointResponseDTO.model_validate(sale_point))
    return result


async def logout_service(token, session):
    revoked_token = Token(id=token)
    session.add(revoked_token)
    session.commit()
    return 'Logout sucedido'

async def get_sale_point_service(id: int, session):
    sale_point = session.query(SalePoints).filter(SalePoints.id == id).first()

    if(sale_point):
        return SalePointResponseDTO.model_validate(sale_point)

def delete_sale_point_service(sale_point_request: SalePointRequestDTO, session):
    sale_point = session.get(SalePoints, sale_point_request.id)
    if not sale_point:
        raise SalePointNotFound()
    sale_point_response = SalePointResponseDTO.model_validate(sale_point)
    #logout
    session.delete(sale_point)
    session.commit()
    return sale_point_response




