from sqlalchemy.orm import Session
from model import RetiradaProduto, Product
from outbounds.outbound_schema import OutboundResponseDTO
from products.ProductExceptions import ProductNotFound, InsuficientProductsAmountException
from fastapi import HTTPException
from outbounds.outbound_exceptions import OutboundNotFound


async def update_quantity_service(session: Session, id: int, quantity: int,):
    try:
        outbound = session.get(RetiradaProduto, id)
        if not outbound:
            raise OutboundNotFound()
        
        product = session.get(Product, outbound.product.id)
        if not product:
            raise ProductNotFound()
        
        product_data = {}
        if product.amount:
            product_data.update({"quantity": product.amount})
            product_data.update({"unit_type": "amount"})
        elif product.kg:
            product_data.update({"quantity": product.amount})
            product_data.update({"unit_type": "kg"})
        elif product.liters:
            product_data.update({"quantity": product.amount})
            product_data.update({"unit_type": "liters"})
            
        if product_data['quantity'] < quantity - outbound.remaining_quantity:
            raise InsuficientProductsAmountException()
        
        if outbound.unidade != product_data['unit_type']:
            raise HTTPException(404, "Invalid inputs")
        
        quantity_to_add = quantity - outbound.remaining_quantity
        
        outbound.taken_quantity += quantity_to_add
        outbound.remaining_quantity += quantity_to_add
        
        product.amount -= quantity_to_add
        session.commit()        
        return OutboundResponseDTO.model_validate(outbound)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()