from fastapi import APIRouter, Depends
from models.model import Order, ItemsOrder, Product
from services.order_service import create_order, get_all_orders, delete_order
from dependecies import make_session
from schemas.schema import OrderRequestDTO

order_router = APIRouter(prefix="/pedidos", tags=["Order"])

@order_router.get("/")
def index(session = Depends(make_session)): 
    orders = get_all_orders(session)
    return {"orders": orders}


@order_router.post("/cadastrar")
async def store(order_data: OrderRequestDTO, session = Depends(make_session)):
        order = await create_order(order_data, session)

        return {
                "message": "Pedido cadastrado",
                "order_id": order.id
        }
        
@order_router.delete("/{id}")
async def destroy(id: int, session = Depends(make_session)):
        order = await delete_order(id, session)
        
        return {"Pedido excluido": order}
        