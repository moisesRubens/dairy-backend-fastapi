from services.order_service import create_order_service, get_all_orders_service, delete_order_service
from schemas.schema import OrderRequestDTO

def create_order_controller(order_data: OrderRequestDTO, user, session):
    order_response_data = create_order_service(order_data, user, session)
    return order_response_data

def get_all_orders_controller(session):
    return get_all_orders_service(session)

def delete_order_controller(id, session):
    return delete_order_service(id, session)