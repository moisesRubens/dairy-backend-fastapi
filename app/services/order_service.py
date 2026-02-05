from models.model import Order, ItemsOrder, Product, SalePoints, OrderSalePoint
from schemas.schema import OrderRequestDTO

async def create_order(order_data: OrderRequestDTO, session):
    order = Order(description=order_data.description)
    session.add(order)
    session.flush()

    sale_point: SalePoints = Depends(get_current_user)

    total_value = 0

    for item in order_data.items:
        product = session.get(Product, item.product_id)
                
        if (item.amount):
            total_value += item.amount*product.price
            product.amount -= item.amount
        elif (item.kg):
            total_value += item.kg*product.price 
            product.kg -= item.kg
        elif (item.liters):
            total_value += item.liters*product.price
            product.liters -= item.liters
                        
        item_order = ItemsOrder(
            order_id = order.id,
            product_id = item.product_id,
            item_price = product.price,
            amount = item.amount,
            kg = item.kg,
            liters = item.liters
        )
        session.add(item_order)
        
    order.total_value = total_value   

    order_sale_point = OrderSalePoint(order.id, sale_point.id)
    session(order_sale_point)

    session.commit()
    session.refresh(order)
    
    return order

def get_all_orders(session):
    # Get all orders
    orders = session.query(Order).all()

    result = []
    for order in orders:
        # load related items
        items = session.query(ItemsOrder).filter_by(order_id=order.id).all()
        result.append({
            "order_id": order.id,
            "description": order.description,
            "total_value": order.total_value,
            "items": [
                {
                    "product_id": item.product_id,
                    "amount": item.amount,
                    "kg": item.kg,
                    "liters": item.liters,
                    "item_price": item.item_price
                }
                for item in items
            ]
        })
    return result

async def delete_order(id: int, session):
    order = session.get(Order, id)
    
    session.delete(order)
    session.commit()
    
    return order
    
    
    
    