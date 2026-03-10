from fastapi import APIRouter, Depends
from sales_points.sale_point_dependencies import validate_token
from dependecies import make_session
from outbounds.outbound_schema import OutboundRequestDTO
from outbounds.outbound_controller import update_quantity_controller

outbound_router = APIRouter(prefix="/outbounds", tags=["Outbounds"])

@outbound_router.patch("/{id}")
async def edit_outbound(outbound_request: OutboundRequestDTO, user = Depends(validate_token), session = Depends(make_session)):
    pass

@outbound_router.patch("/{id}/quantity")
async def update_quantity(id: int, quantity: int, user = Depends(validate_token), session = Depends(make_session)):
    return update_quantity_controller(session, id, quantity)