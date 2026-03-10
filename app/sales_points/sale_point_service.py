from fastapi import HTTPException, Depends
from model import SalePoints, Token, RetiradaProduto, Product
from sales_points.sale_point_schema import SalePointResponseDTO, SalePointRequestDTO
from pwdlib import PasswordHash
from fastapi.security import OAuth2PasswordRequestForm
from jwt import encode
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
from decouple import config
from sales_points.sale_point_exceptions import ExistingSalePointException, SalePointNotFound
from sales_points.sale_point_dependencies import oauth2_scheme
from typing import Annotated
from products.product_schema import RetirarProdutosRequestDTO, ItemsRetiradaResponseDTO
from products.product_service import get_unit_type_and_quantity_from_product
from products.ProductExceptions import InsuficientProductsAmountException, ProductNotFound
from sqlalchemy import func
from sqlalchemy.orm import Session

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

async def create_outbound_service(session: Session, id: int, outbound_request: RetirarProdutosRequestDTO):
    try:
        if not session.get(SalePoints, id):
            raise SalePointNotFound()
        result = []
        
        for product_outbound in outbound_request.produtos:
            product = session.get(Product, product_outbound.product_id)
            
            if not product:
                raise ProductNotFound()
            
            exists_outbound = session.query(RetiradaProduto).filter(date.today() == func.date(RetiradaProduto.data), RetiradaProduto.sale_point_id == id, RetiradaProduto.product_id == product_outbound.product_id).first()
            print(exists_outbound)
            if exists_outbound:
                continue
            product_data = get_unit_type_and_quantity_from_product(session, product)
            if product_outbound.unidade != product_data.get("unit_type"):
                raise HTTPException(404, "Dados inválidos")
            if product_outbound.quantidade > product_data.get("quantity"):
                raise InsuficientProductsAmountException()
            
            match product_data.get("unit_type"):
                case 'amount':
                    product.amount -= product_outbound.quantidade
                case 'kg':
                    product.kg -= product_outbound.quantidade
                case 'liters':
                    product.liters -= product_outbound.quantidade
            
            outbound = RetiradaProduto(
                        sale_point_id=id,
                        product_id=product_outbound.product_id,
                        taken_quantity=product_outbound.quantidade,
                        unidade=product_outbound.unidade,
                        observacao=outbound_request.observacao,
                        remaining_quantity = product_outbound.quantidade)
            session.add(outbound)
            session.flush()
            result.append(ItemsRetiradaResponseDTO.from_orm(outbound))
            
        session.commit()
        return result 
    except Exception as e:
        session.rollback()
        raise e
    finally: 
        session.close()
        
async def delete_outbounds_service(session: Session, id: int):
    try:
        result = []
        outbounds = session.query(RetiradaProduto).filter(RetiradaProduto.sale_point_id == id).all()
        
        if not outbounds:
            return result

        for outbound in outbounds:
            product = session.get(Product, outbound.product_id)
            if outbound.status:
                match outbound.unidade:
                    case 'amount':
                        product.amount += outbound.remaining_quantity
                    case 'kg':
                        product.kg += outbound.remaining_quantity
                    case 'liters':
                        product.liters += outbound.remaining_quantity
            result.append(ItemsRetiradaResponseDTO.from_orm(outbound))
            session.delete(outbound)
        
        session.commit()
        return result
    except Exception:
        session.rollback()
        raise 
    finally:
        session.close()
        
async def return_outbounds_service(session: Session, id: int):
    try:
        result = []
        outbounds = session.query(RetiradaProduto).filter(RetiradaProduto.sale_point_id == id, func.date(RetiradaProduto.data) == date.today(), RetiradaProduto.status == True).all()
        
        for outbound in outbounds:
            product = session.get(Product, outbound.product_id)
            match outbound.unidade:
                case 'amount':
                    product.amount += outbound.remaining_quantity
                case 'kg':
                    product.kg += outbound.remaining_quantity
                case 'liters':
                    product.liters += outbound.remaining_quantity
            result.append(ItemsRetiradaResponseDTO.from_orm(outbound))
            outbound.remaining_quantity = 0
            outbound.status = False
        
        session.commit()
        return result 
    except Exception: 
        session.rollback()
        raise
    finally: 
        session.close()