from sqlalchemy.orm import sessionmaker
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from model import db, Token, SalePoints
from jwt import decode
from decouple import config
from exceptions import ExpiredTokenException
from dependencies import make_session
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

        # Papel autoritativo vem do banco, não do token (defesa contra token
        # defasado se o papel da conta mudou após a emissão). Normaliza também
        # o id como inteiro para as checagens de permissão downstream.
        user_data["role"] = sale_point.role
        user_data["sale_point_id"] = sale_point.id

        return user_data
    except ExpiredTokenException as e:
        raise HTTPException(401, detail=str(e))
    except SalePointNotFound as e:
        raise HTTPException(401, detail=str(e))


async def require_admin(user = Depends(validate_token)):
    """Exige que o usuário autenticado tenha papel de administrador."""
    if user.get("role") != "admin":
        raise HTTPException(403, detail="Acesso restrito a administradores")
    return user


async def require_self_or_admin(id: int, user = Depends(validate_token)):
    """Permite a ação se o usuário for admin OU o dono do recurso (id da rota).

    Fecha o IDOR das rotas /auth/{id}/...: hoje qualquer vendedor consegue
    ler/alterar os dados de outro ponto trocando o id na URL.
    """
    if user.get("role") != "admin" and user.get("sale_point_id") != id:
        raise HTTPException(403, detail="Acesso negado a recursos de outro ponto de venda")
    return user