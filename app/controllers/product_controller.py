from services.product_service import delete_product_service, create_product_service, get_all_products_service
from fastapi import HTTPException
from exceptions.ProductExceptions import ExistingProductException, ProductNotFound

def delete_product_controller(session, id):
    try:
        product_data = delete_product_service(session, id)
        return product_data
    except ProductNotFound as e:
        raise HTTPException(404, "Product not found")
    except Exception as e:
        raise e
    
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
