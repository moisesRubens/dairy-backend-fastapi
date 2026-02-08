from services.order_service import create_order_service
from schemas.schema import OrderRequestDTO, SalePointResponseDTO, OrderResponseDTO

async def create_order(order_data: OrderRequestDTO, user: SalePointResponseDTO, session):
    order_response_data = await create_order_service(order_data, user.id, session)
    return order_response_data