from fastapi import APIRouter, Depends
from sales_points.sale_point_dependencies import validate_token
from dependecies import make_session
from outbounds.outbound_schema import OutboundRequestDTO
from outbounds.outbound_controller import update_quantity_controller, edit_outbound_controller, get_all_outbounds_controller
from datetime import date
from typing import Optional


outbound_router = APIRouter(prefix="/outbounds", tags=["Outbounds"])

@outbound_router.patch("/{id}")
async def edit_outbound(id: int, outbound_request: OutboundRequestDTO, user = Depends(validate_token), session = Depends(make_session)):
    result = edit_outbound_controller(session, id, outbound_request)
    return result

@outbound_router.patch("/{id}/quantity")
async def update_quantity(id: int, quantity: int, user = Depends(validate_token), session = Depends(make_session)):
    return await update_quantity_controller(session, id, quantity)

@outbound_router.get("/")
async def index(date: Optional[date] = None, user = Depends(validate_token), session = Depends(make_session)):
    result = await get_all_outbounds_controller(date, session)
    return result