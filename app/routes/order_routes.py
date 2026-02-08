from fastapi import APIRouter, Depends
from models.model import Order, ItemsOrder, Product
from services.order_service import get_all_orders, delete_order
from dependecies import make_session, validate_token
from schemas.schema import OrderRequestDTO, OrderResponseDTO
from controllers.order_controller import create_order

order_router = APIRouter(prefix="/pedidos", tags=["Order"])

@order_router.get("/")
def index(session = Depends(make_session)): 
    orders = get_all_orders(session)
    return {"orders": orders}


@order_router.post("/cadastrar")
async def store(order_data: OrderRequestDTO, user = Depends(validate_token), session = Depends(make_session)):
        order = await create_order(order_data, user, session)

        return {"Pedido cadastrado": order}
        
@order_router.delete("/{id}")
async def destroy(id: int, session = Depends(make_session)):
        order = await delete_order(id, session)
        
        return {"Pedido excluido": order}
        