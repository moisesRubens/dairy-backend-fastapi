from sqlalchemy.orm import Session
from outbounds.outbound_service import update_quantity_service

async def update_quantity_controller(session: Session, id: int, new_quantity: int):
    return update_quantity_service(session, id, new_quantity)