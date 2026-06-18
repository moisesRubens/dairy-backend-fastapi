from model import Product, RetiradaProduto, SalePoints
from products.product_schema import ProductResponseDTO, ItemRetiradaDTO, RetiradaResponseDTO, ItemsRetiradaResponseDTO, ProductRequestDTO
from products.ProductExceptions import ExistingProductException, ProductNotFound, InsuficientProductsAmountException
from sqlalchemy import func, desc
from sqlalchemy.orm import selectinload, Session
from fastapi import HTTPException
from typing import List
from datetime import date

async def get_all_products_service(session):
    products = session.query(Product).all()
    return [ProductResponseDTO.model_validate(product) for product in products]

async def get_products_service(session, user):
    products = session.query(Product).all()
    return [ProductResponseDTO.model_validate(product) for product in products]

def delete_product_service(session, id):
    product = session.get(Product, id)
    if not product:
        raise ProductNotFound()
    
    product_data = ProductResponseDTO.model_validate(product)
    session.delete(product)
    session.commit() 
    return product_data

def delete_all_products_service(session):
    try:
        session.query(Product).delete(synchronize_session="fetch")
        session.commit()
    except Exception as e:
        session.rollback()
        raise e

def create_product_service(producst_list_request: list[ProductRequestDTO], session):
    products_added = []
    
    for data in producst_list_request:
        if not validate_product(data.amount, data.kg, data.liters):
            raise HTTPException(400, f"Invalid units for product {data.name}. Select only one: amount, kg or liters.")

        if session.query(Product).filter(func.upper(Product.name) == data.name.upper()).first():
            raise ExistingProductException()

        product = Product()
        product.name = data.name
        product.price = data.price
        product.amount = data.amount
        product.kg = data.kg
        product.liters = data.liters
        
        session.add(product)
        products_added.append(product)
        
    session.commit()
    return [ProductResponseDTO.model_validate(p) for p in products_added]

def validate_product(amount, kg, liters):
    return  not (kg and amount) or (kg and liters) or (amount and liters)

async def retirar_produtos_service(session, sale_point_id: int, produtos: List[ItemRetiradaDTO], observacao: str = None):
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
                raise HTTPException(404, "invalid inputs")
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
            
    session.commit()
    return sucessos

async def get_products_by_sale_point_service(sale_point_id, session, date_param, status=False):
    result = []
    query = session.query(RetiradaProduto).filter(RetiradaProduto.sale_point_id == sale_point_id)
    
    if date_param is not None:
        query = query.filter(func.date(RetiradaProduto.data) == date_param)  
    retiradas = query.options(selectinload(RetiradaProduto.product)).order_by(desc(RetiradaProduto.data)).all()
    
    sale_point = session.get(SalePoints, sale_point_id)

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
    try:
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
        session.commit()
        return sucessos
    except Exception as e:
        session.rollback()
        raise e
        

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
    result = {"unit_type": None,
              "quantity": None}
    
    if product.amount != -1:
        result["unit_type"] = "amount"
        result["quantity"] = product.amount
    elif product.kg != -1:
        result["unit_type"] = "kg"
        result["quantity"] = product.kg
    elif product.liters != -1:
        result["unit_type"] = "liters"
        result["quantity"] = product.liters
    
    return result

def get_product_service(session: Session, id: int):
    try:
        product = session.get(Product, id)
        if product:
            return ProductResponseDTO.model_validate(product)
        raise ProductNotFound()
    except Exception:
        session.rollback()
        raise 
        

def edit_product_service(session: Session, id: int, product_request: ProductRequestDTO):
    try:
        product = session.get(Product, id)
        if not product:
            raise ProductNotFound()
        
        if product_request.name:
            product.name = product_request.name 
        if product_request.price:
            product.price = product_request.price 
        if product_request.amount:
            product.amount = product_request.amount 
        if product_request.kg:
            product.kg = product_request.kg 
        if product_request.liters:
            product.liters = product_request.liters 
            
        session.commit()
        return ProductResponseDTO.model_validate(product)
        
    except Exception:
        session.rollback()
        raise 