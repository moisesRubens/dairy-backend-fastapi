from products.product_service import delete_product_service, create_product_service, get_all_products_service, delete_all_products_service, get_products_by_sale_point_service, retirar_produtos_service, get_products_service, get_all_retiradas_service,subtrair_estoque_service
from fastapi import HTTPException
from products.ProductExceptions import ExistingProductException, ProductNotFound
from typing import List
from products.product_schema import ItemRetiradaDTO

def delete_product_controller(session, id):
    try:
        product_data = delete_product_service(session, id)
        return product_data
    except ProductNotFound as e:
        raise HTTPException(404, "Product not found")
    except Exception as e:
        raise e
    
def delete_all_products_controller(session):
    try: 
        delete_all_products_service(session)
    except Exception as e:
        raise HTTPException(500, detail=str(e))
    
def create_product_controller(name, price, amount, kg, liters, session):
    try:
        product_data = create_product_service(name, price, amount, kg, liters, session)
        return product_data
    except ExistingProductException as e:
        raise HTTPException(409, detail=str(e)) 
    
def get_all_products_controller(session):
    try:
        products_data = get_all_products_service(session)
        return products_data
    except Exception as e:
        raise HTTPException(200, detail=str(e))
    
def get_products_controller(session, user):
    try:
        get_products_service(session, user)
    except Exception as e: 
        raise e
    
from fastapi import HTTPException
from sqlalchemy.orm import Session

def retirar_produtos_controller(session: Session, sale_point_id: int, produtos: list, observacao: str = None):
    """
    Controlador para retirar produtos do estoque
    """
    try:
        # Chama o service para processar a retirada
        resultado = retirar_produtos_service(session, sale_point_id, produtos, observacao)
        
        return {
            "sucesso": True,
            "mensagem": f"{len(resultado['sucessos'])} produtos retirados com sucesso",
            "detalhes": resultado
        }
        
    except ValueError as e:
        # Erros de validação (estoque insuficiente, produto não encontrado)
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        # Erros inesperados
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar retirada: {str(e)}")


def get_products_by_sale_point_controller(sale_point_id, session: Session, user):
    try:
        products = get_products_by_sale_point_service(sale_point_id, session, user)
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar produtos: {str(e)}")


def get_all_products_controller(session: Session):
    """
    Controlador para buscar todos os produtos (estoque total)
    """
    try:
        products = get_all_products_service(session)
        return products
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar produtos: {str(e)}")
    
def get_all_retiradas_controller(session: Session):
    try:
        retiradas = get_all_retiradas_service(session)
        return retiradas
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar retiradas: {str(e)}")
    
def subtrair_estoque_controller(session, sale_point_id: int, items: List[ItemRetiradaDTO]):
    try:
        resultado = subtrair_estoque_service(session, sale_point_id, items)
        return resultado
        
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao subtrair estoque: {str(e)}")