from database.model import db
from database.money import ensure_money_schema
from sqlalchemy.orm import sessionmaker
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from database.model import Token
from jwt import decode
from decouple import config
from exceptions.common_exceptions import ExpiredTokenException

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/sessions")

async def make_session():
    ensure_money_schema(db)
    Session = sessionmaker(bind=db)
    with Session() as session:
        yield session
        




            
     
