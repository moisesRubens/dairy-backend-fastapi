from fastapi import APIRouter, Depends
from typing import Optional
from sales_points.sale_point_dependencies import  validate_token
from dependecies import make_session
from orders.order_schema import OrderRequestDTO
from orders.order_controller import create_order_controller, get_all_orders_controller, delete_order_controller, delete_all_orders_controller, get_order_controller, get_all_orders_controller_de_pedidos, edit_order_controller

order_router = APIRouter(prefix="/pedidos", tags=["Order"])

@order_router.get("/")
def index(date=None, description=None, status=None, user = Depends(validate_token), session = Depends(make_session)): 
    orders = get_all_orders_controller_de_pedidos(session, date, description, status)
    return {"orders": orders}

@order_router.get("/{id}")
def show(id: int, user = Depends(validate_token), session = Depends(make_session)):
        result = get_order_controller(session, user, id)
        return result


@order_router.patch("/{id}")
async def edit(id: int, order_request: OrderRequestDTO, user = Depends(validate_token), session = Depends(make_session)):
        return await edit_order_controller(session, id, order_request)

        
@order_router.delete("/{id}")
async def destroy(id: int, session = Depends(make_session), user = Depends(validate_token)):
        order = delete_order_controller(id, session)
        return {"pedido excluido": order}
        
@order_router.delete("/")
async def delete_all(user = Depends(validate_token), session = Depends(make_session)):
        delete_all_orders_controller(session)
        return {"message": "Orders excluded"}


