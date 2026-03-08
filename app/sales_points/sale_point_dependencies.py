from sqlalchemy.orm import sessionmaker
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from model import db, Token, SalePoints
from jwt import decode
from decouple import config
from exceptions import ExpiredTokenException
from dependecies import make_session
from sales_points.sale_point_exceptions import SalePointNotFound

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def validate_token(token: Annotated[str, Depends(oauth2_scheme)], session = Depends(make_session)):
    try:
        SECRET_KEY = config('SECRET_KEY')
        ALGORITHM = config('ALGORITHM')
        user_data = decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sale_point_id = int(user_data.get("sub"))  
        sale_point = session.get(SalePoints, sale_point_id)

        if not sale_point:
            raise SalePointNotFound()
        if session.get(Token, token):
            raise ExpiredTokenException('Token expired')
        
        return user_data
    except ExpiredTokenException as e:
        raise HTTPException(401, detail=str(e))
    except SalePointNotFound as e:
        raise HTTPException(401, detail=str(e))