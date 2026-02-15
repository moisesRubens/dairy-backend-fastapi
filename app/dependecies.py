from model import db
from sqlalchemy.orm import sessionmaker
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from model import Token
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



            
     
