from orders.order_service import create_order_service, get_all_orders_service, delete_order_service, delete_all_orders_service
from orders.order_schema import OrderRequestDTO

def create_order_controller(order_data: OrderRequestDTO, user, session):
    order_response_data = create_order_service(order_data, user, session)
    
    return order_response_data

def get_all_orders_controller(session, user, date, description, status):
    return get_all_orders_service(session, user, date, description, status)

def delete_order_controller(id, session):
    return delete_order_service(id, session)

def delete_all_orders_controller(session):
    try:
        delete_all_orders_service(session)
    except Exception as e:
        raise HTTPException(500, detail=str(e))