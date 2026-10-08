from exceptions.product_exceptions import BusinessConflict, ProductNotFound
from exceptions.sale_point_exceptions import SalePointNotFound
from exceptions.common_exceptions import InvalidCredentialsException
from database.model import Product, RetiradaProduto, SalePoints, ItemsOrder
from schemas.product_schema import ProductResponseDTO, ItemRetiradaDTO, RetiradaResponseDTO, ItemsRetiradaResponseDTO, ProductRequestDTO, ProductUpdateDTO
from exceptions.product_exceptions import ExistingProductException, ProductNotFound, InsuficientProductsAmountException
from sqlalchemy import func, desc
from sqlalchemy.orm import selectinload, Session
from typing import List
from datetime import date
from services.idempotency import replay, remember
from sqlalchemy.exc import IntegrityError
from services.authorization import require_admin

async def get_all_products_service(session, limit=None, offset=0):
    query = session.query(Product).order_by(Product.id).offset(offset)
    if limit is not None:
        query = query.limit(limit)
    products = query.all()
    return [ProductResponseDTO.model_validate(product) for product in products]

async def get_products_service(session, user):
    products = session.query(Product).all()
    return [ProductResponseDTO.model_validate(product) for product in products]

def delete_product_service(session, id, user):
    with session.begin():
        require_admin(session, user, 'Somente administradores podem excluir produtos')
        product = session.get(Product, id)
        if not product:
            raise ProductNotFound()
    
        product_data = ProductResponseDTO.model_validate(product)
        # Preserve historical item names, prices and quantities even on SQLite
        # connections where foreign key enforcement has not been enabled.
        session.query(ItemsOrder).filter(ItemsOrder.product_id == id).update(
            {ItemsOrder.product_id: None}, synchronize_session='fetch')
        session.delete(product)
        return product_data

def delete_all_products_service(session, user):
    with session.begin():
        require_admin(session, user, 'Somente administradores podem excluir produtos')
        products = session.query(Product).order_by(Product.id).all()
        result = [ProductResponseDTO.model_validate(product) for product in products]
        session.query(ItemsOrder).update({ItemsOrder.product_id: None}, synchronize_session='fetch')
        for product in products:
            session.delete(product)
        return result

def create_product_service(producst_list_request: list[ProductRequestDTO], session):
    try:
        with session.begin():
            products_added = []
            if not producst_list_request:
                raise ValueError("Supply at least one product")
            for data in producst_list_request:
                key = f'product:{data.client_request_id}' if data.client_request_id else None
                payload = data.model_dump(exclude={'client_request_id'})
                existing_response = replay(session, key, payload)
                if existing_response is not None:
                    products_added.append(ProductResponseDTO.model_validate(existing_response))
                    continue
                if session.query(Product).filter(func.upper(Product.name) == data.name.upper()).first():
                    raise ExistingProductException()
                product = Product(**payload)
                session.add(product)
                session.flush()
                products_added.append(product)
                remember(session, key, payload, ProductResponseDTO.model_validate(product).model_dump(mode='json'))
            result = [ProductResponseDTO.model_validate(p) for p in products_added]
            return result
    except IntegrityError:
        session.rollback()
        cached = [replay(session, f'product:{data.client_request_id}',
                         data.model_dump(exclude={'client_request_id'})) if data.client_request_id else None
                  for data in producst_list_request]
        if all(item is not None for item in cached):
            return [ProductResponseDTO.model_validate(item) for item in cached]
        raise


def validate_product(amount, kg, liters):
    return sum(value is not None and value != -1 for value in (amount, kg, liters)) == 1


async def retirar_produtos_service(session, sale_point_id: int, produtos: List[ItemRetiradaDTO], observacao: str = None):
    with session.begin():
        sucessos = []
    
        for item in produtos:
                product = session.query(Product).filter(Product.id == item.product_id).first()
            
                if not product:
                    raise InsuficientProductsAmountException("no product")
                if item.unidade == 'amount':
                    if product.amount < item.quantidade:
                        raise InsuficientProductsAmountException("amount")
                    product.amount -= item.quantidade
                elif item.unidade == 'kg':
                    if product.kg < item.quantidade:
                        raise InsuficientProductsAmountException("kg")
                    product.kg -= item.quantidade
                elif item.unidade == 'liters':
                    if product.liters < item.quantidade:
                        raise InsuficientProductsAmountException("liters")
                    product.liters -= item.quantidade
                else:
                    raise ValueError("invalid inputs")
                retirada = session.query(RetiradaProduto).filter(RetiradaProduto.product_id == item.product_id, RetiradaProduto.sale_point_id == sale_point_id, func.date(RetiradaProduto.data) == date.today()).first()
                if(retirada):
                    if retirada.status:
                        retirada.taken_quantity += item.quantidade
                        retirada.remaining_quantity = retirada.taken_quantity - retirada.sold_quantity
                    else:
                        retirada.taken_quantity = item.quantidade if item.quantidade>retirada.taken_quantity else retirada.taken_quantity
                        retirada.remaining_quantity = item.quantidade
                        retirada.status = True
                else:
                    new_retirada = RetiradaProduto(
                        sale_point_id=sale_point_id,
                        product_id=item.product_id,
                        taken_quantity=item.quantidade,
                        unidade=item.unidade,
                        observacao=observacao,
                        remaining_quantity = item.quantidade
                    )
                    session.add(new_retirada)
                    retirada = new_retirada
            
                session.flush() # Garante que o ID e campos do banco existam antes de criar o DTO
                sucessos.append(ItemsRetiradaResponseDTO.from_orm(retirada))
            
        return sucessos

async def get_products_by_sale_point_service(sale_point_id, session, date_param, status=False, since=None, include_open=False, limit=None, offset=0):
    result = []
    query = session.query(RetiradaProduto).filter(RetiradaProduto.sale_point_id == sale_point_id)
    
    if date_param is not None:
        query = query.filter(func.date(RetiradaProduto.data) == date_param)  
    if since is not None:
        from sqlalchemy import or_
        recent = func.date(RetiradaProduto.data) >= since
        query = query.filter(or_(recent, RetiradaProduto.status.is_(True)) if include_open else recent)
    query = query.options(selectinload(RetiradaProduto.product)).order_by(RetiradaProduto.id).offset(offset)
    if limit is not None:
        query = query.limit(limit)
    retiradas = query.all()
    
    sale_point = session.get(SalePoints, sale_point_id)
    if sale_point is None:
        raise SalePointNotFound("Sale point not found")

    if status: 
        return retiradas 
    else:  
        for retirada in retiradas:
            result.append(ItemsRetiradaResponseDTO.from_orm(retirada))
        return {
            'sale_point_name': sale_point.name,
            'outbounds': result
        }

async def return_products_to_storage_service(session, user, sale_point_id):
    with session.begin():
        sucessos = []
        
        id = sale_point_id if sale_point_id else user['sub']
        current_date = date.today()  
        
        outbounds = await get_products_by_sale_point_service(
            id, 
            session, 
            current_date, 
            True
        )
        
        for outbound in outbounds:
            product = session.get(Product, outbound.product_id)  
            
            if not product:
                continue
            remaining_quantity = outbound.remaining_quantity 
            
            if product.amount is not None:
                product.amount += remaining_quantity
            if product.kg is not None:
                product.kg += remaining_quantity
            if product.liters is not None:
                product.liters += remaining_quantity
            
            outbound.status = False
            outbound.remaining_quantity = 0
            outbound_response = ItemsRetiradaResponseDTO.from_orm(outbound)
            sucessos.append(outbound_response)
        return sucessos
        

def get_estoque_restante(product, unidade: str):
    if unidade == 'amount':
        return product.amount
    elif unidade == 'kg':
        return product.kg
    elif unidade == 'liters':
        return product.liters
    return 0

async def get_all_retiradas_service(session):
    retiradas = session.query(RetiradaProduto).order_by(
        RetiradaProduto.data.desc()
    ).all()
    
    result = []
    for retirada in retiradas:
        product = session.query(Product).get(retirada.product_id)
        
        # Calcula o estoque restante baseado no produto e na unidade da retirada
        estoque_restante = 0
        if product:
            if retirada.unidade == 'amount':
                estoque_restante = product.amount or 0
            elif retirada.unidade == 'kg':
                estoque_restante = product.kg or 0
            elif retirada.unidade == 'liters':
                estoque_restante = product.liters or 0
        
        result.append({
            "id": retirada.id,
            "product_id": retirada.product_id,
            "nome": product.name if product else "Produto não encontrado",
            "quantidade": retirada.taken_quantity,
            "unidade": retirada.unidade,
            "estoque_restante": estoque_restante,  
            "data_retirada": retirada.data.isoformat() if retirada.data else None,
            "observacao": retirada.observacao,
            "sale_point_id": retirada.sale_point_id
        })
    
    return result

def get_unit_type_and_quantity_from_product(session, product):
    units = (
        ("amount", product.amount),
        ("kg", product.kg),
        ("liters", product.liters),
    )

    for unit_type, quantity in units:
        if quantity is not None and quantity != -1:
            return {"unit_type": unit_type, "quantity": quantity}

    return {"unit_type": None, "quantity": None}

def get_product_service(session: Session, id: int):
    product = session.get(Product, id)
    if product is None:
        raise ProductNotFound()
    return ProductResponseDTO.model_validate(product)
        

def edit_product_service(session: Session, id: int, product_request: ProductUpdateDTO):
    with session.begin():
        product = session.get(Product, id)
        if product is None:
            raise ProductNotFound()
        changes = product_request.model_dump(exclude_unset=True)
        if "name" in changes and session.query(Product).filter(
            func.upper(Product.name) == changes["name"].upper(), Product.id != id
        ).first():
            raise ExistingProductException()
        units = {key: changes.get(key, getattr(product, key)) for key in ("amount", "kg", "liters")}
        if not validate_product(**units):
            raise ValueError("Supply exactly one stock unit")
        for field, value in changes.items():
            setattr(product, field, value)
        session.flush()
        result = ProductResponseDTO.model_validate(product)
        return result
