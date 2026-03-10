from model import Product, RetiradaProduto
from products.product_schema import ProductResponseDTO, ItemRetiradaDTO, RetiradaResponseDTO, ItemsRetiradaResponseDTO
from products.ProductExceptions import ExistingProductException, ProductNotFound, InsuficientProductsAmountException
from sqlalchemy import func, desc
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from typing import List
from datetime import date

def get_all_products_service(session):
    result = []
    products = session.query(Product).all()
    if products:
        for product in products:
            product_data = ProductResponseDTO.model_validate(product)
            result.append(product_data)
    return result

def get_products_service(session, user):
    result = []
    products = session.query(Product).all()
    if products:
        for product in products:
            product_data = ProductResponseDTO.model_validate(product)
            result.append(product_data)
    return result

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
    finally:
        session.close()


def create_product_service(name, price, amount, kg, liters, session):
    if not validate_product:
        raise HTTPException(404, "Invalid inputs") 
    
    if session.query(Product).filter(func.upper(Product.name) == name.upper()).first():
        raise ExistingProductException()
    product = Product()
    product.name = name
    product.price = price
    product.amount = amount
    product.kg = kg
    product.liters = liters
    session.add(product)
    session.commit()
    
    return ProductResponseDTO.model_validate(product)

def validate_product(amount, kg, liters):
    return  not (kg and amount) or (kg and liters) or (amount and liters)

def retirar_produtos_service(session, sale_point_id: int, produtos: list, observacao: str = None):
    try:
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
                session.commit()
                sucessos.append(
                    ItemsRetiradaResponseDTO.from_orm(retirada)
                )
        return sucessos
    finally:
        session.close()


def get_products_by_sale_point_service(sale_point_id, session, date_param, status=False):
    result = []
    query = session.query(RetiradaProduto).filter(RetiradaProduto.sale_point_id == sale_point_id)
    
    if date_param is not None:
        query = query.filter(func.date(RetiradaProduto.data) == date_param)  
    retiradas = query.options(selectinload(RetiradaProduto.product)).order_by(desc(RetiradaProduto.data)).all()
    
    if status: 
        return retiradas 
    else:  
        for retirada in retiradas:
            result.append(ItemsRetiradaResponseDTO.from_orm(retirada))
        return result

def return_products_to_storage_service(session, user, sale_point_id):
    try:
        sucessos = []
        
        id = sale_point_id if sale_point_id else user['sub']
        current_date = date.today()  
        
        outbounds = get_products_by_sale_point_service(
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
    finally:
        session.close()
        

def get_estoque_restante(product, unidade: str):
    if unidade == 'amount':
        return product.amount
    elif unidade == 'kg':
        return product.kg
    elif unidade == 'liters':
        return product.liters
    return 0

def get_all_retiradas_service(session):
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