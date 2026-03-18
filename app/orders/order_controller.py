from orders.order_service import create_order_service, get_all_orders_service, delete_order_service, delete_all_orders_service, get_orders_by_sale_point_id_service, get_order_service, get_all_orders_service_de_pedidos, edit_order_service
from orders.order_schema import OrderRequestDTO
from products.ProductExceptions import InsuficientProductsAmountException
from fastapi import HTTPException
from sqlalchemy.orm import Session

async def create_order_controller(order_data: OrderRequestDTO, id: int, session):
    try:
        order_response_data = await create_order_service(order_data, id, session)
        return order_response_data
    except InsuficientProductsAmountException as e:
        raise HTTPException(409, detail=str(e.message))
    except Exception as e:
        raise e
    
async def get_order_controller(session, user, id):
    try:
        result = await get_order_service(session, user, id)
        return result
    except Exception as e:
        raise e

async def get_all_orders_controller(session, user, date, description, status):
    return await get_all_orders_service(session, user, date, description, status)

async def delete_order_controller(id, session):
    return await delete_order_service(id, session)

async def delete_all_orders_controller(session):
    try:
        await delete_all_orders_service(session)
    except Exception as e:
        raise HTTPException(500, detail=str(e))
    
async def get_orders_by_sale_point_id_controller(session, date, sale_point_id):
    try:
        return await get_orders_by_sale_point_id_service(session, date, sale_point_id)
    except Exception as e:
        return e
    
async def get_all_orders_controller_de_pedidos(session, date, status, descripion):
    return await get_all_orders_service_de_pedidos(session, date, status, descripion)


async def edit_order_controller(session: Session, id: int, order_request: OrderRequestDTO):
    return await edit_order_service(session, id, order_request)