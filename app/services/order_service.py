from models.model import Order, ItemsOrder, Product, SalePoints, OrderSalePoint
from schemas.schema import OrderRequestDTO, SalePointResponseDTO, OrderResponseDTO, ItemOrderResponseDTO
from fastapi import Depends


async def create_order_service(order_data: OrderRequestDTO, id_user: int, session):
    order = Order(description=order_data.description)
    session.add(order)
    session.flush()

    sale_point = session.get(SalePoints, id_user)

    total_value = 0.0

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

    order_sale_point = OrderSalePoint(order.id, sale_point.id)
    session.add(order_sale_point)

    session.commit()
    session.refresh(order)

    return OrderResponseDTO(
        id=order.id,
        status=order.status,
        total_value=order.total_value,
        description=order.description,
        date=order.order_date,
        items=[
            ItemOrderResponseDTO(
                product_id=i.product_id,
                price=i.item_price,
                amount=i.amount,
                kg=i.kg,
                liters=i.liters
            )
            for i in order.items
        ]
    )


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
    
    
    
    