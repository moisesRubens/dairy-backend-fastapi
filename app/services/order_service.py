from models.model import Order, ItemsOrder, Product, SalePoints, OrderSalePoint
from schemas.schema import OrderRequestDTO, OrderResponse


def create_order_service(order_data: OrderRequestDTO, user, session):
    order = Order()
    total_value = 0.0
    order.total_value = total_value
    order.description = order_data.description
    session.add(order)
    session.flush()

    sale_point = session.get(SalePoints, user['id'])

    for item in order_data.items:
        product = session.get(Product, item.product_id)

        if item.amount is not None:
            total_value += item.amount * product.price
            product.amount -= item.amount
        elif item.kg is not None:
            total_value += item.kg * product.price
            product.kg -= item.kg
        elif item.liters is not None:
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
        result.append(order_data)
    return result

async def delete_order(id: int, session):
    order = session.get(Order, id)
    session.delete(order)
    session.commit()
    return order
    
    
    
    