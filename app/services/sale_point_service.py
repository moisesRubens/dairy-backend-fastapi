from exceptions.product_exceptions import BusinessConflict, ProductNotFound
from exceptions.sale_point_exceptions import SalePointNotFound
from exceptions.common_exceptions import InvalidCredentialsException
from database.model import SalePoints, Token, RetiradaProduto, Product, OrderSalePoint, Order
from schemas.sale_point_schema import SalePointResponseDTO, SalePointRequestDTO, SalePointUpdateDTO, OrderSalePointResponseDTO
from pwdlib import PasswordHash
from fastapi.security import OAuth2PasswordRequestForm
from jwt import encode
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
from decouple import config
from exceptions.sale_point_exceptions import ExistingSalePointException, SalePointNotFound
from dependencies.sale_point_dependencies import oauth2_scheme
from typing import Annotated
from schemas.product_schema import RetirarProdutosRequestDTO, ItemsRetiradaResponseDTO, ProductResponseDTO
from services.product_service import get_unit_type_and_quantity_from_product
from exceptions.product_exceptions import InsuficientProductsAmountException, ProductNotFound
from schemas.order_schema import OrderResponseDTO
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload
from schemas.outbound_schema import OutboundResponseDTOTest
from services.authorization import require_admin
from exceptions.common_exceptions import PermissionDenied


pwd_context = PasswordHash.recommended()

async def create_sale_point_service(sale_point_request: SalePointRequestDTO, session):
    with session.begin():
        sale_point = session.query(SalePoints).filter(func.upper(SalePoints.name) == sale_point_request.name.upper()).first()
        if(sale_point):
            raise ExistingSalePointException()
    
        sale_point = SalePoints()
        hashed_pw = pwd_context.hash(sale_point_request.password)
        sale_point.password = hashed_pw
        sale_point.name = sale_point_request.name
        sale_point.email = sale_point_request.email
        sale_point.level = 0
        session.add(sale_point)
        session.flush()
        sale_point_response = SalePointResponseDTO.model_validate(sale_point)
        return sale_point_response


async def edit_sale_point_service(id: int, sale_point_request: SalePointUpdateDTO, session, user):
    with session.begin():
        actor_id = int(user['sub'])
        actor = session.get(SalePoints, actor_id)
        is_admin = actor is not None and actor.level == 1
        if 'level' in sale_point_request.model_fields_set and not is_admin:
            raise PermissionDenied('Somente administradores podem alterar permissoes')
        if id != actor_id and not is_admin:
            raise PermissionDenied('Sem permissao para editar outro perfil')
        sale_point = session.get(SalePoints, id)
        if not sale_point:
            raise SalePointNotFound()

        changes = sale_point_request.model_dump(exclude_unset=True)
        if "name" in changes:
            duplicate = session.query(SalePoints).filter(
                func.upper(SalePoints.name) == changes["name"].upper(),
                SalePoints.id != id,
            ).first()
            if duplicate:
                raise ExistingSalePointException()
        if "password" in changes:
            changes["password"] = pwd_context.hash(changes["password"])
        for field, value in changes.items():
            setattr(sale_point, field, value)

        session.flush()
        result = SalePointResponseDTO.model_validate(sale_point)
        return result


def login_service(form_data: OAuth2PasswordRequestForm, session):
    SECRET_KEY = config('SECRET_KEY')
    EXPIRE_TOKEN = int(config('EXPIRE_TIME_TOKEN'))
    ALGORITHM = config('ALGORITHM')

    sale_point = session.query(SalePoints).filter(SalePoints.name == form_data.username).first()
    if not sale_point:
        raise SalePointNotFound()
    if not pwd_context.verify(form_data.password, sale_point.password):
        raise InvalidCredentialsException("invalid credentials")
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

def delete_all_sales_points_service(session, user):
    with session.begin():
        require_admin(session, user, 'Somente administradores podem excluir pontos de venda')
        sale_points = session.query(SalePoints).order_by(SalePoints.id).all()
        result = [SalePointResponseDTO.model_validate(sale_point) for sale_point in sale_points]
        for sale_point in sale_points:
            session.delete(sale_point)
        return result


async def logout_service(token, session):
    with session.begin():
        revoked_token = Token()
        revoked_token.id = token
        session.add(revoked_token)
        return 'Logout successful'

async def get_sale_point_service(id: int, session):
    sale_point = session.query(SalePoints).filter(SalePoints.id == id).first()
    if not sale_point:
        raise SalePointNotFound()
    
    return SalePointResponseDTO.model_validate(sale_point)


async def delete_sale_point_service(id: int, session, user):
    with session.begin():
        require_admin(session, user, 'Somente administradores podem excluir pontos de venda')
        sale_point = session.get(SalePoints, id)
        if not sale_point:
            raise SalePointNotFound()
        sale_point_response = SalePointResponseDTO.model_validate(sale_point)
        session.delete(sale_point)
        return sale_point_response

async def create_outbound_service(session: Session, id: int, outbound_request: RetirarProdutosRequestDTO):
    from services.idempotency import replay, remember
    from sqlalchemy.exc import IntegrityError
    key = f'outbound:{id}:{outbound_request.client_request_id}' if outbound_request.client_request_id else None
    payload = outbound_request.model_dump(exclude={'client_request_id'})
    try:
        with session.begin():
            cached = replay(session, key, payload)
            if cached is not None:
                return [ItemsRetiradaResponseDTO.model_validate(item) for item in cached]
            if session.get(SalePoints, id) is None:
                raise SalePointNotFound()
            result = []
            seen = set()
            for item in outbound_request.produtos:
                if item.product_id in seen:
                    raise ValueError("Duplicate product in outbound")
                seen.add(item.product_id)
                product = session.query(Product).filter(Product.id == item.product_id).with_for_update().first()
                if product is None:
                    raise ProductNotFound()
                unit = get_unit_type_and_quantity_from_product(session, product)
                if item.unidade != unit["unit_type"]:
                    raise ValueError("Quantity unit does not match product")
                if item.unidade == "amount" and not item.quantidade.is_integer():
                    raise ValueError("Amount must be an integer")
                if item.quantidade > unit["quantity"]:
                    raise InsuficientProductsAmountException()
                outbound = session.query(RetiradaProduto).filter(
                    RetiradaProduto.sale_point_id == id,
                    RetiradaProduto.product_id == item.product_id,
                    func.date(RetiradaProduto.data) == (outbound_request.outbound_date or date.today()),
                    RetiradaProduto.status.is_(True),
                ).with_for_update().first()
                if outbound is None:
                    outbound = RetiradaProduto(sale_point_id=id, product_id=item.product_id,
                        taken_quantity=item.quantidade, remaining_quantity=item.quantidade,
                        unidade=item.unidade, observacao=outbound_request.observacao)
                    if outbound_request.outbound_date is not None:
                        outbound.data = datetime.combine(outbound_request.outbound_date, datetime.min.time())
                    session.add(outbound)
                else:
                    outbound.taken_quantity += item.quantidade
                    outbound.remaining_quantity += item.quantidade
                setattr(product, item.unidade, unit["quantity"] - item.quantidade)
                session.flush()
                result.append(ItemsRetiradaResponseDTO.from_orm(outbound))
            remember(session, key, payload, [item.model_dump(mode='json', by_alias=True) for item in result])
            return result
    except IntegrityError:
        session.rollback()
        cached = replay(session, key, payload)
        if cached is not None:
            return [ItemsRetiradaResponseDTO.model_validate(item) for item in cached]
        raise


async def delete_outbounds_service(session: Session, id: int, user, before=None):
    # DELETE encerra a sessao sem excluir o historico.
    return await return_outbounds_service(session, id, before, admin_user=user)


async def return_outbounds_service(session: Session, id: int, before=None, admin_user=None):
    with session.begin():
        if admin_user is not None:
            require_admin(session, admin_user, 'Somente administradores podem encerrar retiradas')
        sale_point = session.query(SalePoints).filter(
            SalePoints.id == id
        ).with_for_update().first()
        if sale_point is None:
            raise SalePointNotFound("Ponto de venda nao encontrado")

        query = session.query(RetiradaProduto).filter(
            RetiradaProduto.sale_point_id == id,
            RetiradaProduto.status.is_(True),
        )
        if before is not None:
            # Os registros existentes usam hora local sem timezone no SQLite.
            if before.tzinfo is None:
                raise ValueError("O limite deve incluir o fuso horario")
            cutoff = before.astimezone(ZoneInfo("America/Sao_Paulo")).replace(tzinfo=None)
            query = query.filter(RetiradaProduto.data <= cutoff)
        outbounds = query.order_by(
            RetiradaProduto.product_id, RetiradaProduto.id
        ).with_for_update().all()

        result = []
        for outbound in outbounds:
            product = session.query(Product).filter(
                Product.id == outbound.product_id
            ).with_for_update().first()
            if product is None:
                raise ProductNotFound("Produto nao encontrado")
            if outbound.unidade not in ("amount", "kg", "liters"):
                raise ValueError("Unidade invalida")
            remaining = outbound.remaining_quantity or 0
            if remaining < 0:
                raise ValueError("Saldo da retirada invalido")
            stock = getattr(product, outbound.unidade)
            if stock is None:
                raise ValueError("Unidade incompat?vel com o estoque")
            setattr(product, outbound.unidade, stock + remaining)
            outbound.remaining_quantity = 0
            outbound.status = False
            result.append(ItemsRetiradaResponseDTO.from_orm(outbound))

        return result

async def delete_orders_service(session: Session, id: int, user):
    with session.begin():
        require_admin(session, user, 'Somente administradores podem excluir pedidos')
        if session.get(SalePoints, id) is None:
            raise SalePointNotFound()
        result = []
        query = session.query(OrderSalePoint).filter(OrderSalePoint.sale_point_id == id)
        order_sale_point_ralations = query.options(selectinload(OrderSalePoint.order)).all()
        orders = [osp.order for osp in order_sale_point_ralations]
            
        result = OrderSalePointResponseDTO(
            sale_point_id=id,
            orders=[OrderResponseDTO.from_orm(order) for order in orders]
        )
        for order in orders:
            session.delete(order)
        return result
