from model import Order, ItemsOrder, Product, SalePoints, OrderSalePoint, RetiradaProduto
from orders.order_schema import OrderResponse, OrderRequestDTO, ItemOrderResponseDTO
from fastapi import HTTPException
from products.product_service import validate_product
from products.ProductExceptions import InsuficientProductsAmountException
from datetime import datetime, date
from zoneinfo import ZoneInfo

def create_order_service(order_data: OrderRequestDTO, user, session):    
    try:
        order = Order()
        total_value = 0.0
        order.total_value = total_value
        order.status = True
        order.description = order_data.description
        session.add(order)
        session.flush()

        sale_point = session.get(SalePoints, user['sub'])

        for item in order_data.items:
            retirada = session.query(RetiradaProduto).filter(RetiradaProduto.sale_point_id==user['sub'], RetiradaProduto.product_id==item.product_id,
                                                            date.today() == func.date(RetiradaProduto.data)).first()
            map = validate_item_order_request(item, retirada)
            product = session.get(Product, item.product_id)
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
            
            total_value += map['quantity']*product.price
            retirada.total_value += total_value
            retirada.remaining_quantity -= map['quantity']

            item_order = ItemsOrder(
                order_id=order.id,
                product_id=item.product_id,
                item_price=product.price,
                amount=item.amount,
                kg=item.kg,
                liters=item.liters
            )
            session.add(item_order)
            session.flush()

        order.total_value = total_value
        order_sale_point = OrderSalePoint()
        order_sale_point.order_id = order.id
        order_sale_point.sale_point_id = sale_point.id
        session.add(order_sale_point)
        
        session.commit()
        session.refresh(order)

        order_response = OrderResponse.model_validate(order)
        
        return order_response
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


from sqlalchemy import func
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
        order_data = OrderResponse.model_validate(order)
        result.append(order_data)
    return result

def delete_order_service(id: int, session):
    order = session.get(Order, id)
    order_data = OrderResponse.model_validate(order)
    items = session.query(ItemsOrder).filter(ItemsOrder.order_id==order.id)
    for item in items:
        order_data.items.append(ItemOrderResponseDTO.model_validate(item))
    session.delete(order)
    session.commit()
    return order_data

def delete_all_orders_service(session):
    try:
        session.query(OrderSalePoint).delete(synchronize_session="fetch")
        session.query(ItemsOrder).delete(synchronize_session="fetch")
        session.query(Order).delete(synchronize_session="fetch")
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
        
def get_orders_by_sale_point_id_service(session, date, sale_point_id):
    try:
        result = []
        query = session.query(Order).join(
            OrderSalePoint,
            Order.id == OrderSalePoint.order_id
        ).filter(
            OrderSalePoint.sale_point_id == sale_point_id
        )
        if date:
            query = query.filter(func.date(Order.order_date) == date)
        orders = query.all()
        for order in orders:
            result.append(OrderResponse.model_validate(order))
        return result  
        
    except Exception as e:
        print(f"Erro ao buscar pedidos: {e}")
        return []
    finally:
        session.close()
        
def get_order_service(session, user, id):
    order = session.get(Order, id)
    return OrderResponse.model_validate(order)

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
    
