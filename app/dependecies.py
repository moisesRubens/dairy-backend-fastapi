from models.model import db
from sqlalchemy.orm import sessionmaker
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from models.model import Token
from jwt import decode
from decouple import config
from exceptions.TokenExceptions import ExpiredTokenException

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def make_session():
    try:
        Session = sessionmaker(bind=db)
        session = Session()
        yield session
    finally:
        session.close()

async def validate_token(token: Annotated[str, Depends(oauth2_scheme)], session = Depends(make_session)):
    try:
        if session.get(Token, token):
            raise ExpiredTokenException('Token expired')
        SECRET_KEY = config('SECRET_KEY')
        ALGORITHM = config('ALGORITHM')
        user_data = decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return user_data
    except ExpiredTokenException as e:
        raise HTTPException(401, detail=str(e))

            
     
