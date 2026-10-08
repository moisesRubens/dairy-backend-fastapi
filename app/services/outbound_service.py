from exceptions.product_exceptions import BusinessConflict, ProductNotFound
from exceptions.sale_point_exceptions import SalePointNotFound
from exceptions.common_exceptions import InvalidCredentialsException
from sqlalchemy.orm import Session
from database.model import RetiradaProduto, Product, SalePoints, Order, OrderSalePoint
from schemas.product_schema import ItemsRetiradaResponseDTO
from schemas.outbound_schema import OutboundResponseDTO, OutboundRequestDTO
from exceptions.product_exceptions import ProductNotFound, InsuficientProductsAmountException
from exceptions.outbound_exceptions import OutboundNotFound
from sqlalchemy import func, desc
from sqlalchemy.orm import selectinload


def get_outbound_service(session: Session, id: int):
    outbound = session.get(RetiradaProduto, id)
    if outbound is None:
        raise OutboundNotFound()
    return ItemsRetiradaResponseDTO.from_orm(outbound)


async def update_quantity_service(session: Session, id: int, quantity: float):
    return edit_outbound_service(session, id, OutboundRequestDTO(remaining_quantity=quantity))


def edit_outbound_service(session: Session, id: int, outbound_request: OutboundRequestDTO):
    with session.begin():
        outbound = session.query(RetiradaProduto).filter(RetiradaProduto.id == id).with_for_update().first()
        if outbound is None:
            raise OutboundNotFound()
        changes = outbound_request.model_dump(exclude_unset=True)
        quantity = changes.get("remaining_quantity")
        closing = changes.get("status") is False
        if not outbound.status and (quantity is not None or changes.get("status") is True):
            raise BusinessConflict("Outbound is closed")
        if closing and quantity not in (None, 0):
            raise ValueError("Closed outbound must have zero remaining quantity")
        if closing:
            quantity = 0
        if quantity is not None and outbound.status:
            product = session.query(Product).filter(Product.id == outbound.product_id).with_for_update().first()
            if product is None:
                raise ProductNotFound()
            if outbound.unidade not in ("amount", "kg", "liters"):
                raise ValueError("Invalid outbound unit")
            if outbound.unidade == "amount" and not float(quantity).is_integer():
                raise ValueError("Amount must be an integer")
            stock = getattr(product, outbound.unidade)
            if stock is None or stock < 0:
                raise ValueError("Incompatible stock unit")
            delta = quantity - outbound.remaining_quantity
            if delta > stock:
                raise InsuficientProductsAmountException()
            setattr(product, outbound.unidade, stock - delta)
            if not closing:
                outbound.taken_quantity = outbound.sold_quantity + quantity
            outbound.remaining_quantity = quantity
        if "observation" in changes:
            outbound.observacao = changes["observation"]
        if "status" in changes:
            outbound.status = changes["status"]
        session.flush()
        result = ItemsRetiradaResponseDTO.from_orm(outbound)
        return result


async def get_all_products_by_sale_point_service(session, date_param, status=False):
    result = []
    sales_query = session.query(OrderSalePoint.sale_point_id, func.sum(Order.total_value)).join(Order)
    if date_param is not None:
        sales_query = sales_query.filter(func.date(Order.order_date) == date_param)
    sales_totals = dict(sales_query.group_by(OrderSalePoint.sale_point_id).all())
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
            'sale_point_id': sale_point.id,
            'sales_total': round(sales_totals.get(sale_point.id, 0.0), 2),
            'sale_point_name': sale_point.name,
            'outbounds': outbound_items
        })
    
    return result
    
    
