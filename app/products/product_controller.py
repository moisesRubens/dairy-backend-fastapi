from products.product_service import delete_product_service, create_product_service, get_all_products_service, delete_all_products_service, get_products_by_sale_point_service, retirar_produtos_service, get_products_service, get_all_retiradas_service,return_products_to_storage_service, get_product_service, edit_product_service
from fastapi import HTTPException
from products.ProductExceptions import ExistingProductException, ProductNotFound
from products.product_schema import ProductRequestDTO
from typing import List
from sqlalchemy.orm import Session


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
    
async def get_product_controller(session: Session, id: int):
    return get_product_service(session, id)
    

async def edit_product_controller(session: Session, id: int, product_request: ProductRequestDTO):
    return edit_product_service(session, id, product_request)

    
from fastapi import HTTPException
from sqlalchemy.orm import Session

def retirar_produtos_controller(session: Session, sale_point_id: int, produtos: list, observacao: str = None):
    try:
        resultado = retirar_produtos_service(session, sale_point_id, produtos, observacao)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def get_products_by_sale_point_controller(sale_point_id, date, session: Session, user):
    try:
        id = sale_point_id if sale_point_id else user['sub']   
        products = get_products_by_sale_point_service(id, session, date, False)
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar produtos: {str(e)}")


def get_all_products_controller(session: Session):
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
    
def return_products_to_storage_controller(session, user, sale_point_id):
    try:
        return return_products_to_storage_service(session, user, sale_point_id)
    except Exception as e:
        do_rollback_session(session)
        raise HTTPException(status_code=500, detail=f"Erro ao subtrair estoque: {str(e)}")
    
def do_rollback_session(session):
    session.open()
    session.rollback()
    session.close()