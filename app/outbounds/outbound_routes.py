from fastapi import APIRouter, Depends
from sales_points.sale_point_dependencies import validate_token
from dependecies import make_session
from outbounds.outbound_schema import OutboundRequestDTO

outbound_router = APIRouter(prefix="/outbounds", tags=["Outbounds"])

@outbound_router.patch("/{id}")
async def edit_outbound(outbound_request: OutboundRequestDTO, user = Depends(validate_token), session = Depends(make_session)):
    pass