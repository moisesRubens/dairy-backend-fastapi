from services.product_service import delete_product_service
from fastapi import HTTPException

def delete_product_controller(session, id):
    try:
        product_data = delete_product_service(session, id)
        return product_data
    except HTTPException as e:
        raise e(404, "Product not found")
    except Exception as e:
        raise e