from fastapi import HTTPException, Depends
from model import SalePoints, Token
from sales_points.sale_point_schema import SalePointResponseDTO, SalePointRequestDTO
from pwdlib import PasswordHash
from fastapi.security import OAuth2PasswordRequestForm
from jwt import encode
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from decouple import config
from sales_points.sale_point_exceptions import ExistingSalePointException, SalePointNotFound
from sales_points.sale_point_dependencies import oauth2_scheme
from typing import Annotated
from sqlalchemy import func

pwd_context = PasswordHash.recommended()

async def create_sale_point_service(sale_point_request: SalePointRequestDTO, session):
    sale_point = session.query(SalePoints).filter(func.upper(SalePoints.name) == sale_point_request.name.upper()).first()
    if(sale_point):
        raise ExistingSalePointException()
    
    sale_point = SalePoints()
    hashed_pw = pwd_context.hash(sale_point_request.password)
    sale_point.password = hashed_pw
    sale_point.name = sale_point_request.name
    sale_point.email = sale_point_request.email
    session.add(sale_point)
    session.flush()
    sale_point_response = SalePointResponseDTO.model_validate(sale_point)
    session.commit()
    return sale_point_response

def login_service(form_data: OAuth2PasswordRequestForm, session):
    SECRET_KEY = config('SECRET_KEY')
    EXPIRE_TOKEN = int(config('EXPIRE_TIME_TOKEN'))
    ALGORITHM = config('ALGORITHM')

    sale_point = session.query(SalePoints).filter(SalePoints.name == form_data.username).first()
    if not sale_point:
        raise SalePointNotFound()
    if not pwd_context.verify(form_data.password, sale_point.password):
        raise HTTPException(401, "invalid credentials")
    payload = {"sub": str(sale_point.id)}
    expire = datetime.now(tz=ZoneInfo("America/Sao_Paulo")) + timedelta(minutes=EXPIRE_TOKEN)
    payload.update({'exp': expire})
    token = encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token
    

def get_all_sales_points_service(session):
    result = []
    sales_points = session.query(SalePoints).all()
    if sales_points:
        for sale_point in sales_points:
            result.append(SalePointResponseDTO.model_validate(sale_point))
    return result

def delete_all_sales_points_service(session):
    try:
        session.query(SalePoints).delete(synchronize_session="fetch")
        session.commit()
    except Exception as e:
        session.rollback()
        raise e 
    finally:
        session.close()

async def logout_service(token, session):
    revoked_token = Token()
    revoked_token.id = token
    session.add(revoked_token)
    session.commit()
    return 'Logout successful'

async def get_sale_point_service(id: int, session):
    sale_point = session.query(SalePoints).filter(SalePoints.id == id).first()
    if not sale_point:
        raise SalePointNotFound()
    
    return SalePointResponseDTO.model_validate(sale_point)


async def delete_sale_point_service(sale_point_request: SalePointRequestDTO, token, session):
    sale_point = session.get(SalePoints, sale_point_request.id)
    if not sale_point:
        raise SalePointNotFound()
    sale_point_response = SalePointResponseDTO.model_validate(sale_point)
    session.delete(sale_point)
    session.commit()
    #await logout_service(token, session)
    return sale_point_response




