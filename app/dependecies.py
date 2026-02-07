from models.model import db
from sqlalchemy.orm import sessionmaker
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from models.model import SalePoints

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def make_session():
    try:
        Session = sessionmaker(bind=db)
        session = Session()
        yield session
    finally:
        session.close()

async def validate_token(token: Annotated[str, Depends(oauth2_scheme)], session = Depends(make_session)):
    return session.query(SalePoints).filter(SalePoints.name == token).first()