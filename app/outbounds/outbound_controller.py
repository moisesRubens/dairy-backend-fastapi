from sqlalchemy.orm import Session
from outbounds.outbound_service import update_quantity_service
from fastapi import HTTPException

async def update_quantity_controller(session: Session, id: int, new_quantity: int):
    try:
        return await update_quantity_service(session, id, new_quantity)
    except Exception as e:
        raise HTTPException(400, detail=str(e))