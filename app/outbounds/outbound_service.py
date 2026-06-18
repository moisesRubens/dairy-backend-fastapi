from sqlalchemy.orm import Session
from model import RetiradaProduto, Product, SalePoints
from products.product_schema import ItemsRetiradaResponseDTO
from outbounds.outbound_schema import OutboundResponseDTO, OutboundRequestDTO
from products.ProductExceptions import ProductNotFound, InsuficientProductsAmountException
from fastapi import HTTPException
from outbounds.outbound_exceptions import OutboundNotFound
from sqlalchemy import func, desc
from sqlalchemy.orm import selectinload


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
        
def edit_outbound_service(session: Session, id: int, outbound_request: OutboundRequestDTO):
    try:
        outbound = session.get(RetiradaProduto, id)
        
        if outbound_request.name:
            outbound.name = outbound_request.name
        if outbound_request.status is not None:
            outbound.status = outbound_request.status 
        if outbound_request.date:
            outbound.data = outbound_request.date
        if outbound_request.unit_type:
            outbound.unidade = outbound_request.unit_type
        if outbound_request.taken_quantity:
            outbound.sold_quantity = outbound_request.sold_quantity
        if outbound_request.remaining_quantity:
            outbound.remaining_quantity = outbound_request.remaining_quantity
        if outbound_request.total_value_item:
            outbound.total_value = outbound_request.total_value_item
        if outbound_request.observation:
            outbound.observacao = outbound_request.observation
        
        session.commit()
        return OutboundResponseDTO.model_validate(outbound)
    except Exception:
        session.rollback()
        raise 
    finally:
        session.close()


async def get_all_products_by_sale_point_service(session, date_param, status=False):
    result = []
    sale_points = session.query(SalePoints).all()
    
    for sale_point in sale_points:
        query = session.query(RetiradaProduto).filter(RetiradaProduto.sale_point_id == sale_point.id)
        
        if date_param is not None:
            query = query.filter(func.date(RetiradaProduto.data) == date_param)
        
        retiradas = query.options(selectinload(RetiradaProduto.product)).order_by(desc(RetiradaProduto.data)).all()
        
        outbound_items = []
        for retirada in retiradas:
            outbound_items.append(ItemsRetiradaResponseDTO.from_orm(retirada))
        
        result.append({
            'sale_point_name': sale_point.name,
            'outbounds': outbound_items
        })
    
    return result
    
    