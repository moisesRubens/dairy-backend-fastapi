from models.model import Order, ItemsOrder, Product
from schemas.schema import OrderRequestDTO

async def create_order(order_data: OrderRequestDTO, session):
    order = Order(description=order_data.description)
    session.add(order)
    session.flush()

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
    session.commit()
    session.refresh(order)
    
    return order
    