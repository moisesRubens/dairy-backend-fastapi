from model import Order, ItemsOrder, Product, SalePoints, OrderSalePoint
from orders.order_schema import OrderResponse, OrderRequestDTO, ItemOrderResponseDTO
from fastapi import HTTPException
from products.product_service import validate_product

def create_order_service(order_data: OrderRequestDTO, user, session):    
    order = Order()
    total_value = 0.0
    order.total_value = total_value
    order.description = order_data.description
    session.add(order)
    session.flush()

    sale_point = session.get(SalePoints, user['sub'])

    for item in order_data.items:
        product = session.get(Product, item.product_id)
        obj = validate_item_order_request(item, product)
        
        if not validate_product(item.amount, item.kg, item.liters) or not obj:
            raise HTTPException(404, "invalid inputs")
        
        if product.amount:
            if product.amount < item.amount:
                raise HTTPException(409, detail="Insuficiente")    
            product.amount -= item.amount
        elif product.kg:
            if product.kg < item.kg:
                raise HTTPException(409, detail="Insuficiente")   
            product.kg -= item.kg
        elif product.liters:
            if product.liters < item.liters:
                raise HTTPException(409, detail="Insuficiente")   
            product.liters -= item.liters
            
        total_value += obj*product.price
        item_order = ItemsOrder(
            order_id=order.id,
            product_id=item.product_id,
            item_price=product.price,
            amount=item.amount,
            kg=item.kg,
            liters=item.liters
        )
        session.add(item_order)
        order.item_order.append(item_order)

    order.total_value = total_value
    order_sale_point = OrderSalePoint()
    order_sale_point.order_id = order.id
    order_sale_point.sale_point_id = sale_point.id
    session.add(order_sale_point)
    session.commit()
    session.refresh(order)

    order_response = OrderResponse.model_validate(order)
    
    return order_response


def get_all_orders_service(session):
    orders = session.query(Order).all()
    result = []
    for order in orders:
        order_data = OrderResponse.model_validate(order)
        items = session.query(ItemsOrder).filter(ItemsOrder.order_id==order.id).all()
        for item in items:
            order_data.items.append(ItemOrderResponseDTO.model_validate(item))
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

def validate_item_order_request(item_order_request, product):
    obj = None
    
    if item_order_request.amount:
        obj = item_order_request.amount if product.amount else None
    if item_order_request.kg:
        obj = item_order_request.kg if product.kg else None
    if item_order_request.liters:
        obj = item_order_request.liters if product.liters else None
    return obj
    