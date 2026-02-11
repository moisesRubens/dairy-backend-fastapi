from models.model import db
from sqlalchemy.orm import sessionmaker
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from models.model import SalePoints
from schemas.schema import SalePointResponseDTO

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
        data_user = session.query(SalePoints).filter(SalePoints.name == token).first()
        return SalePointResponseDTO.model_validate(data_user)
    except Exception:
        raise HTTPException(status_code=404, detail="token not found") 
            
     
