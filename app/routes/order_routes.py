from fastapi import APIRouter, Depends
from models.model import Order, ItemsOrder
from dependecies import make_session
from schemas.schema import OrderRequestDTO

order_router = APIRouter(prefix="/pedidos", tags=["Order"])

@order_router.get("/")
async def index(): 
    return {"message": "orders"}

@order_router.post("/cadastrar")
async def store(total_value: float, sale_point_id: int, product_id: int, session = Depends(make_session)):
        order = Order(total_value)
        session.add(order)
        session.commit()
        return {"message": "Pedido cadastrado"}

@order_router.post("/cadastrar")
async def store(order_data: OrderRequestDTO, session = Depends(make_session)):
        order = Order(description=order_data.description)

        session.add(order)
        session.commit()
        session.refresh(order)

        total = 0

        for item in order_data.items:
                item_order = ItemsOrder(
                        order_id = order.id,
                        product_id = item.product_id,
                        amount = item.amount,
                        kg = item.kg,
                        liters = item.liters
                )

        session.add(item_order)

        session.commit()

        return {
                "message": "Pedido cadastrado",
                "order_id": order.id
        }