from model import Product, RetiradaProduto
from products.product_schema import ProductResponseDTO, ItemRetiradaDTO, RetiradaResponseDTO, ItemsRetiradaResponseDTO
from products.ProductExceptions import ExistingProductException, ProductNotFound
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
    sucessos = []
    erros = []
    
    for item in produtos:
        try:
            product = session.query(Product).filter(Product.id == item.product_id).first()
            
            if not product:
                erros.append({
                    "product_id": item.product_id,
                    "erro": "Produto não encontrado"
                })
                continue
            
            if item.unidade == 'amount':
                if product.amount < item.quantidade:
                    erros.append({
                        "product_id": item.product_id,
                        "nome": product.name,
                        "erro": f"Estoque insuficiente: disponível {product.amount} unidades"
                    })
                    continue
                product.amount -= item.quantidade
                
            elif item.unidade == 'kg':
                if product.kg < item.quantidade:
                    erros.append({
                        "product_id": item.product_id,
                        "nome": product.name,
                        "erro": f"Estoque insuficiente: disponível {product.kg} kg"
                    })
                    continue
                product.kg -= item.quantidade
                
            elif item.unidade == 'liters':
                if product.liters < item.quantidade:
                    erros.append({
                        "product_id": item.product_id,
                        "nome": product.name,
                        "erro": f"Estoque insuficiente: disponível {product.liters} litros"
                    })
                    continue
                product.liters -= item.quantidade
            
            else:
                erros.append({
                    "product_id": item.product_id,
                    "erro": f"Unidade inválida: {item.unidade}"
                })
                continue
            
            has_retirada = session.query(RetiradaProduto).filter(RetiradaProduto.product_id == item.product_id, RetiradaProduto.sale_point_id == sale_point_id, func.date(RetiradaProduto.data) == date.today()).first()
            if(has_retirada):
                has_retirada.taken_quantity += item.quantidade
            else:
                retirada = RetiradaProduto(
                    sale_point_id=sale_point_id,
                    product_id=item.product_id,
                    taken_quantity=item.quantidade,
                    unidade=item.unidade,
                    observacao=observacao
                )
                session.add(retirada)
            session.commit()
            sucessos.append({
                "product_id": item.product_id,
                "nome": product.name,
                "quantidade": item.quantidade,
                "unidade": item.unidade,
                "estoque_restante": get_estoque_restante(product, item.unidade)
            })
            
        except Exception as e:
            erros.append({
                "product_id": item.product_id,
                "erro": f"Erro inesperado: {str(e)}"
            })
    if sucessos:
        session.commit()
    
    return {
        "sucessos": sucessos,
        "erros": erros,
        "total_sucessos": len(sucessos),
        "total_erros": len(erros)
    }


def get_products_by_sale_point_service(sale_point_id, session, user):
    result = []
    id = sale_point_id if sale_point_id else user['sub']
    retiradas = session.query(RetiradaProduto).filter(
        RetiradaProduto.sale_point_id == id
    ).options(
        selectinload(RetiradaProduto.product)
    ).order_by(desc(RetiradaProduto.data)).all()
    #for retirada in retiradas:
        #result.append(retirada)
        
    for retirada in retiradas:
        result.append(ItemsRetiradaResponseDTO.from_orm(retirada))
        
    return result

def subtrair_estoque_service(session, sale_point_id: int, items: List[ItemRetiradaDTO]):
    try:
        sucessos = []
        for item in items:
            retirada = session.query(RetiradaProduto).filter(
                RetiradaProduto.product_id == item.product_id,
                RetiradaProduto.sale_point_id == sale_point_id,
                date.today() == func.date(RetiradaProduto.data)
            ).first()
            
            if not retirada:
                sucessos.append({"message": "retirada não encontrada"})
                return sucessos
            elif (retirada.taken_quantity - retirada.sold_quantity) < item.quantidade:
                sucessos.append({"message": "estoque insuficiente"})
                return sucessos
            
            product = session.get(Product, item.product_id)
            if product.amount is not None:
                product.amount += item.quantidade
            elif product.kg is not None:
                product.kg += item.quantidade
            elif product.liters is not None:
                product.liters += item.quantidade
            if item.quantidade == (retirada.sold_quantity - item.quantidade):
                retirada.status = True
            sucessos.append({
                "product_id": item.product_id,
                "nome": product.name,
                "quantidade": item.quantidade,
                "unidade": item.unidade,
                "estoque_restante": get_estoque_restante(product, item.unidade)
            })   
        session.commit()
        return sucessos
    except Exception as e:
        print(f"Erro: {e}")
        session.rollback()
        raise
    finally:
        session.close()

def get_estoque_restante(product, unidade: str):
    """
    Retorna a quantidade restante no estoque para uma determinada unidade
    """
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
            "estoque_restante": estoque_restante,  # Agora calculado corretamente
            "data_retirada": retirada.data.isoformat() if retirada.data else None,
            "observacao": retirada.observacao,
            "sale_point_id": retirada.sale_point_id
        })
    
    return result