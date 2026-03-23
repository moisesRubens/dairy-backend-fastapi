from fastapi import APIRouter, Depends, Response, status
from sales_points.sale_point_dependencies import  validate_token
from dependecies import make_session
from orders.order_schema import OrderRequestDTO
from orders.order_controller import delete_order_controller, delete_all_orders_controller, get_order_controller, get_all_orders_controller_de_pedidos, edit_order_controller

order_router = APIRouter(prefix="/pedidos", tags=["Order"])

@order_router.get("/")
async def index(date=None, description=None, status=None, user = Depends(validate_token), session = Depends(make_session)): 
    orders = await get_all_orders_controller_de_pedidos(session, date, description, status)
    return orders

@order_router.get("/{id}")
async def show(id: int, user = Depends(validate_token), session = Depends(make_session)):
        result = await get_order_controller(session, user, id)
        return result


@order_router.patch("/{id}")
async def edit(id: int, order_request: OrderRequestDTO, user = Depends(validate_token), session = Depends(make_session)):
        return await edit_order_controller(session, id, order_request)

        
@order_router.delete("/{id}")
async def destroy(id: int, session = Depends(make_session), user = Depends(validate_token)):
        order = await delete_order_controller(id, session)
        return order
        
@order_router.delete("/")
async def delete_all(user = Depends(validate_token), session = Depends(make_session)):
        await delete_all_orders_controller(session)
        return Response(status_code=status.HTTP_204_NO_CONTENT)


