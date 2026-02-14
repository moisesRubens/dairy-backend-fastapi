from fastapi import APIRouter, Depends
from services.order_service import delete_order
from dependecies import make_session, validate_token
from schemas.schema import OrderRequestDTO
from controllers.order_controller import create_order_controller, get_all_orders_controller

order_router = APIRouter(prefix="/pedidos", tags=["Order"])

@order_router.get("/")
def index(session = Depends(make_session)): 
    orders = get_all_orders_controller(session)
    return orders

@order_router.post("/cadastrar")
async def store(order_data: OrderRequestDTO, user = Depends(validate_token), session = Depends(make_session)):
        order = create_order_controller(order_data, user, session)
        return {"Pedido cadastrado": order}
        
@order_router.delete("/{id}")
async def destroy(id: int, session = Depends(make_session)):
        order = delete_order(id, session)
        return {"Pedido excluido": order}
        