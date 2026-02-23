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
        if not validate_product(item.amount, item.kg, item.liters):
            raise HTTPException(404, "invalid inputs")
        product = session.get(Product, item.product_id)
        if not validate_item_order_request(item, product):
            raise HTTPException(404, "invalid inputs")
        
        if item.amount is not None and product.amount is not None:
            total_value += item.amount * product.price
            product.amount = product.amount - item.amount
        elif item.kg is not None and product.kg is not None:
            total_value += item.kg * product.price
            product.kg = product.kg - item.kg
        elif item.liters is not None and product.liters is not None:
            total_value += item.liters * product.price
            product.liters -= item.liters

        item_order = ItemsOrder(
            order_id=order.id,
            product_id=item.product_id,
            item_price=product.price,
            amount=item.amount,
            kg=item.kg,
            liters=item.liters
        )
        session.add(item_order)

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

def validate_item_order_request(item_order_request, product):
    valid = True
    
    if item_order_request.amount:
        if not product.amount:
            valid = False
    if item_order_request.kg:
        if not product.kg:
            valid = False
    if item_order_request.liters:
        if not product.liters:
            valid = False
    return valid
    