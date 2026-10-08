from exceptions.product_exceptions import BusinessConflict, ProductNotFound
from exceptions.sale_point_exceptions import SalePointNotFound
from exceptions.common_exceptions import InvalidCredentialsException
from exceptions.product_exceptions import ProductNotFound, BusinessConflict
from exceptions.sale_point_exceptions import SalePointNotFound
from database.model import Order, ItemsOrder, Product, SalePoints, OrderSalePoint, RetiradaProduto
from schemas.order_schema import OrderResponse, OrderRequestDTO, ItemOrderResponseDTO, OrderResponseDTO, OrderUpdateDTO
from exceptions.order_exceptions import AdminPermissionRequired, OrderNotFoundException
from services.product_service import validate_product
from exceptions.product_exceptions import InsuficientProductsAmountException
from datetime import datetime, date
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from services.idempotency import replay, remember
from services.authorization import require_admin
from database.money import money, subtotal

def create_order_service(order_data: OrderRequestDTO, sale_point_id: int, session):    
    try:
        with session.begin():
            request_key = f'{sale_point_id}:{order_data.client_request_id}' if order_data.client_request_id else None
            operation_key = f'order:{request_key}' if request_key else None
            payload = order_data.model_dump(exclude={'client_request_id'})
            cached = replay(session, operation_key, payload)
            if cached is not None:
                return OrderResponseDTO.model_validate(cached)
            if request_key:
                existing = session.query(Order).filter(Order.client_request_id == request_key).first()
                if existing:
                    return OrderResponseDTO.model_validate(existing)
            order = Order()
            order.client_request_id = request_key
            total_value = money(0)
            order.discount_value = money(0)
            order.total_value = 0
            order.description = order_data.description
            if order_data.status is not None:
                order.status = order_data.status
            order_status = order_data.order_status or ('pendente' if order_data.status is False else 'pago')
            order.status = order_status != 'pendente'
            if order_data.order_date is not None:
                order.order_date = datetime.combine(order_data.order_date, datetime.min.time())
            session.add(order)
            session.flush()

            sale_point = session.get(SalePoints, sale_point_id)

            if sale_point is None:
                raise SalePointNotFound()
            seen = set()
            for item in order_data.items:
                if item.product_id in seen:
                    raise ValueError("Duplicate product in order")
                seen.add(item.product_id)
                product = session.get(Product, item.product_id)
                if product is None:
                    raise ProductNotFound()
                sale_date = order_data.order_date or date.today()
                retirada = session.query(RetiradaProduto).filter(RetiradaProduto.sale_point_id==sale_point_id, RetiradaProduto.product_id==item.product_id, sale_date == func.date(RetiradaProduto.data), RetiradaProduto.status.is_(True)).first()
                if retirada is None:
                    raise BusinessConflict("No active outbound for product")
                if item.quantity is not None:
                    if retirada.unidade == "amount" and not item.quantity.is_integer():
                        raise ValueError("Amount must be an integer")
                    setattr(item, retirada.unidade, item.quantity)
                map = validate_item_order_request(item, retirada)
                if map["key"] != retirada.unidade:
                    raise ValueError("Quantity unit does not match outbound")
                remaining_quantity = retirada.remaining_quantity

                if remaining_quantity <= 0 or remaining_quantity < map['quantity']:
                    raise InsuficientProductsAmountException()
            
                match map['key']:
                    case 'amount':
                        retirada.sold_quantity += item.amount
                    case 'kg':
                        retirada.sold_quantity += item.kg
                    case 'liters':
                        retirada.sold_quantity += item.liters
            
                item_value = subtotal(product.price, map["quantity"])
                total_value += item_value
                retirada.total_value = money(retirada.total_value) + item_value
                retirada.remaining_quantity -= map['quantity']

                item_order = ItemsOrder(
                    order_id=order.id,
                    product_id=item.product_id,
                    product_name=product.name,
                    item_price=product.price,
                    amount=item.amount,
                    kg=item.kg,
                    liters=item.liters
                )
                session.add(item_order)
                session.flush()

            if order_status == 'desconto':
                if order_data.total_value is None or order_data.total_value > total_value:
                    raise ValueError('Discount order requires a final value up to the original total')
                order.discount_value = total_value - order_data.total_value
                total_value = order_data.total_value
            order.total_value = total_value
            order_sale_point = OrderSalePoint()
            order_sale_point.order_id = order.id
            order_sale_point.sale_point_id = sale_point.id
            session.add(order_sale_point)
            session.flush()
            session.refresh(order, ['order_sale_point'])
        
            order_response = OrderResponseDTO.model_validate(order)
            remember(session, operation_key, payload, order_response.model_dump(mode='json'))
            return order_response
    except IntegrityError:
        session.rollback()
        cached = replay(session, operation_key, payload)
        if cached is not None:
            return OrderResponseDTO.model_validate(cached)
        raise


from sqlalchemy import func, select
from datetime import datetime, timedelta

def get_all_orders_service(session, user, date=None, description=None, status=None):
    sale_point_orders = session.query(OrderSalePoint.order_id).filter(OrderSalePoint.sale_point_id == user['sub']).subquery()
    query = session.query(Order).filter(Order.id.in_(sale_point_orders))
    
    if status is not None:
        query = query.filter(Order.status == status)
    if description:
        query = query.filter(Order.description.ilike(f'%{description}%'))
    if date:
        filter_date = datetime.strptime(date, '%Y-%m-%d').date()
        start_of_day = datetime.combine(filter_date, datetime.min.time()).replace(
            tzinfo=ZoneInfo("America/Sao_Paulo")
        )
        end_of_day = datetime.combine(filter_date, datetime.max.time()).replace(
            tzinfo=ZoneInfo("America/Sao_Paulo")
        )
        query = query.filter(
            Order.order_date >= start_of_day,
            Order.order_date <= end_of_day
        )
    orders = query.all()
    result = []
    for order in orders:
        order_data = OrderResponseDTO.model_validate(order)
        result.append(order_data)
    return result


def _require_order_admin(session: Session, user):
    require_admin(session, user, 'Somente administradores podem excluir pedidos')


def delete_order(id: int, session: Session, user) -> OrderResponseDTO:
    with session.begin():
        _require_order_admin(session, user)
        order = session.get(Order, id)
        if order is None:
            raise OrderNotFoundException('Pedido não encontrado')
        order_data = OrderResponseDTO.model_validate(order)
        session.delete(order)
    return order_data


def delete_all_orders_service(session: Session, user) -> list[OrderResponseDTO]:
    with session.begin():
        _require_order_admin(session, user)
        orders = session.scalars(select(Order).order_by(Order.id)).all()
        result = [OrderResponseDTO.model_validate(order) for order in orders]
        for order in orders:
            session.delete(order)
    return result
        
def get_orders_by_sale_point_id_service(session, date, sale_point_id, since=None, include_pending=False, limit=200, offset=0):
    if session.get(SalePoints, sale_point_id) is None:
        raise SalePointNotFound()
    query = session.query(Order).join(OrderSalePoint).filter(OrderSalePoint.sale_point_id == sale_point_id)
    if date is not None:
        query = query.filter(func.date(Order.order_date) == date)
    if since is not None:
        from sqlalchemy import or_
        recent = func.date(Order.order_date) >= since
        query = query.filter(or_(recent, Order.status.is_(False)) if include_pending else recent)
    return [OrderResponseDTO.model_validate(order) for order in query.order_by(Order.id).offset(offset).limit(limit).all()]


def search_order(session, user, id) -> OrderResponseDTO:
    order = session.get(Order, id)

    if order is None:
        raise OrderNotFoundException("Pedido não encontrado")
    
    return OrderResponseDTO.model_validate(order)

def list_orders_service(session, date, status, description, page=1, size=20):
    filters = []
    if date is not None:
        filters.append(func.date(Order.order_date) == date)
    if status is not None:
        filters.append(Order.status == status)
    if description is not None:
        filters.append(Order.description.ilike(f"%{description}%"))
    orders = session.scalars(
        select(Order)
        .where(*filters)
        .order_by(Order.id)
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    return [OrderResponseDTO.model_validate(order) for order in orders]


def edit_order(session: Session, id: int, order_request: OrderUpdateDTO):
    with session.begin():
        order = session.get(Order, id)
        if order is None:
            raise OrderNotFoundException("Pedido não encontrado")
        for field, value in order_request.model_dump(exclude_unset=True).items():
            if field in ('order_status', 'total_value'):
                continue
            if field == "order_date":
                value = datetime.combine(value, datetime.min.time())
            setattr(order, field, value)
            if field == 'status':
                order.discount_value = money(0)
        if order_request.order_status is not None:
            original = sum((subtotal(item.item_price, item.amount or item.kg or item.liters or 0)
                           for item in order.item_order), money(0))
            if not order.item_order:
                original = order.total_value + (order.discount_value or 0)
            if order_request.order_status == 'desconto':
                final = order_request.total_value
                if final is None or final > original:
                    raise ValueError('Discount order requires a final value up to the original total')
                order.discount_value = original - final
                order.total_value = final
            else:
                order.discount_value = 0
                order.total_value = original
            order.status = order_request.order_status != 'pendente'
        session.flush()
        result = OrderResponseDTO.model_validate(order)

        return result


def validate_item_order_request(item_order_request, product):
    remaining_quantity = product.taken_quantity - product.sold_quantity
    if not remaining_quantity:
        raise InsuficientProductsAmountException()
    
    key = ''
    obj = 0
    if item_order_request.amount:
        obj = item_order_request.amount
        key = 'amount'
    if item_order_request.kg:
        obj = item_order_request.kg
        key = 'kg'
    if item_order_request.liters:
        obj = item_order_request.liters
        key = 'liters'

    return {"key": key,
            "quantity": obj}
    
