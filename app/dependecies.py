from models.model import db
from sqlalchemy.orm import sessionmaker
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from models.model import SalePoints, Token
from schemas.schema import SalePointResponseDTO
from jwt import decode
from decouple import config

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def make_session():
    try:
        Session = sessionmaker(bind=db)
        session = Session()
        yield session
    finally:
        session.close()

async def validate_token(token: Annotated[str, Depends(oauth2_scheme)], session = Depends(make_session)):
    if session.get(Token, token):
        raise Exception('Token expirado já')

    SECRET_KEY = config('SECRET_KEY')
    ALGORITHM = config('ALGORITHM')
    form_data = decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    data_user = session.query(SalePoints).filter(SalePoints.name == form_data.get("sub")).first()
    return token
            
     
