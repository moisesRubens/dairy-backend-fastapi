from model import Product, RetiradaProduto
from products.product_schema import ProductResponseDTO, ItemRetiradaDTO
from products.ProductExceptions import ExistingProductException, ProductNotFound
from sqlalchemy import func
from fastapi import HTTPException
from typing import List

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
            # Busca o produto
            product = session.query(Product).filter(Product.id == item.product_id).first()
            
            if not product:
                erros.append({
                    "product_id": item.product_id,
                    "erro": "Produto não encontrado"
                })
                continue
            
            # Valida e processa a retirada baseado na unidade
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
            
            # Registra a retirada na tabela de log
            retirada = RetiradaProduto(
                sale_point_id=sale_point_id,
                product_id=item.product_id,
                quantidade=item.quantidade,
                unidade=item.unidade,
                observacao=observacao
            )
            session.add(retirada)
            
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
    
    # Se houve pelo menos um sucesso, faz commit
    if sucessos:
        session.commit()
    
    return {
        "sucessos": sucessos,
        "erros": erros,
        "total_sucessos": len(sucessos),
        "total_erros": len(erros)
    }


def get_products_by_sale_point_service(session, user):
    # Busca todas as retiradas do ponto de venda
    retiradas = session.query(RetiradaProduto).filter(
        RetiradaProduto.sale_point_id == user['sub']
    ).order_by(RetiradaProduto.data.desc()).all()
    
    # Dicionário para agrupar por produto
    produtos_agrupados = {}
    
    for retirada in retiradas:
        product = session.query(Product).get(retirada.product_id)
        if product:
            # Chave única: product_id + unidade (para não misturar kg com units)
            chave = f"{product.id}_{retirada.unidade}"
            
            if chave not in produtos_agrupados:
                # Primeira vez que vê este produto
                product_data = ProductResponseDTO.model_validate(product)
                product_dict = product_data.dict()
                product_dict.update({
                    "quantidade_retirada": retirada.quantidade,
                    "unidade_retirada": retirada.unidade,
                    "data_retirada": retirada.data.isoformat(),  # Pega a data mais recente
                    "observacao": retirada.observacao,
                    "sale_point_id": retirada.sale_point_id,
                    "total_retiradas": 1  # Contador de quantas vezes retirou
                })
                produtos_agrupados[chave] = product_dict
            else:
                # Já existe, soma a quantidade
                produtos_agrupados[chave]["quantidade_retirada"] += retirada.quantidade
                produtos_agrupados[chave]["total_retiradas"] += 1
                # Mantém a data mais recente
                if retirada.data.isoformat() > produtos_agrupados[chave]["data_retirada"]:
                    produtos_agrupados[chave]["data_retirada"] = retirada.data.isoformat()
    
    # Converte o dicionário para lista e ordena por data (mais recente primeiro)
    result = list(produtos_agrupados.values())
    result.sort(key=lambda x: x["data_retirada"], reverse=True)
    
    return result

def subtrair_estoque_service(session, sale_point_id: int, items: List[ItemRetiradaDTO]):
    sucessos = []
    erros = []
    
    for item in items:
        try:
            # Busca o produto - item é um objeto ItemRetiradaDTO, use item.product_id
            product = session.query(Product).filter(Product.id == item.product_id).first()
            
            if not product:
                erros.append({
                    "product_id": item.product_id,
                    "erro": "Produto não encontrado"
                })
                continue
            
            # Subtrai baseado na unidade
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
            
            # Registra a retirada
            retirada = RetiradaProduto(
                sale_point_id=sale_point_id,
                product_id=item.product_id,
                quantidade=item.quantidade,
                unidade=item.unidade,
                observacao="Subtraído por pedido"
            )
            session.add(retirada)
            
            sucessos.append({
                "product_id": item.product_id,
                "nome": product.name,
                "quantidade": item.quantidade,
                "unidade": item.unidade,
                "estoque_restante": get_estoque_restante(product, item.unidade)
            })
            
        except Exception as e:
            erros.append({
                "product_id": item.product_id if hasattr(item, 'product_id') else 'unknown',
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

# Adicione esta função auxiliar no product_service.py
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
            "quantidade": retirada.quantidade,
            "unidade": retirada.unidade,
            "estoque_restante": estoque_restante,  # Agora calculado corretamente
            "data_retirada": retirada.data.isoformat() if retirada.data else None,
            "observacao": retirada.observacao,
            "sale_point_id": retirada.sale_point_id
        })
    
    return result