from sqlalchemy.orm import Session
from model import RetiradaProduto, Product
from outbounds.outbound_exceptions import OutboundNotFound
from outbounds.outbound_schema import OutboundResponseDTO
from products.ProductExceptions import ProductNotFound, InsuficientProductsAmountException
from fastapi import HTTPException


async def update_quantity_service(session: Session, id: int, quantity: int,):
    try:
        outbound = session.get(RetiradaProduto, id)
        if not outbound:
            raise OutboundNotFound()
        
        product = session.get(Product, outbound.order.id)
        if not product:
            raise ProductNotFound()
        
        product_data = {}
        if product.amount:
            product_data.append({"quantity": product.amount}, {"unit_type": "amount"})
        elif product.kg:
            product_data.append({"quantity": product.amount}, {"unit_type": "amount"})
        elif product.liters:
            product_data.append({"quantity": product.amount}, {"unit_type": "amount"})
            
        if product_data['quantity'] < quantity:
            raise InsuficientProductsAmountException()
        
        if outbound.unidade != product_data['unit_type']:
            raise HTTPException(404, "Invalid inputs")
        
        outbound.quantidade = product_data['quantity']
        product.amount -= product_data['quantity']

        session.commit()        
        return OutboundResponseDTO.model_validate(outbound)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()