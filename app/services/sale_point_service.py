from fastapi import HTTPException, status
from models.model import SalePoints, Token
from schemas.schema import SalePointResponseDTO
from pwdlib import PasswordHash
from fastapi.security import OAuth2PasswordRequestForm
from jwt import encode
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from decouple import config

pwd_context = PasswordHash.recommended()

async def create_sale_point(name: str, email: str, password: str, session):
    sale_point = session.query(SalePoints).filter(SalePoints.name == name).first()
    
    if(sale_point):
        return "Ja existe"
    
    hashed_pw = pwd_context.hash(password)
    sale_point = SalePoints(name, email, hashed_pw)
    session.add(sale_point)
    session.commit()
    return SalePointResponseDTO.model_validate(sale_point)

async def login_service(form_data: OAuth2PasswordRequestForm, session):
    SECRET_KEY = config('SECRET_KEY')
    EXPIRE_TOKEN = int(config('EXPIRE_TIME_TOKEN'))
    ALGORITHM = config('ALGORITHM')
    sale_point = session.query(SalePoints).filter(SalePoints.name == form_data.username).first()

    if not sale_point:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario nao encontrado"
        )
    if not pwd_context.verify(form_data.password, sale_point.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="senha incorreta"
        )
    to_encode = {"sub": sale_point.name}
    expire = datetime.now(tz=ZoneInfo("America/Sao_Paulo")) + timedelta(minutes=EXPIRE_TOKEN)
    to_encode.update({'exp': expire})
    token = encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token
    

async def get_all_sales_points(session):
    sales_points = session.query(SalePoints).all()
    return [SalePointResponseDTO.model_validate(sp) for sp in sales_points]


async def logout_service(token, session):
    revoked_token = Token(id=token)
    session.add(revoked_token)
    session.commit()
    return 'Logout sucedido'

async def get_sale_point_service(id: int, session):
    sale_point = session.query(SalePoints).filter(SalePoints.id == id).first()

    if(sale_point):
        return SalePointResponseDTO.model_validate(sale_point)

async def delete_sale_point_service(id: int, session):
    sale_point = session.get(SalePoints, id)

    if sale_point:
        session.delete(sale_point)
        session.commit()

    return SalePointResponseDTO.model_validate(sale_point)


