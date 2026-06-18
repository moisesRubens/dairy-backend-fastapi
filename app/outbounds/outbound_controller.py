from sqlalchemy.orm import Session
from outbounds.outbound_service import update_quantity_service, edit_outbound_service, get_all_products_by_sale_point_service
from outbounds.outbound_schema import OutboundRequestDTO
from fastapi import HTTPException

async def update_quantity_controller(session: Session, id: int, new_quantity: int):
    try:
        return await update_quantity_service(session, id, new_quantity)
    except Exception as e:
        raise HTTPException(400, detail=str(e))
    
def edit_outbound_controller(session: Session, id: int, outbound_request: OutboundRequestDTO):
    try:
        result = edit_outbound_service(session, id, outbound_request)
        return result
    except Exception as e:
        raise HTTPException(400, detail=str(e))


async def get_all_outbounds_controller(date: date, session: Session):
    try:
        return await get_all_products_by_sale_point_service(session, date, False)
    except Exception as e:
        raise e